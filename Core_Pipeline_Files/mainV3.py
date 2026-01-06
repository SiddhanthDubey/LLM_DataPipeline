"""
MainV3 - Intelligent file processing pipeline with specialized models
"""
from Utilities.metadata_extractor import extract_all_metadata
from model_handler import ModelHandler
from ollama_client import OllamaClient
from Utilities.re import extract_python_code
from Utilities.code_exec import execute_code_capture_output
import json
import re
import os
from datetime import datetime


# ============================================================================
# CONFIGURATION
# ============================================================================
FILENAME = "/home/dent1st/SPPproject/ProjectV4/Core_Pipeline_Files/train.txt"  # Change this to any file


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def execute_with_retry(client, initial_prompt, stage_name, max_retries=3):
    """
    Execute code with automatic retry on errors.
    
    Args:
        client: OllamaClient instance
        initial_prompt: Initial prompt to send
        stage_name: Name of stage (for logging)
        max_retries: Maximum retry attempts
    
    Returns:
        tuple: (success: bool, code: str, output: str)
    """
    prompt = initial_prompt
    
    for attempt in range(max_retries):
        print(f"\n{'='*80}")
        print(f"{stage_name} - Attempt {attempt + 1}/{max_retries}")
        print(f"{'='*80}")
        
        # Get model response
        try:
            result = client.chat(prompt)
        except Exception as e:
            print(f"✗ Model communication error: {e}")
            if attempt < max_retries - 1:
                print("Retrying...")
                continue
            else:
                return False, "", str(e)
        
        print("Model Response Preview:")
        preview = result[:300] + "..." if len(result) > 300 else result
        print(preview)
        print("="*80)
        
        # Extract code
        code = extract_python_code(result)
        if not code:
            print("✗ No code found in response")
            if attempt < max_retries - 1:
                prompt = f"""Previous response didn't contain valid Python code.

Please provide ONLY a Python code block with ```python markers.

Original task:
{initial_prompt}
"""
                continue
            else:
                return False, "", "No code generated"
        
        print(f"{stage_name} Code:")
        print(code)
        print("="*80)
        
        # Auto-fix: Add function call if needed
        if "def " in code:
            func_match = re.search(r'def\s+(\w+)\s*\(([^)]*)\)', code)
            if func_match:
                func_name = func_match.group(1)
                if f"{func_name}(" not in code.split(f"def {func_name}")[1]:
                    print("Auto-fix: Adding function call...")
                    params = func_match.group(2).strip()
                    if params and any(p in params.lower() for p in ['filename', 'file', 'path']):
                        code += f"\n{func_name}('{FILENAME}')\n"
                    else:
                        code += f"\n{func_name}()\n"
        
        # Execute code
        print(f"Executing {stage_name.lower()}...")
        output = execute_code_capture_output(code)
        print(f"{stage_name} Output:")
        print(output)
        print("="*80)
        
        # Check for errors (ignore warnings)
        error_indicators = [
            "Error:", "Exception:", "Traceback", "NameError", "TypeError",
            "ValueError", "FileNotFoundError", "ImportError", "KeyError",
            "AttributeError", "SyntaxError", "ModuleNotFoundError"
        ]
        
        has_error = any(indicator in output for indicator in error_indicators)
        
        # Filter out warnings
        if has_error:
            lines = output.split('\n')
            error_lines = [l for l in lines if any(e in l for e in error_indicators)]
            warning_only = all('Warning' in l or 'FutureWarning' in l for l in error_lines)
            if warning_only:
                has_error = False
        
        if not has_error:
            print(f"✓ {stage_name} succeeded!")
            return True, code, output
        
        # Error detected
        print(f"✗ {stage_name} failed with error. Preparing retry...")
        
        if attempt < max_retries - 1:
            retry_prompt = f"""The previous code failed with this error:

ERROR OUTPUT:
{output}

PREVIOUS CODE:
```python
{code}
```

ANALYZE AND FIX:
- What caused the error?
- Missing imports or wrong methods?
- File path issues?
- Logic errors?

Generate CORRECTED Python code that fixes these issues.
Return ONLY the Python code block.
"""
            prompt = retry_prompt
    
    print(f"✗ {stage_name} failed after {max_retries} attempts")
    return False, code, output


def print_banner(text):
    """Print a formatted banner"""
    print("\n" + "="*80)
    print(text.center(80))
    print("="*80)


def print_section(text):
    """Print a section header"""
    print("\n" + "-"*80)
    print(text)
    print("-"*80)


# ============================================================================
# MAIN PIPELINE
# ============================================================================
def main():
    """Main execution pipeline"""
    
    print_banner("INTELLIGENT FILE PROCESSING PIPELINE V3")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target File: {FILENAME}")
    
    # Check if file exists
    if not os.path.exists(FILENAME):
        print(f"\n✗ Error: File not found: {FILENAME}")
        print("Please ensure the file exists in the current directory.")
        return
    
    # ========================================================================
    # STAGE 0: INITIALIZATION
    # ========================================================================
    print_section("STAGE 0: INITIALIZATION")
    
    # Extract file metadata
    print("Extracting file metadata...")
    try:
        file_metadata = extract_all_metadata(FILENAME)
        print("✓ Metadata extracted")
        print(f"  File type: {file_metadata['basic']['extension']}")
        print(f"  File size: {file_metadata['basic']['size_kb']:.2f} KB")
    except Exception as e:
        print(f"✗ Error extracting metadata: {e}")
        return
    
    # Initialize model handler
    print("\nInitializing model handler...")
    try:
        model_handler = ModelHandler()
        print("✓ Model handler initialized")
    except Exception as e:
        print(f"✗ Error initializing model handler: {e}")
        return
    
    # Get appropriate model for file type
    print("\nSelecting specialized model...")
    file_ext = file_metadata['basic']['extension']
    model_config = model_handler.get_model_for_file(file_ext)
    print(f"✓ Model selected: {model_config['model_key']}")
    print(f"  Model name: {model_config['name']}")
    print(f"  Description: {model_config['description']}")
    print(f"  Temperature: {model_config['temperature']}")
    
    # Create session ID
    session_id = model_handler.create_session_id(FILENAME)
    print(f"\n✓ Session created: {session_id}")
    
    # Initialize Ollama client
    print("\nInitializing Ollama client...")
    try:
        client = OllamaClient()
        
        # Test connection
        if not client.test_connection():
            print("✗ Cannot connect to Ollama")
            print("  Make sure Ollama is running: ollama serve")
            return
        
        print("✓ Connected to Ollama")
        
        # Check if model is available
        available_models = client.list_available_models()
        if model_config['name'] not in available_models:
            print(f"✗ Model '{model_config['name']}' not found")
            print(f"  Run: ollama pull {model_config['name']}")
            return
        
        print(f"✓ Model '{model_config['name']}' available")
        
        # Configure client with selected model
        client.set_model(model_config)
        print("✓ Client configured with model")
        
    except Exception as e:
        print(f"✗ Error initializing Ollama client: {e}")
        return
    
    # Session data to be saved
    session_data = {
        'filename': FILENAME,
        'file_metadata': file_metadata,
        'model_config': model_config,
        'stages': {}
    }
    
    # ========================================================================
    # STAGE 1: INSPECTION
    # ========================================================================
    print_banner("STAGE 1: FILE INSPECTION")
    
    # Generate inspection prompt
    inspection_prompt = model_handler.get_inspection_prompt(file_metadata)
    
    # Execute with retry
    max_retries = model_handler.get_max_retries()
    inspection_success, inspection_code, inspection_output = execute_with_retry(
        client,
        inspection_prompt,
        "INSPECTION",
        max_retries
    )
    
    # Save stage results
    session_data['stages']['inspection'] = {
        'success': inspection_success,
        'code': inspection_code,
        'output': inspection_output,
        'timestamp': datetime.now().isoformat()
    }
    
    if not inspection_success:
        print_banner("PIPELINE FAILED - INSPECTION STAGE")
        print("Saving session data...")
        model_handler.save_session(session_data)
        return
    
    # ========================================================================
    # STAGE 2: CLEANING
    # ========================================================================
    print_banner("STAGE 2: FILE CLEANING")
    
    # Generate cleaning prompt
    cleaning_prompt = model_handler.get_cleaning_prompt(file_metadata, inspection_output)
    
    # Execute with retry
    cleaning_success, cleaning_code, cleaning_output = execute_with_retry(
        client,
        cleaning_prompt,
        "CLEANING",
        max_retries
    )
    
    # Save stage results
    session_data['stages']['cleaning'] = {
        'success': cleaning_success,
        'code': cleaning_code,
        'output': cleaning_output,
        'timestamp': datetime.now().isoformat()
    }
    
    if not cleaning_success:
        print_banner("PIPELINE FAILED - CLEANING STAGE")
        print("Saving session data...")
        model_handler.save_session(session_data)
        return
    
    # ========================================================================
    # STAGE 3: VERIFICATION
    # ========================================================================
    print_banner("STAGE 3: VERIFICATION")
    
    cleaned_filename = f"cleaned_{FILENAME}"
    
    if os.path.exists(cleaned_filename):
        file_size = os.path.getsize(cleaned_filename)
        print(f"✓ Cleaned file created: {cleaned_filename}")
        print(f"  File size: {file_size} bytes ({file_size/1024:.2f} KB)")
        
        # Type-specific verification
        ext = file_metadata['basic']['extension'].lower()
        verification_results = {'exists': True, 'size': file_size}
        
        if ext == '.csv':
            try:
                import pandas as pd
                df = pd.read_csv(cleaned_filename)
                print(f"  Rows: {len(df)}")
                print(f"  Columns: {len(df.columns)}")
                print(f"  Missing values: {df.isnull().sum().sum()}")
                verification_results.update({
                    'rows': len(df),
                    'columns': len(df.columns),
                    'missing_values': int(df.isnull().sum().sum())
                })
            except Exception as e:
                print(f"  Warning: Could not verify CSV: {e}")
                verification_results['verification_error'] = str(e)
        
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            try:
                from PIL import Image
                img = Image.open(cleaned_filename)
                print(f"  Dimensions: {img.size}")
                print(f"  Mode: {img.mode}")
                verification_results.update({
                    'dimensions': img.size,
                    'mode': img.mode
                })
            except Exception as e:
                print(f"  Warning: Could not verify image: {e}")
                verification_results['verification_error'] = str(e)
        
        elif ext in ['.txt', '.log', '.md']:
            try:
                with open(cleaned_filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.count('\n')
                    chars = len(content)
                print(f"  Lines: {lines}")
                print(f"  Characters: {chars}")
                verification_results.update({
                    'lines': lines,
                    'characters': chars
                })
            except Exception as e:
                print(f"  Warning: Could not verify text file: {e}")
                verification_results['verification_error'] = str(e)
        
        session_data['verification'] = verification_results
        session_data['success'] = True
    else:
        print(f"✗ Cleaned file not created: {cleaned_filename}")
        session_data['verification'] = {'exists': False}
        session_data['success'] = False
    
    # ========================================================================
    # STAGE 4: SESSION SUMMARY
    # ========================================================================
    print_banner("STAGE 4: SESSION SUMMARY")
    
    # Add conversation summary
    session_data['conversation'] = client.get_conversation_summary()
    
    # Save session
    print("Saving session data...")
    model_handler.save_session(session_data)
    
    # Print summary
    print_section("SUMMARY")
    print(f"File processed: {FILENAME}")
    print(f"Model used: {model_config['model_key']} ({model_config['name']})")
    print(f"Inspection: {'✓ Success' if inspection_success else '✗ Failed'}")
    print(f"Cleaning: {'✓ Success' if cleaning_success else '✗ Failed'}")
    print(f"Output file: {cleaned_filename}")
    print(f"Session ID: {session_id}")
    print(f"Session saved: {model_handler.get_session_path()}")
    
    print_banner("PIPELINE COMPLETED SUCCESSFULLY" if session_data['success'] else "PIPELINE COMPLETED WITH ERRORS")


# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Pipeline interrupted by user")
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()