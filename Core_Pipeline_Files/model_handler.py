"""
Model Handler - Assigns specialized models based on file type
"""
import json
import os
from datetime import datetime
from pathlib import Path


class ModelHandler:
    """Handles model selection and configuration based on file type"""
    
    def __init__(self, config_path="models_config.json"):
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

2. ANALYZE THOROUGHLY (Choose based on file type):

   === FOR STRUCTURED DATA (CSV, Excel, Parquet) ===
   Must analyze:
   - Row and column counts
   - Data types for EACH column
   - Missing value count AND percentage for EACH column
   - Identify columns with >70%, 20-70%, <20% missing
   - Duplicate row count
   - For numeric columns: min, max, mean, median
   - For text columns: unique value counts
   - Look for error values: "ERROR", "UNKNOWN", "N/A", "null"
   - Check for impossible values (negative prices, future dates)
   
   === FOR TEXT FILES (TXT, LOG, MD, CSV as text) ===
   Must analyze:
   - Total line count
   - Total character count
   - Encoding detected (UTF-8, Latin-1, CP1252, etc.)
   - Line ending type (LF \\n, CRLF \\r\\n, CR \\r)
   - Empty line count and distribution
   - Lines with trailing whitespace (count)
   - Lines with leading whitespace (count)
   - Control characters found (count \\x00-\\x1f)
   - Null bytes (\\x00) count
   - Non-ASCII character count
   - Average line length
   
   === FOR IMAGES (JPG, PNG, GIF, BMP, TIFF) ===
   Must analyze:
   - Width x Height (dimensions)
   - Color mode (RGB, RGBA, Grayscale, CMYK)
   - File format and compression level
   - File size in KB/MB
   - EXIF data present? (count of tags)
   - GPS data present? (privacy concern)
   - Orientation issues (needs rotation?)
   - Image quality assessment
   - Is resolution excessive? (>4K)
   
   === FOR JSON FILES ===
   Must analyze:
   - Structure depth (nested levels)
   - Total keys count
   - Data types of values
   - Null/undefined values count
   - Trailing commas (syntax errors)
   - Inconsistent formatting
   - Schema validation (if applicable)
   - File size
   
   === FOR XML/HTML FILES ===
   Must analyze:
   - Total tags count
   - Malformed tags count
   - Unclosed tags
   - Invalid characters in tags
   - Schema/DTD validation
   - Namespace issues
   - Indentation consistency
   - File size
   
   === FOR PDF FILES ===
   Must analyze:
   - Page count
   - Text extractability (% of pages with text)
   - Metadata present (author, creator, dates)
   - Embedded images count
   - File size and size per page
   - Compression used
   - Encrypted? (password protected)
   - Form fields present
   
   === FOR AUDIO FILES (WAV, MP3, FLAC, OGG) ===
   Must analyze:
   - Duration (in seconds/minutes)
   - Sample rate (Hz)
   - Bit depth (16-bit, 24-bit, etc.)
   - Channels (mono/stereo)
   - Bitrate (for compressed formats)
   - Format and codec
   - Metadata tags (artist, album, etc.)
   - Silence at start/end (detect)
   - Volume levels (peak, average)
   
   === FOR VIDEO FILES (MP4, AVI, MKV) ===
   Must analyze:
   - Duration
   - Frame rate (FPS)
   - Resolution (width x height)
   - Video codec
   - Audio codec
   - Bitrate (video and audio)
   - Audio tracks count
   - Subtitle tracks
   - Metadata present
   - File size

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
   - NO if __name__ == "__main__" blocks

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

2. APPLY YOUR CLEANING STRATEGY:

   Analyze the inspection results and decide the best cleaning approach.
   
   === FOR CSV/EXCEL/STRUCTURED DATA ===
   EXAMPLE cleaning structure:
   Step 1: Import pandas
   Step 2: Load file with pd.read_csv()
   Step 3: Replace error values ("ERROR", "UNKNOWN", "N/A", "null") with NaN
   Step 4: For text columns: use df['col'].fillna(df['col'].mode()[0])
   Step 5: For numeric columns: use df['col'].fillna(df['col'].median())
   Step 6: Remove duplicates: df = df.drop_duplicates()
   Step 7: Save: df.to_csv('cleaned_filename.csv', index=False)
   Step 8: Print final missing count
   
   === FOR TEXT FILES (TXT, LOG, MD) ===
   EXAMPLE cleaning structure:
   Step 1: Import necessary libraries
   Step 2: Read file with proper encoding detection
   Step 3: Fix encoding (convert to UTF-8)
   Step 4: Normalize line endings to \\n
   Step 5: Remove excessive blank lines (max 2 consecutive)
   Step 6: Strip trailing whitespace from each line
   Step 7: Remove control characters and null bytes
   Step 8: Save with UTF-8 encoding
   
   Common issues to fix:
   - Mixed encodings (Latin-1, CP1252, UTF-8)
   - Windows line endings (\\r\\n) → Unix (\\n)
   - Trailing spaces at end of lines
   - Multiple consecutive blank lines
   - Control characters (\\x00-\\x1f)
   
   === FOR IMAGES (JPG, PNG, GIF, BMP) ===
   EXAMPLE cleaning structure:
   Step 1: from PIL import Image
   Step 2: Load image: img = Image.open('filename')
   Step 3: Remove EXIF data: img_clean = Image.new(img.mode, img.size)
   Step 4: Copy pixel data without metadata
   Step 5: Optimize: save with optimize=True, quality=85
   Step 6: Fix orientation if needed
   Step 7: Resize if oversized (>4000px)
   Step 8: Save: img_clean.save('cleaned_filename.jpg')
   
   Common issues to fix:
   - Large EXIF data (GPS, camera info)
   - Wrong orientation (needs rotation)
   - Oversized dimensions (>4K)
   - Unoptimized compression
   
   === FOR JSON/XML FILES ===
   EXAMPLE cleaning structure:
   Step 1: import json (or xml.etree.ElementTree)
   Step 2: Load and parse the file
   Step 3: Fix syntax errors (trailing commas, quotes)
   Step 4: Remove null/undefined values if needed
   Step 5: Normalize structure (consistent formatting)
   Step 6: Validate schema/structure
   Step 7: Pretty print with proper indentation
   Step 8: Save with proper encoding
   
   Common issues to fix:
   - Trailing commas in JSON
   - Inconsistent indentation
   - Mixed quote styles
   - Null/undefined values
   - Malformed tags (XML)
   
   === FOR PDF FILES ===
   EXAMPLE cleaning structure:
   Step 1: from PyPDF2 import PdfReader, PdfWriter
   Step 2: Read PDF: reader = PdfReader('filename.pdf')
   Step 3: Create clean writer: writer = PdfWriter()
   Step 4: Copy pages without metadata
   Step 5: Remove document metadata
   Step 6: Compress if needed
   Step 7: Save: writer.write('cleaned_filename.pdf')
   Step 8: Report pages and size reduction
   
   Common issues to fix:
   - Large metadata (author, creation software)
   - Uncompressed content
   - Embedded fonts causing bloat
   
   === FOR AUDIO FILES (WAV, MP3, FLAC) ===
   EXAMPLE cleaning structure:
   Step 1: import wave (or pydub)
   Step 2: Load audio file
   Step 3: Normalize volume levels
   Step 4: Remove silence from start/end
   Step 5: Standardize sample rate (44100 Hz)
   Step 6: Convert to mono if stereo not needed
   Step 7: Remove metadata tags
   Step 8: Save in optimized format
   
   Common issues to fix:
   - Inconsistent volume levels
   - Silent periods at start/end
   - Varying sample rates
   - Large metadata/album art
   
   CRITICAL RULES FOR ALL TYPES:
   - Import ALL needed libraries at the top
   - Handle errors with try/except
   - Save the cleaned file as the LAST step
   - Print what was cleaned and final stats
   - Don't delete original file
   - NO if __name__ == "__main__" blocks
   
==================== CLEANING REPORT ====================
File: {filename}

ACTIONS TAKEN:
1. [what you did]
2. [what you did]

FINAL STATE:
- Missing values: [count]
- Rows: [count]

✓ Saved to: cleaned_{filename}
============================================================

Write clean, working Python code. No complex logic needed.
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