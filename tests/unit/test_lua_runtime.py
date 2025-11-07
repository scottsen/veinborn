"""
Unit tests for LuaRuntime.

Tests cover:
- Basic Lua execution
- Sandbox restrictions
- Timeout protection
- Error handling
- Script loading
- Syntax validation
"""

import pytest
import tempfile
from pathlib import Path
import lupa

from core.scripting.lua_runtime import (
    LuaRuntime,
    LuaTimeoutError,
    LuaSandboxError
)


class TestLuaRuntimeInitialization:
    """Test LuaRuntime initialization and setup."""

    def test_initialization(self):
        """Test basic runtime initialization."""
        runtime = LuaRuntime()
        assert runtime is not None
        assert runtime.lua is not None
        assert runtime.default_timeout == 3.0

    def test_custom_timeout(self):
        """Test initialization with custom timeout."""
        runtime = LuaRuntime(default_timeout=5.0)
        assert runtime.default_timeout == 5.0

    def test_custom_scripts_dir(self):
        """Test initialization with custom scripts directory."""
        custom_dir = Path("/tmp/lua_scripts")
        runtime = LuaRuntime(scripts_dir=custom_dir)
        assert runtime.scripts_dir == custom_dir


class TestBasicExecution:
    """Test basic Lua script execution."""

    def test_simple_arithmetic(self):
        """Test simple arithmetic expression."""
        runtime = LuaRuntime()
        result = runtime.execute_script("return 2 + 2")
        assert result == 4

    def test_string_operations(self):
        """Test string manipulation."""
        runtime = LuaRuntime()
        result = runtime.execute_script('return "Hello, " .. "Lua!"')
        assert result == "Hello, Lua!"

    def test_table_creation(self):
        """Test Lua table creation and access."""
        runtime = LuaRuntime()
        result = runtime.execute_script("""
            local t = {a = 1, b = 2, c = 3}
            return t.a + t.b + t.c
        """)
        assert result == 6

    def test_function_definition(self):
        """Test defining and calling Lua functions."""
        runtime = LuaRuntime()
        result = runtime.execute_script("""
            local function add(x, y)
                return x + y
            end
            return add(10, 20)
        """)
        assert result == 30

    def test_eval(self):
        """Test eval method for simple expressions."""
        runtime = LuaRuntime()
        result = runtime.eval("5 * 5")
        assert result == 25


class TestSandboxRestrictions:
    """Test sandbox security restrictions."""

    def test_io_blocked(self):
        """Test that io library is blocked."""
        runtime = LuaRuntime()
        with pytest.raises(lupa.LuaError):
            runtime.execute_script("return io.open('/etc/passwd', 'r')")

    def test_os_blocked(self):
        """Test that os library is blocked."""
        runtime = LuaRuntime()
        with pytest.raises(lupa.LuaError):
            runtime.execute_script("return os.execute('ls')")

    def test_load_blocked(self):
        """Test that dynamic code loading is blocked."""
        runtime = LuaRuntime()
        with pytest.raises(lupa.LuaError):
            runtime.execute_script("return load('return 42')")

    def test_loadfile_blocked(self):
        """Test that loadfile is blocked."""
        runtime = LuaRuntime()
        with pytest.raises(lupa.LuaError):
            runtime.execute_script("return loadfile('/tmp/test.lua')")

    def test_dofile_blocked(self):
        """Test that dofile is blocked."""
        runtime = LuaRuntime()
        with pytest.raises(lupa.LuaError):
            runtime.execute_script("return dofile('/tmp/test.lua')")

    def test_debug_blocked(self):
        """Test that debug library is blocked."""
        runtime = LuaRuntime()
        with pytest.raises(lupa.LuaError):
            runtime.execute_script("return debug.getinfo(1)")

    def test_require_blocked(self):
        """Test that require is blocked."""
        runtime = LuaRuntime()
        with pytest.raises(lupa.LuaError):
            runtime.execute_script("return require('socket')")


class TestAllowedLibraries:
    """Test that safe libraries are allowed."""

    def test_math_allowed(self):
        """Test that math library is available."""
        runtime = LuaRuntime()
        result = runtime.execute_script("return math.sqrt(16)")
        assert result == 4.0

    def test_string_allowed(self):
        """Test that string library is available."""
        runtime = LuaRuntime()
        result = runtime.execute_script('return string.upper("hello")')
        assert result == "HELLO"

    def test_table_allowed(self):
        """Test that table library is available."""
        runtime = LuaRuntime()
        result = runtime.execute_script("""
            local t = {3, 1, 2}
            table.sort(t)
            return t[1]
        """)
        assert result == 1


class TestErrorHandling:
    """Test error handling for Lua scripts."""

    def test_syntax_error(self):
        """Test handling of syntax errors."""
        runtime = LuaRuntime()
        with pytest.raises(lupa.LuaSyntaxError):
            runtime.execute_script("return 2 +")  # Incomplete expression

    def test_runtime_error(self):
        """Test handling of runtime errors."""
        runtime = LuaRuntime()
        with pytest.raises(lupa.LuaError):
            runtime.execute_script("return nil.field")  # Nil access

    def test_division_by_zero(self):
        """Test division by zero (Lua returns inf)."""
        runtime = LuaRuntime()
        result = runtime.execute_script("return 1 / 0")
        assert result == float('inf')

    def test_undefined_variable(self):
        """Test that undefined variables return nil."""
        runtime = LuaRuntime()
        result = runtime.execute_script("return undefined_var")
        assert result is None


class TestGlobalsManagement:
    """Test global variable management."""

    def test_set_and_get_global(self):
        """Test setting and getting global variables."""
        runtime = LuaRuntime()
        runtime.set_global("test_value", 42)
        result = runtime.execute_script("return test_value")
        assert result == 42

    def test_get_global(self):
        """Test getting global variables."""
        runtime = LuaRuntime()
        runtime.execute_script("my_global = 'test'")
        result = runtime.get_global("my_global")
        assert result == "test"

    def test_inject_globals_in_execute(self):
        """Test injecting globals during execution."""
        runtime = LuaRuntime()
        result = runtime.execute_script(
            "return multiplier * 5",
            globals_dict={"multiplier": 3}
        )
        assert result == 15


class TestFunctionCalls:
    """Test calling Lua functions."""

    def test_call_function(self):
        """Test calling a Lua function by name."""
        runtime = LuaRuntime()
        runtime.execute_script("""
            function multiply(a, b)
                return a * b
            end
        """)
        result = runtime.call_function("multiply", 6, 7)
        assert result == 42

    def test_call_nonexistent_function(self):
        """Test calling non-existent function raises error."""
        runtime = LuaRuntime()
        with pytest.raises(AttributeError):
            runtime.call_function("nonexistent_function")

    def test_call_function_with_error(self):
        """Test function that raises an error."""
        runtime = LuaRuntime()
        runtime.execute_script("""
            function error_func()
                error("Intentional error")
            end
        """)
        with pytest.raises(lupa.LuaError):
            runtime.call_function("error_func")


class TestScriptLoading:
    """Test loading scripts from files."""

    def test_load_script_file(self):
        """Test loading and executing a script file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            script_dir = Path(tmpdir)
            script_file = script_dir / "test_script.lua"

            # Write test script
            script_file.write_text("return 123")

            # Load and execute
            runtime = LuaRuntime(scripts_dir=script_dir)
            result = runtime.load_script_file("test_script.lua")
            assert result == 123

    def test_load_nonexistent_file(self):
        """Test loading non-existent file raises error."""
        runtime = LuaRuntime()
        with pytest.raises(FileNotFoundError):
            runtime.load_script_file("nonexistent.lua")

    def test_load_complex_script(self):
        """Test loading script with functions and logic."""
        with tempfile.TemporaryDirectory() as tmpdir:
            script_dir = Path(tmpdir)
            script_file = script_dir / "fibonacci.lua"

            # Write Fibonacci script
            script_file.write_text("""
                function fib(n)
                    if n <= 1 then return n end
                    return fib(n - 1) + fib(n - 2)
                end
                return fib(10)
            """)

            runtime = LuaRuntime(scripts_dir=script_dir)
            result = runtime.load_script_file("fibonacci.lua")
            assert result == 55  # 10th Fibonacci number


class TestSyntaxValidation:
    """Test script syntax validation."""

    def test_valid_syntax(self):
        """Test validating correct syntax."""
        runtime = LuaRuntime()
        valid, error = runtime.validate_script_syntax("return 2 + 2")
        assert valid is True
        assert error is None

    def test_invalid_syntax(self):
        """Test validating incorrect syntax."""
        runtime = LuaRuntime()
        valid, error = runtime.validate_script_syntax("return 2 +")
        assert valid is False
        assert error is not None

    def test_empty_script(self):
        """Test validating empty script."""
        runtime = LuaRuntime()
        valid, error = runtime.validate_script_syntax("")
        assert valid is True


class TestTimeoutProtection:
    """Test timeout protection for long-running scripts."""

    @pytest.mark.skip(reason="Timeout requires Unix signals, may not work in all environments")
    def test_infinite_loop_timeout(self):
        """Test that infinite loops are terminated."""
        runtime = LuaRuntime(default_timeout=1.0)
        with pytest.raises((LuaTimeoutError, lupa.LuaError)):
            runtime.execute_script("""
                while true do
                    -- Infinite loop
                end
            """)

    @pytest.mark.skip(reason="Timeout requires Unix signals, may not work in all environments")
    def test_long_computation_timeout(self):
        """Test that long computations are terminated."""
        runtime = LuaRuntime(default_timeout=1.0)
        with pytest.raises((LuaTimeoutError, lupa.LuaError)):
            runtime.execute_script("""
                local sum = 0
                for i = 1, 1000000000 do
                    sum = sum + i
                end
                return sum
            """)

    def test_quick_execution_no_timeout(self):
        """Test that quick scripts don't trigger timeout."""
        runtime = LuaRuntime(default_timeout=1.0)
        result = runtime.execute_script("return 42")
        assert result == 42


class TestComplexScenarios:
    """Test complex realistic scenarios."""

    def test_table_manipulation(self):
        """Test complex table operations."""
        runtime = LuaRuntime()
        result = runtime.execute_script("""
            local players = {}
            table.insert(players, {name = "Alice", hp = 100})
            table.insert(players, {name = "Bob", hp = 80})

            local total_hp = 0
            for _, player in ipairs(players) do
                total_hp = total_hp + player.hp
            end

            return total_hp
        """)
        assert result == 180

    def test_conditional_logic(self):
        """Test conditional logic and branching."""
        runtime = LuaRuntime()
        result = runtime.execute_script("""
            function classify_number(n)
                if n < 0 then
                    return "negative"
                elseif n == 0 then
                    return "zero"
                else
                    return "positive"
                end
            end

            return classify_number(5)
        """)
        assert result == "positive"

    def test_return_multiple_values(self):
        """Test returning multiple values from Lua."""
        runtime = LuaRuntime()
        # lupa with unpack_returned_tuples=True returns tuples
        result = runtime.execute_script("return 1, 2, 3")
        assert result == (1, 2, 3)

    def test_python_to_lua_conversion(self):
        """Test Python objects being passed to Lua."""
        runtime = LuaRuntime()
        # Pass Python dictionary to Lua
        runtime.set_global("config", {"max_hp": 100, "mana": 50})
        result = runtime.execute_script("""
            return config.max_hp + config.mana
        """)
        assert result == 150
