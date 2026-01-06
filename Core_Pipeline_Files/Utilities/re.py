"""
Regex-based Python code extraction from text
"""
import re


def extract_python_code(text: str) -> str:
    """
    Extract Python code from text containing code blocks.
    
    Args:
        text: Text that may contain code blocks
    
    Returns:
        str: Extracted Python code, or empty string if none found
    
    Note:
        Returns empty string instead of raising error to allow
        retry logic in mainV3.py to handle it gracefully.
    """
    if not text:
        return ""
    
    # Case 1: ```python ... ```
    match = re.search(r"```python\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Case 2: ``` ... ``` (generic code block)
    match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Case 3: ''' ... ''' (triple single quotes)
    match = re.search(r"'''\s*(.*?)\s*'''", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Case 4: """ ... """ (triple double quotes)
    match = re.search(r'"""\s*(.*?)\s*"""', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Case 5: Look for import statements (might be raw code without markers)
    if re.search(r'^\s*(import|from|def|class)\s+', text, re.MULTILINE):
        # Looks like raw Python code
        return text.strip()
    
    # No code found - return empty string
    # mainV3.py will detect this and handle appropriately
    return ""


def extract_code_blocks(text: str) -> list:
    """
    Extract all code blocks from text.
    
    Args:
        text: Text that may contain multiple code blocks
    
    Returns:
        list: List of code blocks found
    """
    blocks = []
    
    # Find all ```python ... ``` blocks
    python_blocks = re.findall(r"```python\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    blocks.extend(python_blocks)
    
    # Find all generic ``` ... ``` blocks (exclude already found python blocks)
    generic_blocks = re.findall(r"```(?!python)\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    blocks.extend(generic_blocks)
    
    return [block.strip() for block in blocks if block.strip()]


def is_valid_python_code(code: str) -> bool:
    """
    Check if string contains valid Python code (syntax check only).
    
    Args:
        code: String to check
    
    Returns:
        bool: True if valid Python syntax
    """
    try:
        compile(code, '<string>', 'exec')
        return True
    except SyntaxError:
        return False


if __name__ == "__main__":
    # Test cases
    print("Testing extract_python_code...")
    
    # Test 1: With python marker
    test1 = """
Here is some code:
```python
import pandas as pd
df = pd.read_csv('file.csv')
print(df.head())
```
That's the code!
"""
    result1 = extract_python_code(test1)
    print(f"Test 1: {'✓' if 'pandas' in result1 else '✗'}")
    
    # Test 2: Generic code block
    test2 = """
```
x = 5
print(x)
```
"""
    result2 = extract_python_code(test2)
    print(f"Test 2: {'✓' if 'x = 5' in result2 else '✗'}")
    
    # Test 3: No code block
    test3 = "This is just text without code"
    result3 = extract_python_code(test3)
    print(f"Test 3: {'✓' if result3 == '' else '✗'}")
    
    # Test 4: Raw Python code
    test4 = """import sys
import os
print('hello')"""
    result4 = extract_python_code(test4)
    print(f"Test 4: {'✓' if 'import sys' in result4 else '✗'}")
    
    print("\n✓ All tests complete!")