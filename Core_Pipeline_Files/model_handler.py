"""
Model Handler - Assigns specialized models based on file type
"""
import json
import os
from datetime import datetime
from pathlib import Path


class ModelHandler:
    """Handles model selection and configuration based on file type"""
    
    def __init__(self, config_path="/home/dent1st/SPPproject/ProjectV4/Core_Pipeline_Files/models_config.json"):
        """
        Initialize the model handler.
        
        Args:
            config_path: Path to the models configuration JSON file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.current_model = None
        self.current_session_id = None
        
        # Create session storage directory if needed
        session_path = self.config['settings']['session_storage_path']
        Path(session_path).mkdir(parents=True, exist_ok=True)
    
    def _load_config(self):
        """Load model configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                "Please ensure models_config.json exists in the project directory."
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
    
    def get_model_for_file(self, file_extension):
        """
        Get the appropriate model configuration for a file type.
        
        Args:
            file_extension: File extension (e.g., '.csv', '.txt')
        
        Returns:
            dict: Model configuration including name, prompts, and parameters
        """
        # Normalize extension
        extension = file_extension.lower()
        if not extension.startswith('.'):
            extension = f'.{extension}'
        
        # Get model key from mapping
        model_key = self.config['file_type_mapping'].get(
            extension,
            self.config['settings']['default_model']
        )
        
        # Get model configuration
        model_config = self.config['models'].get(model_key)
        
        if not model_config:
            # Fallback to general cleaner
            model_key = self.config['settings']['default_model']
            model_config = self.config['models'][model_key]
        
        # Add metadata
        model_config['model_key'] = model_key
        model_config['file_extension'] = extension
        
        self.current_model = model_config
        return model_config
    
    def create_session_id(self, filename):
        """
        Create a unique session ID for this processing run.
        
        Args:
            filename: Name of the file being processed
        
        Returns:
            str: Unique session identifier
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = filename.replace('.', '_').replace('/', '_').replace('\\', '_')
        session_id = f"{safe_filename}_{timestamp}"
        self.current_session_id = session_id
        return session_id
    
    def get_session_path(self):
        """Get the path for storing this session's data"""
        if not self.current_session_id:
            raise ValueError("No active session. Call create_session_id first.")
        
        session_dir = Path(self.config['settings']['session_storage_path'])
        return session_dir / f"{self.current_session_id}.json"
    
    def save_session(self, session_data):
        """
        Save session data to file.
        
        Args:
            session_data: Dictionary containing session information
        """
        if not self.config['settings']['log_sessions']:
            return
        
        session_path = self.get_session_path()
        
        # Add metadata
        session_data['session_id'] = self.current_session_id
        session_data['timestamp'] = datetime.now().isoformat()
        session_data['model_used'] = self.current_model
        
        with open(session_path, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        print(f"Session saved: {session_path}")
    
    def get_inspection_prompt(self, file_metadata):
        """
        Generate inspection prompt with model's system context.
        
        Args:
            file_metadata: Dictionary containing file metadata
        
        Returns:
            str: Formatted inspection prompt
        """
        model = self.current_model
        extension = file_metadata['basic']['extension']
        filename = file_metadata['basic']['filename']
        
        return f"""You are analyzing a file for inspection.

FILE METADATA:
{json.dumps(file_metadata, indent=2)}

DETECTED FILE TYPE: {extension}
ASSIGNED MODEL: {model['model_key']} ({model['description']})

YOUR EXPERTISE:
{model['system_prompt']}

YOUR TASK - FILE INSPECTION:

1. LOAD THE FILE:
   - Use filename: '{filename}'
   - Choose appropriate library for {extension} files
   - Handle any loading errors gracefully

2. ANALYZE THOROUGHLY:
   For structured data (CSV, Excel):
   - Row and column counts
   - Data types for each column
   - Missing value analysis (count and percentage)
   - Duplicate row detection
   - Statistical summary for numeric columns
   - Unique value counts for categorical columns
   - Identify columns with high missing % (>70%, 20-70%, <20%)
   
   For text files (TXT, LOG, MD):
   - Line and character counts
   - Encoding detection
   - Line ending type (LF, CRLF, CR)
   - Empty line count
   - Whitespace issues (trailing/leading)
   - Control character detection
   
   For images (JPG, PNG, etc.):
   - Dimensions (width x height)
   - Color mode (RGB, RGBA, Grayscale)
   - File format and compression info
   - EXIF data presence
   - File size analysis
   
   For JSON/XML:
   - Structure depth and complexity
   - Key/attribute presence
   - Schema validation
   - Syntax errors
   
   For audio/video:
   - Duration and format
   - Quality metrics (sample rate, bitrate)
   - Codec information
   
   For documents (PDF, DOCX):
   - Page/section count
   - Text extractability
   - Metadata present

3. IDENTIFY ISSUES:
   - List ALL problems found
   - Categorize by severity: CRITICAL, WARNING, INFO
   - Quantify each issue (e.g., "45 rows missing Age data")

4. RECOMMEND ACTIONS:
   - Specific cleaning steps needed
   - Priority order for fixes

5. CODE REQUIREMENTS:
   - Write EXECUTABLE Python code
   - Include all necessary imports
   - Use try/except for error handling
   - Print clear, structured output
   - NO function definitions without calls

6. OUTPUT FORMAT:
==================== INSPECTION REPORT ====================
File: {filename}
Type: {extension}
Model: {model['model_key']}

[Your detailed analysis here]

ISSUES FOUND:
[CRITICAL] - [description]
[WARNING] - [description]
[INFO] - [description]

RECOMMENDED CLEANING ACTIONS:
1. [action]
2. [action]
============================================================

Return ONLY executable Python code."""

    def get_cleaning_prompt(self, file_metadata, inspection_output):
        """
        Generate cleaning prompt with model's system context.
        
        Args:
            file_metadata: Dictionary containing file metadata
            inspection_output: Output from inspection stage
        
        Returns:
            str: Formatted cleaning prompt
        """
        model = self.current_model
        extension = file_metadata['basic']['extension']
        filename = file_metadata['basic']['filename']
        
        return f"""You are cleaning a file based on inspection results.

FILE METADATA:
{json.dumps(file_metadata, indent=2)}

YOUR EXPERTISE:
{model['system_prompt']}

INSPECTION RESULTS:
{inspection_output}

YOUR TASK - FILE CLEANING:

1. ANALYZE INSPECTION OUTPUT:
   - Parse all issues found
   - Prioritize by severity
   - Plan cleaning strategy

2. APPLY SPECIALIZED CLEANING:

   For STRUCTURED DATA (CSV, Excel, Parquet):
   a) Missing Values Strategy:
      - Columns >70% missing → DROP COLUMN (document reason)
      - Columns 20-70% missing → IMPUTE:
        * Numeric: median grouped by related column
        * Categorical: mode (most frequent)
        * Boolean: mode
        * DateTime: forward/backward fill
      - Columns <20% missing → IMPUTE (prefer over deletion)
   
   b) Data Quality:
      - Remove exact duplicates
      - Fix data types (category dtype for low-cardinality)
      - Strip whitespace from strings
      - Remove control characters and null bytes
      - Validate ranges (no negative ages, impossible dates)
   
   c) CRITICAL - Use MODERN pandas:
      ✓ df['col'] = df['col'].fillna(value)
      ✗ df['col'].fillna(value, inplace=True)  # DEPRECATED
   
   For TEXT FILES (TXT, LOG, MD):
   - Convert to UTF-8 encoding
   - Normalize line endings to LF
   - Remove excessive blank lines (keep max 2 consecutive)
   - Strip trailing whitespace
   - Remove control characters
   - Fix common encoding artifacts
   
   For IMAGES (JPG, PNG, etc.):
   - Remove EXIF data (privacy)
   - Optimize compression (maintain quality)
   - Fix orientation based on EXIF
   - Resize if oversized (>4K resolution)
   - Convert to efficient format if needed
   
   For JSON/XML:
   - Fix syntax errors (trailing commas, malformed tags)
   - Validate structure
   - Normalize formatting
   - Handle null values appropriately
   
   For AUDIO/VIDEO:
   - Normalize audio levels
   - Remove silence from start/end
   - Standardize format/codec
   - Fix metadata issues
   
   For DOCUMENTS (PDF, DOCX):
   - Extract and clean text
   - Remove metadata
   - Fix encoding issues
   - Optimize file size

3. PRESERVATION PRIORITY:
   - ALWAYS prefer data preservation over deletion
   - Only drop columns if >70% missing
   - Document every change made
   - Maintain original structure when possible

4. CODE REQUIREMENTS:
   - Write EXECUTABLE Python code
   - Include all imports
   - Comprehensive error handling
   - Print progress and results
   - Save to: 'cleaned_{filename}'

5. OUTPUT FORMAT:
==================== CLEANING REPORT ====================
File: {filename}
Type: {extension}
Model: {model['model_key']}

ACTIONS TAKEN:
1. [action]: [details, counts]
2. [action]: [details, counts]

RESULTS:
Before → After
- Rows/Items: [x] → [y]
- Columns/Fields: [x] → [y]
- Missing values: [x] → [y]
- File size: [x] KB → [y] KB

✓ Saved to: cleaned_{filename}
============================================================

Return ONLY executable Python code."""

    def get_max_retries(self):
        """Get maximum retry attempts from config"""
        return self.config['settings']['max_retries']
    
    def get_model_info(self):
        """Get current model information for display"""
        if not self.current_model:
            return "No model assigned"
        
        return {
            'model_key': self.current_model['model_key'],
            'model_name': self.current_model['name'],
            'description': self.current_model['description'],
            'temperature': self.current_model['temperature']
        }


# Convenience functions
def create_default_config():
    """Create a default models_config.json if it doesn't exist"""
    if os.path.exists("models_config.json"):
        print("models_config.json already exists")
        return
    
    default_config = {
        "models": {
            "csv_cleaner": {
                "name": "llama3.2:3b",
                "description": "Specialized model for structured data",
                "temperature": 0.3,
                "system_prompt": "You are a data cleaning expert...",
                "max_tokens": 4000,
                "top_p": 0.9
            },
            "general_cleaner": {
                "name": "llama3.2:3b",
                "description": "General-purpose cleaner",
                "temperature": 0.5,
                "system_prompt": "You are a file processing expert...",
                "max_tokens": 4000,
                "top_p": 0.9
            }
        },
        "file_type_mapping": {
            ".csv": "csv_cleaner"
        },
        "settings": {
            "default_model": "general_cleaner",
            "max_retries": 3,
            "enable_memory": True,
            "log_sessions": True,
            "session_storage_path": "./sessions"
        }
    }
    
    with open("models_config.json", 'w') as f:
        json.dump(default_config, f, indent=2)
    
    print("Created default models_config.json")


if __name__ == "__main__":
    # Test the model handler
    print("Testing ModelHandler...")
    
    handler = ModelHandler()
    
    # Test CSV file
    print("\n1. Testing CSV file:")
    model = handler.get_model_for_file('.csv')
    print(f"   Model: {model['name']}")
    print(f"   Description: {model['description']}")
    
    # Test text file
    print("\n2. Testing TXT file:")
    model = handler.get_model_for_file('.txt')
    print(f"   Model: {model['name']}")
    print(f"   Description: {model['description']}")
    
    # Test unknown file
    print("\n3. Testing unknown file (.xyz):")
    model = handler.get_model_for_file('.xyz')
    print(f"   Model: {model['name']} (fallback)")
    print(f"   Description: {model['description']}")
    
    print("\n✓ ModelHandler test complete!")