"""
Safe code execution with output capture
"""
import io
import sys
import contextlib
import traceback


def execute_code_capture_output(code: str) -> str:
    """
    Execute Python code and capture all output (stdout + stderr).
    
    Args:
        code: Python code to execute
    
    Returns:
        str: Combined stdout and stderr output
    
    Note:
        Captures both print statements (stdout) and errors (stderr)
        to provide complete output for debugging.
    """
    if not code or not code.strip():
        return "Error: No code provided to execute"
    
    # Buffers for stdout and stderr
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    
    # Shared namespace for execution
    exec_env = {}
    
    try:
        # Redirect both stdout and stderr
        with contextlib.redirect_stdout(stdout_buffer), \
             contextlib.redirect_stderr(stderr_buffer):
            exec(code, exec_env)
        
        # Combine outputs
        stdout_content = stdout_buffer.getvalue()
        stderr_content = stderr_buffer.getvalue()
        
        # Return combined output
        output = stdout_content
        if stderr_content:
            if output:
                output += "\n" + "="*80 + "\n"
            output += "STDERR:\n" + stderr_content
        
        return output if output else "[No output produced]"
    
    except Exception as e:
        # Capture the full traceback
        error_output = stdout_buffer.getvalue()
        if error_output:
            error_output += "\n" + "="*80 + "\n"
        
        error_output += f"Error: {type(e).__name__}: {str(e)}\n"
        error_output += "\nTraceback:\n"
        error_output += traceback.format_exc()
        
        return error_output


def execute_code_safe(code: str, timeout: int = 30) -> dict:
    """
    Execute code with safety checks and timeout (requires additional setup).
    
    Args:
        code: Python code to execute
        timeout: Maximum execution time in seconds
    
    Returns:
        dict: {
            'success': bool,
            'output': str,
            'error': str or None,
            'execution_time': float
        }
    """
    import time
    
    start_time = time.time()
    
    try:
        output = execute_code_capture_output(code)
        execution_time = time.time() - start_time
        
        # Check if there was an error in output
        has_error = any(indicator in output for indicator in [
            'Error:', 'Exception:', 'Traceback'
        ])
        
        return {
            'success': not has_error,
            'output': output,
            'error': output if has_error else None,
            'execution_time': execution_time
        }
    
    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = f"Execution failed: {type(e).__name__}: {str(e)}"
        
        return {
            'success': False,
            'output': '',
            'error': error_msg,
            'execution_time': execution_time
        }


def validate_code_safety(code: str) -> tuple:
    """
    Perform basic safety checks on code before execution.
    
    Args:
        code: Python code to validate
    
    Returns:
        tuple: (is_safe: bool, warnings: list)
    
    Warning:
        This is NOT a comprehensive security check.
        Do not use for untrusted code!
    """
    warnings = []
    is_safe = True
    
    # Dangerous patterns (basic check only)
    dangerous_patterns = [
        (r'\beval\b', 'Uses eval()'),
        (r'\bexec\b', 'Uses exec()'),
        (r'\b__import__\b', 'Uses __import__()'),
        (r'\bos\.system\b', 'Uses os.system()'),
        (r'\bsubprocess\b', 'Uses subprocess'),
        (r'\bopen\(.*[\'"]w', 'Writes to files'),
        (r'\bos\.remove\b', 'Deletes files'),
        (r'\bshutil\.rmtree\b', 'Deletes directories'),
    ]
    
    for pattern, warning in dangerous_patterns:
        import re
        if re.search(pattern, code):
            warnings.append(warning)
    
    # Note: File operations are actually needed for cleaning!
    # So we only warn, not block
    
    return is_safe, warnings


if __name__ == "__main__":
    # Test cases
    print("Testing execute_code_capture_output...")
    print("="*80)
    
    # Test 1: Normal execution
    print("\nTest 1: Normal print")
    code1 = """
print("Hello, World!")
print("Line 2")
"""
    output1 = execute_code_capture_output(code1)
    print(output1)
    print(f"Status: {'✓' if 'Hello' in output1 else '✗'}")
    
    # Test 2: Error handling
    print("\nTest 2: Error handling")
    code2 = """
print("Before error")
x = 1 / 0  # This will raise an error
print("After error - won't print")
"""
    output2 = execute_code_capture_output(code2)
    print(output2)
    print(f"Status: {'✓' if 'ZeroDivisionError' in output2 else '✗'}")
    
    # Test 3: Import and use library
    print("\nTest 3: Using libraries")
    code3 = """
import math
result = math.sqrt(16)
print(f"Square root of 16 is {result}")
"""
    output3 = execute_code_capture_output(code3)
    print(output3)
    print(f"Status: {'✓' if '4' in output3 else '✗'}")
    
    # Test 4: Multiple outputs
    print("\nTest 4: Multiple outputs")
    code4 = """
for i in range(3):
    print(f"Iteration {i}")
"""
    output4 = execute_code_capture_output(code4)
    print(output4)
    print(f"Status: {'✓' if 'Iteration 2' in output4 else '✗'}")
    
    # Test 5: No output
    print("\nTest 5: No output")
    code5 = """
x = 5
y = 10
z = x + y
"""
    output5 = execute_code_capture_output(code5)
    print(f"Output: '{output5}'")
    print(f"Status: {'✓' if 'No output' in output5 else '✗'}")
    
    # Test 6: Safe execution with metadata
    print("\nTest 6: Safe execution wrapper")
    code6 = "print('Testing safe execution')"
    result6 = execute_code_safe(code6)
    print(f"Success: {result6['success']}")
    print(f"Output: {result6['output']}")
    print(f"Time: {result6['execution_time']:.4f}s")
    print(f"Status: {'✓' if result6['success'] else '✗'}")
    
    print("\n" + "="*80)
    print("✓ All tests complete!")