"""
Universal File Comparer - Automatically detects file type and compares appropriately
"""
import os
import json
from pathlib import Path


def compare_files(clean_file, dirty_file, output_report=None):
    """
    Automatically detect file type and perform appropriate comparison.
    
    Args:
        clean_file: Path to cleaned file
        dirty_file: Path to original/dirty file
        output_report: Optional custom report path
    
    Returns:
        bool: True if comparison succeeded
    """
    # Detect file type
    ext = Path(clean_file).suffix.lower()
    
    if output_report is None:
        output_report = f"comparison_report_{ext[1:]}.txt"
    
    print(f"Detected file type: {ext}")
    print(f"Comparing: {dirty_file} → {clean_file}")
    
    # Route to appropriate comparer
    if ext in ['.csv', '.tsv']:
        from csv_comparer import compare_csv_files
        try:
            compare_csv_files(clean_file, dirty_file, output_report)
            print(f"✓ CSV comparison complete: {output_report}")
            return True
        except Exception as e:
            print(f"✗ CSV comparison failed: {e}")
            return False
    
    elif ext in ['.txt', '.log', '.md', '.rst']:
        from text_comparer import compare_text_files
        try:
            compare_text_files(clean_file, dirty_file, output_report)
            print(f"✓ Text comparison complete: {output_report}")
            return True
        except Exception as e:
            print(f"✗ Text comparison failed: {e}")
            return False
    
    elif ext == '.json':
        return compare_json_files(clean_file, dirty_file, output_report)
    
    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
        return compare_image_files(clean_file, dirty_file, output_report)
    
    else:
        print(f"⚠ No specialized comparer for {ext}")
        return compare_binary_files(clean_file, dirty_file, output_report)


def compare_json_files(clean_file, dirty_file, output_report):
    """Compare JSON files"""
    import json
    
    try:
        with open(clean_file, 'r') as f:
            clean_data = json.load(f)
        with open(dirty_file, 'r') as f:
            dirty_data = json.load(f)
        
        with open(output_report, 'w') as report:
            report.write("="*80 + "\n")
            report.write("JSON COMPARISON REPORT\n")
            report.write("="*80 + "\n\n")
            
            report.write(f"Clean file: {clean_file}\n")
            report.write(f"Dirty file: {dirty_file}\n\n")
            
            # Structure comparison
            report.write("STRUCTURE:\n")
            report.write(f"Clean type: {type(clean_data).__name__}\n")
            report.write(f"Dirty type: {type(dirty_data).__name__}\n\n")
            
            if isinstance(clean_data, dict) and isinstance(dirty_data, dict):
                clean_keys = set(clean_data.keys())
                dirty_keys = set(dirty_data.keys())
                
                report.write(f"Clean keys: {len(clean_keys)}\n")
                report.write(f"Dirty keys: {len(dirty_keys)}\n")
                
                if clean_keys == dirty_keys:
                    report.write("✓ Keys match\n")
                else:
                    missing = dirty_keys - clean_keys
                    added = clean_keys - dirty_keys
                    if missing:
                        report.write(f"Removed keys: {missing}\n")
                    if added:
                        report.write(f"Added keys: {added}\n")
            
            report.write("\n" + "="*80 + "\n")
            report.write("END OF REPORT\n")
            report.write("="*80 + "\n")
        
        print(f"✓ JSON comparison complete: {output_report}")
        return True
    
    except Exception as e:
        print(f"✗ JSON comparison failed: {e}")
        return False


def compare_image_files(clean_file, dirty_file, output_report):
    """Compare image files"""
    try:
        from PIL import Image
        
        clean_img = Image.open(clean_file)
        dirty_img = Image.open(dirty_file)
        
        with open(output_report, 'w') as report:
            report.write("="*80 + "\n")
            report.write("IMAGE COMPARISON REPORT\n")
            report.write("="*80 + "\n\n")
            
            report.write(f"Clean file: {clean_file}\n")
            report.write(f"  Size: {os.path.getsize(clean_file)} bytes\n")
            report.write(f"  Dimensions: {clean_img.size}\n")
            report.write(f"  Mode: {clean_img.mode}\n")
            report.write(f"  Format: {clean_img.format}\n\n")
            
            report.write(f"Dirty file: {dirty_file}\n")
            report.write(f"  Size: {os.path.getsize(dirty_file)} bytes\n")
            report.write(f"  Dimensions: {dirty_img.size}\n")
            report.write(f"  Mode: {dirty_img.mode}\n")
            report.write(f"  Format: {dirty_img.format}\n\n")
            
            size_diff = os.path.getsize(clean_file) - os.path.getsize(dirty_file)
            report.write(f"Size change: {size_diff:+d} bytes ")
            report.write(f"({size_diff/os.path.getsize(dirty_file)*100:+.1f}%)\n")
            
            if clean_img.size != dirty_img.size:
                report.write(f"⚠ Dimensions changed: {dirty_img.size} → {clean_img.size}\n")
            else:
                report.write(f"✓ Dimensions unchanged\n")
            
            if clean_img.mode != dirty_img.mode:
                report.write(f"⚠ Color mode changed: {dirty_img.mode} → {clean_img.mode}\n")
            else:
                report.write(f"✓ Color mode unchanged\n")
            
            # EXIF comparison
            dirty_exif = dirty_img.getexif() if hasattr(dirty_img, 'getexif') else {}
            clean_exif = clean_img.getexif() if hasattr(clean_img, 'getexif') else {}
            
            report.write(f"\nEXIF data:\n")
            report.write(f"  Dirty: {len(dirty_exif)} tags\n")
            report.write(f"  Clean: {len(clean_exif)} tags\n")
            if len(clean_exif) < len(dirty_exif):
                report.write(f"  ✓ Removed {len(dirty_exif) - len(clean_exif)} EXIF tags\n")
            
            report.write("\n" + "="*80 + "\n")
            report.write("END OF REPORT\n")
            report.write("="*80 + "\n")
        
        print(f"✓ Image comparison complete: {output_report}")
        return True
    
    except Exception as e:
        print(f"✗ Image comparison failed: {e}")
        return False


def compare_binary_files(clean_file, dirty_file, output_report):
    """Generic binary file comparison"""
    with open(output_report, 'w') as report:
        report.write("="*80 + "\n")
        report.write("BINARY FILE COMPARISON REPORT\n")
        report.write("="*80 + "\n\n")
        
        clean_size = os.path.getsize(clean_file)
        dirty_size = os.path.getsize(dirty_file)
        
        report.write(f"Clean file: {clean_file}\n")
        report.write(f"  Size: {clean_size} bytes ({clean_size/1024:.2f} KB)\n\n")
        
        report.write(f"Dirty file: {dirty_file}\n")
        report.write(f"  Size: {dirty_size} bytes ({dirty_size/1024:.2f} KB)\n\n")
        
        size_diff = clean_size - dirty_size
        report.write(f"Size difference: {size_diff:+d} bytes ")
        if dirty_size > 0:
            report.write(f"({size_diff/dirty_size*100:+.1f}%)\n")
        else:
            report.write("\n")
        
        # Check if files are identical
        with open(clean_file, 'rb') as f1, open(dirty_file, 'rb') as f2:
            identical = f1.read() == f2.read()
        
        if identical:
            report.write("\n✓ Files are identical\n")
        else:
            report.write("\n⚠ Files are different\n")
        
        report.write("\n" + "="*80 + "\n")
        report.write("END OF REPORT\n")
        report.write("="*80 + "\n")
    
    print(f"✓ Binary comparison complete: {output_report}")
    return True


# ============================================================================
# CLI Interface
# ============================================================================
if __name__ == "__main__":
    import sys
    
    print("Universal File Comparer")
    print("="*80)
    
    if len(sys.argv) >= 3:
        dirty_file = sys.argv[1]
        clean_file = sys.argv[2]
        output_report = sys.argv[3] if len(sys.argv) > 3 else None
    else:
        # Interactive mode
        dirty_file = input("Enter original/dirty file path: ").strip()
        clean_file = input("Enter cleaned file path: ").strip()
        output_report = input("Enter report path (press Enter for default): ").strip()
        output_report = output_report if output_report else None
    
    # Validate files exist
    if not os.path.exists(dirty_file):
        print(f"✗ Error: File not found: {dirty_file}")
        sys.exit(1)
    
    if not os.path.exists(clean_file):
        print(f"✗ Error: File not found: {clean_file}")
        sys.exit(1)
    
    # Run comparison
    print()
    success = compare_files(clean_file, dirty_file, output_report)
    
    if success:
        print("\n✓ Comparison completed successfully")
        sys.exit(0)
    else:
        print("\n✗ Comparison failed")
        sys.exit(1)