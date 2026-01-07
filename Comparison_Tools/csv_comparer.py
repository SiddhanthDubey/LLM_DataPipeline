import pandas as pd
import numpy as np

def compare_csv_files(clean_file, dirty_file, output_report='comparison_report.txt'):
    """
    Compare two CSV files - one clean and one dirty.
    
    Parameters:
    - clean_file: path to the clean CSV file
    - dirty_file: path to the dirty/uncleaned CSV file
    - output_report: path to save the comparison report
    """
    
    # Read both CSV files
    print("Reading CSV files...")
    df_clean = pd.read_csv(clean_file)
    df_dirty = pd.read_csv(dirty_file)
    
    # Open report file
    with open(output_report, 'w') as report:
        report.write("="*80 + "\n")
        report.write("CSV COMPARISON REPORT\n")
        report.write("="*80 + "\n\n")
        
        # 1. Basic Structure Comparison
        report.write("1. BASIC STRUCTURE\n")
        report.write("-"*80 + "\n")
        report.write(f"Clean file shape: {df_clean.shape}\n")
        report.write(f"Dirty file shape: {df_dirty.shape}\n")
        report.write(f"Row difference: {df_dirty.shape[0] - df_clean.shape[0]}\n")
        report.write(f"Column difference: {df_dirty.shape[1] - df_clean.shape[1]}\n\n")
        
        # 2. Column Comparison
        report.write("2. COLUMN COMPARISON\n")
        report.write("-"*80 + "\n")
        clean_cols = set(df_clean.columns)
        dirty_cols = set(df_dirty.columns)
        
        if clean_cols == dirty_cols:
            report.write("✓ Columns match perfectly\n")
        else:
            missing_in_dirty = clean_cols - dirty_cols
            extra_in_dirty = dirty_cols - clean_cols
            
            if missing_in_dirty:
                report.write(f"Columns in clean but missing in dirty: {missing_in_dirty}\n")
            if extra_in_dirty:
                report.write(f"Extra columns in dirty: {extra_in_dirty}\n")
        report.write("\n")
        
        # 3. Data Quality Metrics (for common columns)
        common_cols = list(clean_cols.intersection(dirty_cols))
        
        report.write("3. DATA QUALITY COMPARISON (Common Columns)\n")
        report.write("-"*80 + "\n")
        
        for col in common_cols:
            report.write(f"\nColumn: {col}\n")
            report.write(f"  Clean - Nulls: {df_clean[col].isna().sum()}, "
                        f"Unique: {df_clean[col].nunique()}\n")
            report.write(f"  Dirty - Nulls: {df_dirty[col].isna().sum()}, "
                        f"Unique: {df_dirty[col].nunique()}\n")
            
            # Check for duplicates
            if df_clean.shape[0] == df_dirty.shape[0]:
                differences = (df_clean[col] != df_dirty[col]).sum()
                report.write(f"  Different values: {differences}\n")
        
        # 4. Missing Values Summary
        report.write("\n4. MISSING VALUES SUMMARY\n")
        report.write("-"*80 + "\n")
        report.write("Clean file missing values:\n")
        report.write(str(df_clean.isna().sum()) + "\n\n")
        report.write("Dirty file missing values:\n")
        report.write(str(df_dirty.isna().sum()) + "\n\n")
        
        # 5. Duplicate Rows
        report.write("5. DUPLICATE ROWS\n")
        report.write("-"*80 + "\n")
        report.write(f"Clean file duplicates: {df_clean.duplicated().sum()}\n")
        report.write(f"Dirty file duplicates: {df_dirty.duplicated().sum()}\n\n")
        
        # 6. Data Type Comparison
        report.write("6. DATA TYPES\n")
        report.write("-"*80 + "\n")
        for col in common_cols:
            clean_type = df_clean[col].dtype
            dirty_type = df_dirty[col].dtype
            if clean_type != dirty_type:
                report.write(f"{col}: Clean={clean_type}, Dirty={dirty_type}\n")
        
        report.write("\n" + "="*80 + "\n")
        report.write("END OF REPORT\n")
        report.write("="*80 + "\n")
    
    print(f"Comparison report saved to: {output_report}")
    
    # Display sample differences if files have same shape
    if df_clean.shape == df_dirty.shape and len(common_cols) > 0:
        print("\nSample of differing rows (first 5):")
        mask = (df_clean[common_cols] != df_dirty[common_cols]).any(axis=1)
        if mask.sum() > 0:
            print(df_dirty[mask].head())
        else:
            print("No differences found in data values!")
    
    return df_clean, df_dirty


# Example usage
if __name__ == "__main__":
    # Replace these with your actual file paths
    clean_file = "/home/dent1st/SPPproject/ProjectV4/Core_Pipeline_Files/cleaned_Titanic-Dataset.csv"
    dirty_file = "/home/dent1st/SPPproject/ProjectV4/Core_Pipeline_Files/Titanic-Dataset.csv"
    
    try:
        df_clean, df_dirty = compare_csv_files(clean_file, dirty_file)
        print("\nComparison complete! Check 'comparison_report.txt' for details.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please update the file paths in the script.")
    except Exception as e:
        print(f"An error occurred: {e}")