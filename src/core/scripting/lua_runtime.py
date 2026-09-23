"""
Lua Runtime wrapper for safe script execution.

This module provides a sandboxed Lua runtime with timeout protection,
error handling, and security restrictions for modding support.
"""

import logging
import time
from pathlib import Path
from typing import Any, Optional, Dict
import lupa


logger = logging.getLogger(__name__)

# VB-17: sentinel error value raised by the instruction-count hook once the
# deadline is passed. Lua's error() is used (not a raw Python exception)
# because a raw Python exception raised from inside a Lua debug hook, while
# it does propagate, gets caught like any other error by a script that
# wraps itself in pcall() -- see _TIMEOUT_SENTINEL usage in _setup_sandbox.
_TIMEOUT_SENTINEL = "__veinborn_lua_timeout__"


class LuaTimeoutError(Exception):
    """Raised when Lua script execution exceeds timeout."""
    pass


class LuaSandboxError(Exception):
    """Raised when Lua script attempts unauthorized operations."""
    pass


class LuaRuntime:
    """
    Safe Lua runtime environment for executing user scripts.

    Features:
    - Sandboxed environment (no file I/O, OS access, or code loading)
    - Timeout protection (configurable, default 3 seconds)
    - Comprehensive error handling
    - Script loading from designated directory

    Example:
        >>> runtime = LuaRuntime()
        >>> result = runtime.execute_script("return 2 + 2")
        >>> print(result)  # 4
    """

    def __init__(self, scripts_dir: Optional[Path] = None, default_timeout: float = 3.0):
        """
        Initialize Lua runtime with sandbox configuration.

        Args:
            scripts_dir: Base directory for loading scripts (default: ./scripts)
            default_timeout: Default execution timeout in seconds (default: 3.0)
        """
        self.lua = lupa.LuaRuntime(
            unpack_returned_tuples=True,
            # VB-17: without these, Lua scripts can call python.eval()/
            # python.builtins.* directly -- confirmed reproducible RCE
            # (execute_script("return python.eval('__import__(\"os\")...')")
            # returned real process data).
            register_eval=False,
            register_builtins=False,
            # VB-17: register_eval/register_builtins alone aren't enough --
            # any Python object or bound method handed to Lua (e.g. every
            # veinborn.* API function in GameContextAPI) is still walkable
            # via dunder attributes (obj.__class__.__base__.__subclasses__()
            # is a well-known route back to arbitrary classes/builtins).
            # Block all underscore-prefixed attribute access from Lua.
            attribute_filter=self._attribute_filter,
        )
        self.default_timeout = default_timeout
        self.scripts_dir = scripts_dir or Path("scripts")
        # No deadline armed until execute_script()/call_function() sets one.
        self._deadline = float('inf')
        self._setup_sandbox()
        logger.info("LuaRuntime initialized with sandbox and timeout protection")

    def _deadline_exceeded(self) -> bool:
        """Called every N Lua instructions by the debug-hook hook (see
        _setup_sandbox). Wall-clock based so it works regardless of what
        the script is doing between hook calls."""
        return time.perf_counter() > self._deadline

    @staticmethod
    def _attribute_filter(obj: Any, name: Any, is_setting: bool) -> Any:
        """Block Lua access to any underscore-prefixed Python attribute.

        Closes the dunder-attribute sandbox-escape route (__class__,
        __globals__, __subclasses__, etc.) on any Python object or bound
        method exposed to Lua scripts. See VB-17.
        """
        if isinstance(name, str) and name.startswith('_'):
            raise AttributeError(f"access to {name!r} is not allowed from Lua")
        return name

    def _setup_sandbox(self) -> None:
        """
        Configure sandbox environment: remove dangerous globals and install
        the instruction-count timeout hook.

        Blocked capabilities:
        - File I/O (io.*)
        - OS access (os.*)
        - Dynamic code loading (load, loadfile, dofile, loadstring)
        - Debug library (debug.*) -- after capturing debug.sethook to
          install our own timeout hook below
        - Package management (require, package.*)

        Allowed capabilities:
        - Math library
        - String library
        - Table library
        - Basic functions (print, tostring, tonumber, etc.)

        Timeout mechanism (VB-17): a plain signal.alarm()-based timeout
        cannot interrupt a tight Lua loop that never calls back into
        Python (confirmed: `while true do end` ran past a 300s wall-clock
        SIGALRM timeout without ever raising) -- CPython only services
        pending signals between its own bytecode instructions, and control
        never returns there while the Lua VM is spinning in pure C. A
        debug.sethook() *count* hook runs every N Lua VM instructions
        regardless, so it reliably interrupts tight loops. Because a script
        could otherwise neutralize the hook's error with
        `while true do pcall(fn) end`, pcall/xpcall are wrapped to detect
        and re-raise our specific timeout sentinel rather than swallowing
        it like any other script error.
        """
        # Bind the deadline check as a Lua global just long enough to wire
        # it into a real Lua closure (debug.sethook requires an actual Lua
        # function, not a bare Python callable -- lupa exposes Python
        # callables as callable userdata, which fails debug.sethook's
        # internal lua_isfunction check).
        self.lua.globals()['_py_deadline_exceeded'] = self._deadline_exceeded

        sandbox_script = f"""
        -- Install instruction-count timeout hook (captures the Python
        -- callback as a local before it's removed from globals below).
        local deadline_exceeded = _py_deadline_exceeded
        local SENTINEL = "{_TIMEOUT_SENTINEL}"

        debug.sethook(function()
            if deadline_exceeded() then
                error(SENTINEL, 0)
            end
        end, "", 1000)

        -- Harden pcall/xpcall so a script can't survive the timeout by
        -- catching-and-retrying in a loop (see docstring above).
        local raw_pcall = pcall
        local raw_xpcall = xpcall

        pcall = function(...)
            local results = {{raw_pcall(...)}}
            if results[1] == false and results[2] == SENTINEL then
                error(SENTINEL, 0)
            end
            return table.unpack(results)
        end

        xpcall = function(f, handler, ...)
            local results = {{raw_xpcall(f, handler, ...)}}
            if results[1] == false and results[2] == SENTINEL then
                error(SENTINEL, 0)
            end
            return table.unpack(results)
        end

        -- Remove dangerous globals (debug last, since sethook was just used)
        io = nil
        os = nil
        load = nil
        loadfile = nil
        dofile = nil
        loadstring = nil
        debug = nil
        require = nil
        package = nil
        _py_deadline_exceeded = nil

        -- Keep safe globals
        -- math, string, table, print, tostring, tonumber remain available
        """

        try:
            self.lua.execute(sandbox_script)
            logger.debug("Lua sandbox configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure Lua sandbox: {e}")
            raise LuaSandboxError(f"Sandbox setup failed: {e}")

    def execute_script(
        self,
        script: str,
        timeout: Optional[float] = None,
        globals_dict: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Execute Lua script with timeout protection.

        Args:
            script: Lua script code to execute
            timeout: Execution timeout in seconds (uses default if None)
            globals_dict: Optional dictionary to inject into Lua globals

        Returns:
            Result of the Lua script execution

        Raises:
            LuaTimeoutError: If execution exceeds timeout
            lupa.LuaError: If Lua script has errors
        """
        timeout = timeout or self.default_timeout

        # Inject custom globals if provided
        if globals_dict:
            lua_globals = self.lua.globals()
            for key, value in globals_dict.items():
                lua_globals[key] = value

        try:
            result = self._execute_with_timeout(script, timeout)
            logger.debug(f"Lua script executed successfully")
            return result
        except LuaTimeoutError:
            logger.error(f"Lua script exceeded timeout of {timeout}s")
            raise
        except lupa.LuaError as e:
            logger.error(f"Lua execution error: {e}")
            raise

    def _execute_with_timeout(self, script: str, timeout: float) -> Any:
        """
        Execute script with timeout protection via the instruction-count
        hook installed in _setup_sandbox() (see its docstring for why a
        signal-based timeout can't reliably interrupt a tight Lua loop).

        Args:
            script: Lua script to execute
            timeout: Timeout in seconds

        Returns:
            Result of script execution

        Raises:
            LuaTimeoutError: If execution exceeds timeout
        """
        self._deadline = time.perf_counter() + timeout
        try:
            return self.lua.execute(script)
        except lupa.LuaError as e:
            if _TIMEOUT_SENTINEL in str(e):
                raise LuaTimeoutError(f"Lua execution exceeded {timeout}s timeout") from e
            raise
        finally:
            self._deadline = float('inf')

    def load_script_file(self, path: str, timeout: Optional[float] = None) -> Any:
        """
        Load and execute a Lua script file.

        Args:
            path: Relative path to script (relative to scripts_dir)
            timeout: Execution timeout in seconds

        Returns:
            Result of script execution

        Raises:
            FileNotFoundError: If script file doesn't exist
            lupa.LuaError: If Lua script has errors
        """
        script_path = self.scripts_dir / path

        if not script_path.exists():
            logger.error(f"Script file not found: {script_path}")
            raise FileNotFoundError(f"Script not found: {script_path}")

        logger.info(f"Loading Lua script: {script_path}")

        with open(script_path, 'r') as f:
            script_code = f.read()

        return self.execute_script(script_code, timeout)

    def eval(self, expression: str) -> Any:
        """
        Evaluate a Lua expression and return the result.

        Args:
            expression: Lua expression to evaluate

        Returns:
            Result of the expression
        """
        return self.lua.eval(expression)

    def call_function(self, func_name: str, *args, **kwargs) -> Any:
        """
        Call a Lua function by name with arguments.

        Args:
            func_name: Name of Lua function in globals
            *args: Positional arguments to pass to function
            **kwargs: Keyword arguments (timeout only)

        Returns:
            Result of function call

        Raises:
            AttributeError: If function doesn't exist
            lupa.LuaError: If function execution fails
        """
        timeout = kwargs.get('timeout', self.default_timeout)
        lua_globals = self.lua.globals()

        if func_name not in lua_globals:
            raise AttributeError(f"Lua function '{func_name}' not found")

        func = lua_globals[func_name]

        # VB-17: timeout was previously accepted but never enforced here --
        # only execute_script() armed the deadline. Arm it for direct
        # function calls too (event handlers, AI behaviours).
        self._deadline = time.perf_counter() + timeout
        try:
            result = func(*args)
            return result
        except lupa.LuaError as e:
            if _TIMEOUT_SENTINEL in str(e):
                logger.error(f"Lua function '{func_name}' exceeded {timeout}s timeout")
                raise LuaTimeoutError(
                    f"Lua function '{func_name}' exceeded {timeout}s timeout"
                ) from e
            logger.error(f"Error calling Lua function '{func_name}': {e}")
            raise
        finally:
            self._deadline = float('inf')

    def get_global(self, name: str) -> Any:
        """
        Get a global variable from Lua environment.

        Args:
            name: Name of global variable

        Returns:
            Value of the global variable
        """
        return self.lua.globals()[name]

    def set_global(self, name: str, value: Any) -> None:
        """
        Set a global variable in Lua environment.

        Args:
            name: Name of global variable
            value: Value to set (will be converted to Lua type)
        """
        self.lua.globals()[name] = value

    def validate_script_syntax(self, script: str) -> tuple[bool, Optional[str]]:
        """
        Validate Lua script syntax without executing it.

        Args:
            script: Lua script code to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Try to compile the script - lupa will catch syntax errors
            self.lua.execute(f"return function() {script} end")
            return True, None
        except lupa.LuaSyntaxError as e:
            return False, str(e)
        except lupa.LuaError as e:
            return False, str(e)
