"""
Lua Runtime wrapper for safe script execution.

This module provides a sandboxed Lua runtime with timeout protection,
error handling, and security restrictions for modding support.
"""

import logging
import signal
from pathlib import Path
from typing import Any, Optional, Dict
import lupa


logger = logging.getLogger(__name__)


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
        self.lua = lupa.LuaRuntime(unpack_returned_tuples=True)
        self.default_timeout = default_timeout
        self.scripts_dir = scripts_dir or Path("scripts")
        self._setup_sandbox()
        logger.info("LuaRuntime initialized with sandbox and timeout protection")

    def _setup_sandbox(self) -> None:
        """
        Configure sandbox environment by removing dangerous globals.

        Blocked capabilities:
        - File I/O (io.*)
        - OS access (os.*)
        - Dynamic code loading (load, loadfile, dofile, loadstring)
        - Debug library (debug.*)
        - Package management (require, package.*)

        Allowed capabilities:
        - Math library
        - String library
        - Table library
        - Basic functions (print, tostring, tonumber, etc.)
        """
        sandbox_script = """
        -- Remove dangerous globals
        io = nil
        os = nil
        load = nil
        loadfile = nil
        dofile = nil
        loadstring = nil
        debug = nil
        require = nil
        package = nil

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
            # Note: lupa doesn't have built-in timeout, so we use signal-based timeout
            # This is a simplified approach - production might need threading-based timeout
            result = self._execute_with_timeout(script, timeout)
            logger.debug(f"Lua script executed successfully")
            return result
        except lupa.LuaError as e:
            logger.error(f"Lua execution error: {e}")
            raise
        except LuaTimeoutError:
            logger.error(f"Lua script exceeded timeout of {timeout}s")
            raise

    def _execute_with_timeout(self, script: str, timeout: float) -> Any:
        """
        Execute script with timeout protection using signals.

        Note: This is a simplified timeout mechanism. For production use,
        consider using threading or multiprocessing for more robust timeout.

        Args:
            script: Lua script to execute
            timeout: Timeout in seconds

        Returns:
            Result of script execution

        Raises:
            LuaTimeoutError: If execution exceeds timeout
        """
        def timeout_handler(signum, frame):
            raise LuaTimeoutError(f"Lua execution exceeded {timeout}s timeout")

        # Set up timeout handler (Unix-only, won't work on Windows)
        try:
            # Try to set alarm - will fail on Windows
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(timeout))

            try:
                result = self.lua.execute(script)
                return result
            finally:
                signal.alarm(0)  # Cancel alarm
                signal.signal(signal.SIGALRM, old_handler)  # Restore handler
        except AttributeError:
            # Windows doesn't have SIGALRM - execute without timeout
            logger.warning("Timeout protection not available on this platform")
            return self.lua.execute(script)

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

        # Call function (lupa handles argument conversion)
        try:
            result = func(*args)
            return result
        except lupa.LuaError as e:
            logger.error(f"Error calling Lua function '{func_name}': {e}")
            raise

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
