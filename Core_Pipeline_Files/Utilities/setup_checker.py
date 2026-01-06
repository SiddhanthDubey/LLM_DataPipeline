"""
Setup Checker - Verify that everything is configured correctly
"""
import os
import sys
import json
from pathlib import Path


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*80)
    print(text.center(80))
    print("="*80)


def print_status(check_name, passed, message=""):
    """Print check status"""
    symbol = "✓" if passed else "✗"
    status = "PASS" if passed else "FAIL"
    print(f"{symbol} {check_name:<50} [{status}]")
    if message:
        print(f"  └─ {message}")


def check_python_version():
    """Check Python version"""
    version = sys.version_info
    passed = version.major >= 3 and version.minor >= 8
    msg = f"Python {version.major}.{version.minor}.{version.micro}"
    print_status("Python Version (>= 3.8)", passed, msg)
    return passed


def check_required_modules():
    """Check if required Python modules are installed"""
    required = {
        'pandas': 'pandas',
        'requests': 'requests',
        'PIL': 'Pillow (for image processing)',
        'numpy': 'numpy'
    }
    
    all_passed = True
    for module, package_name in required.items():
        try:
            __import__(module)
            print_status(f"Module: {package_name}", True)
        except ImportError:
            print_status(f"Module: {package_name}", False, f"Install: pip install {package_name.split()[0]}")
            all_passed = False
    
    return all_passed


def check_ollama_connection():
    """Check if Ollama is running"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        response.raise_for_status()
        print_status("Ollama Connection", True, "Ollama is running")
        return True
    except Exception as e:
        print_status("Ollama Connection", False, "Run: ollama serve")
        return False


def check_ollama_models():
    """Check which Ollama models are installed"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        response.raise_for_status()
        models = response.json().get('models', [])
        model_names = [m['name'] for m in models]
        
        print_status("Ollama Models Available", len(model_names) > 0, f"Found {len(model_names)} model(s)")
        
        # Check for required models
        required_models = ['llama3.2:3b', 'llama3.2:1b']
        for model in required_models:
            if model in model_names:
                print_status(f"  Model: {model}", True)
            else:
                print_status(f"  Model: {model}", False, f"Run: ollama pull {model}")
        
        return len(model_names) > 0
    except:
        print_status("Ollama Models Check", False, "Ollama not running")
        return False


def check_config_file():
    """Check if models_config.json exists and is valid"""
    config_file = "models_config.json"
    
    if not os.path.exists(config_file):
        print_status("Configuration File", False, f"{config_file} not found")
        return False
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Validate structure
        required_keys = ['models', 'file_type_mapping', 'settings']
        has_all_keys = all(key in config for key in required_keys)
        
        if has_all_keys:
            model_count = len(config['models'])
            mapping_count = len(config['file_type_mapping'])
            print_status("Configuration File", True, f"{model_count} models, {mapping_count} file types")
            return True
        else:
            print_status("Configuration File", False, "Invalid structure")
            return False
    except json.JSONDecodeError:
        print_status("Configuration File", False, "Invalid JSON syntax")
        return False


def check_project_structure():
    """Check if all required files exist"""
    required_files = {
        'mainV3.py': 'Main pipeline script',
        'model_handler.py': 'Model handler',
        'ollama_client.py': 'Ollama client',
        'models_config.json': 'Model configuration',
        'universal_comparer.py': 'Universal comparer'
    }
    
    all_present = True
    for filename, description in required_files.items():
        exists = os.path.exists(filename)
        print_status(f"File: {filename}", exists, description if exists else "Missing!")
        if not exists:
            all_present = False
    
    return all_present


def check_directories():
    """Check if required directories exist or can be created"""
    required_dirs = {
        'sessions': 'Session storage',
        'block1': 'Utility modules'
    }
    
    all_ok = True
    for dirname, description in required_dirs.items():
        exists = os.path.exists(dirname)
        
        if not exists:
            try:
                Path(dirname).mkdir(parents=True, exist_ok=True)
                print_status(f"Directory: {dirname}", True, f"Created ({description})")
            except Exception as e:
                print_status(f"Directory: {dirname}", False, f"Cannot create: {e}")
                all_ok = False
        else:
            print_status(f"Directory: {dirname}", True, description)
    
    return all_ok


def check_metadata_extractor():
    """Check if metadata extractor is available"""
    try:
        from block1.metadata_extractor import extract_all_metadata
        print_status("Metadata Extractor", True, "block1.metadata_extractor available")
        return True
    except ImportError as e:
        print_status("Metadata Extractor", False, str(e))
        return False


def check_code_executor():
    """Check if code executor is available"""
    try:
        from codeExecBlock.code_exec import execute_code_capture_output
        print_status("Code Executor", True, "codeExecBlock.code_exec available")
        return True
    except ImportError as e:
        print_status("Code Executor", False, str(e))
        return False


def check_regex_extractor():
    """Check if regex code extractor is available"""
    try:
        from REblock.re import extract_python_code
        print_status("Regex Extractor", True, "REblock.re available")
        return True
    except ImportError as e:
        print_status("Regex Extractor", False, str(e))
        return False


def generate_report(results):
    """Generate final report"""
    print_header("SETUP VERIFICATION SUMMARY")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    percentage = (passed / total) * 100
    
    print(f"\nTests Passed: {passed}/{total} ({percentage:.1f}%)")
    
    if percentage == 100:
        print("\n✓ Your system is ready!")
        print("  Run: python3 mainV3.py")
    elif percentage >= 80:
        print("\n⚠ Your system is mostly ready but has some issues.")
        print("  Review the failed checks above and fix them.")
    else:
        print("\n✗ Your system needs setup.")
        print("  Please fix the failed checks above before running the pipeline.")
    
    print("\nNext Steps:")
    if not results.get('ollama_connection'):
        print("  1. Start Ollama: ollama serve")
    if not results.get('ollama_models'):
        print("  2. Install models: ollama pull llama3.2:3b && ollama pull llama3.2:1b")
    if not results.get('config_file'):
        print("  3. Create models_config.json (template provided)")
    if passed == total:
        print("  1. Edit FILENAME in mainV3.py")
        print("  2. Run: python3 mainV3.py")
        print("  3. Check results in ./sessions/")


def main():
    """Run all checks"""
    print_header("PIPELINE V3 SETUP VERIFICATION")
    print("Checking your system configuration...\n")
    
    results = {}
    
    # System checks
    print("\n" + "-"*80)
    print("SYSTEM REQUIREMENTS")
    print("-"*80)
    results['python'] = check_python_version()
    results['modules'] = check_required_modules()
    
    # Ollama checks
    print("\n" + "-"*80)
    print("OLLAMA SETUP")
    print("-"*80)
    results['ollama_connection'] = check_ollama_connection()
    results['ollama_models'] = check_ollama_models()
    
    # Project structure checks
    print("\n" + "-"*80)
    print("PROJECT STRUCTURE")
    print("-"*80)
    results['config_file'] = check_config_file()
    results['project_files'] = check_project_structure()
    results['directories'] = check_directories()
    
    # Module checks
    print("\n" + "-"*80)
    print("PROJECT MODULES")
    print("-"*80)
    results['metadata_extractor'] = check_metadata_extractor()
    results['code_executor'] = check_code_executor()
    results['regex_extractor'] = check_regex_extractor()
    
    # Generate report
    generate_report(results)
    
    print("\n" + "="*80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup check interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error during setup check: {e}")
        import traceback
        traceback.print_exc()