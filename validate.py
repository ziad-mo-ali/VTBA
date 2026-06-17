#!/usr/bin/env python3
"""
Validation script to compare Java and Python bug assignment outputs.

Loads both output TSVs, aligns rows by natural key (project, bugNumber, assignmentDate),
compares columns, and reports mismatches with detailed statistics.

Usage:
    python validate.py --java-output ./path/to/java/output.tsv --python-output ./path/to/python/output.tsv
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd


def load_output_file(filepath: str, source_name: str) -> pd.DataFrame:
    """Load output TSV file with pandas."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"{source_name} file not found: {path}")
    
    try:
        df = pd.read_csv(path, sep='\t', dtype=str)
        print(f"[OK] Loaded {source_name}: {len(df)} rows, {len(df.columns)} columns")
        print(f"     Columns: {', '.join(df.columns.tolist())}")
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load {source_name} file: {e}")


def find_natural_key_columns(java_df: pd.DataFrame, python_df: pd.DataFrame) -> Tuple[List[str], str]:
    """
    Identify natural key columns present in both files.
    Priority: (project, bugNumber, assignmentDate) or (projectId, bugNumber, assignmentDate)
    Falls back to common columns if exact match not found.
    """
    common_cols = set(java_df.columns) & set(python_df.columns)
    
    # Try preferred natural keys in order
    preferred_keys = [
        ['project', 'bugNumber', 'assignmentDate'],
        ['projectId', 'bugNumber', 'assignmentDate'],
        ['project', 'bugNumber'],
        ['projectId', 'bugNumber'],
    ]
    
    for key_combo in preferred_keys:
        if all(col in common_cols for col in key_combo):
            key_desc = f"({', '.join(key_combo)})"
            print(f"[OK] Using natural key: {key_desc}")
            return key_combo, key_desc
    
    if not common_cols:
        raise ValueError("No common columns found between Java and Python outputs")
    
    raise ValueError(
        f"Could not identify a suitable natural key. Common columns: {', '.join(sorted(common_cols))}"
    )


def align_dataframes(
    java_df: pd.DataFrame, 
    python_df: pd.DataFrame, 
    key_cols: List[str]
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, int]]:
    """
    Align Java and Python dataframes by natural key.
    Returns aligned Java DF, aligned Python DF, and alignment stats.
    """
    java_df = java_df.copy()
    python_df = python_df.copy()
    
    # Create composite key
    java_df['__key__'] = java_df[key_cols].apply(lambda row: tuple(row), axis=1)
    python_df['__key__'] = python_df[key_cols].apply(lambda row: tuple(row), axis=1)
    
    java_keys = set(java_df['__key__'])
    python_keys = set(python_df['__key__'])
    
    common_keys = java_keys & python_keys
    only_java_keys = java_keys - python_keys
    only_python_keys = python_keys - java_keys
    
    stats = {
        'total_java_rows': len(java_df),
        'total_python_rows': len(python_df),
        'common_rows': len(common_keys),
        'only_java': len(only_java_keys),
        'only_python': len(only_python_keys),
    }
    
    # Filter to common keys
    java_aligned = java_df[java_df['__key__'].isin(common_keys)].reset_index(drop=True)
    python_aligned = python_df[python_df['__key__'].isin(common_keys)].reset_index(drop=True)
    
    # Sort by key for alignment
    java_aligned = java_aligned.sort_values(by='__key__').reset_index(drop=True)
    python_aligned = python_aligned.sort_values(by='__key__').reset_index(drop=True)
    
    return java_aligned, python_aligned, stats


def compare_dataframes(
    java_df: pd.DataFrame,
    python_df: pd.DataFrame,
    key_cols: List[str]
) -> Tuple[List[Dict], Dict]:
    """
    Compare aligned dataframes column by column.
    Returns list of mismatches and comparison statistics.
    """
    mismatches = []
    comparison_stats = {
        'total_comparisons': 0,
        'perfect_matches': 0,
        'mismatches': 0,
        'columns_with_mismatches': set(),
    }
    
    # Find common columns (excluding the __key__ column)
    common_cols = sorted((set(java_df.columns) & set(python_df.columns)) - {'__key__'})
    
    print(f"\n[INFO] Comparing {len(common_cols)} common columns across {len(java_df)} rows")
    
    for row_idx in range(len(java_df)):
        row_mismatches = {}
        key_tuple = java_df.iloc[row_idx]['__key__']
        
        for col in common_cols:
            java_val = str(java_df.iloc[row_idx][col])
            python_val = str(python_df.iloc[row_idx][col])
            
            comparison_stats['total_comparisons'] += 1
            
            if java_val != python_val:
                row_mismatches[col] = {
                    'java_value': java_val,
                    'python_value': python_val,
                }
                comparison_stats['mismatches'] += 1
                comparison_stats['columns_with_mismatches'].add(col)
            else:
                comparison_stats['perfect_matches'] += 1
        
        if row_mismatches:
            mismatches.append({
                'key': key_tuple,
                'fields': row_mismatches,
            })
    
    return mismatches, comparison_stats


def print_mismatches(mismatches: List[Dict], key_cols: List[str], max_display: int = 20) -> None:
    """Print detailed mismatch report."""
    if not mismatches:
        print("\n[SUCCESS] No mismatches found!")
        return
    
    print(f"\n{'='*100}")
    print(f"MISMATCHES FOUND: {len(mismatches)} rows with differences")
    print(f"{'='*100}\n")
    
    for i, mismatch in enumerate(mismatches[:max_display]):
        print(f"Row {i+1}/{len(mismatches)}")
        print(f"  Key: {mismatch['key']}")
        
        for field, values in mismatch['fields'].items():
            java_val = values['java_value']
            python_val = values['python_value']
            print(f"  [{field}]")
            print(f"    Java:   {java_val}")
            print(f"    Python: {python_val}")
        print()
    
    if len(mismatches) > max_display:
        print(f"... and {len(mismatches) - max_display} more mismatches (not displayed)")


def print_summary(
    alignment_stats: Dict,
    comparison_stats: Dict,
    key_cols: List[str],
    mismatches: List[Dict]
) -> None:
    """Print comprehensive summary statistics."""
    print(f"\n{'='*100}")
    print("VALIDATION SUMMARY")
    print(f"{'='*100}\n")
    
    print("ALIGNMENT STATISTICS:")
    print(f"  Java output total rows:    {alignment_stats['total_java_rows']:>10,}")
    print(f"  Python output total rows:  {alignment_stats['total_python_rows']:>10,}")
    print(f"  Aligned common rows:       {alignment_stats['common_rows']:>10,}")
    print(f"  Only in Java:              {alignment_stats['only_java']:>10,}")
    print(f"  Only in Python:            {alignment_stats['only_python']:>10,}")
    
    alignment_rate = (alignment_stats['common_rows'] / max(alignment_stats['total_java_rows'], 1)) * 100
    print(f"  Alignment rate:            {alignment_rate:>10.2f}%\n")
    
    print("COMPARISON STATISTICS:")
    print(f"  Natural key columns:       {', '.join(key_cols)}")
    print(f"  Total field comparisons:   {comparison_stats['total_comparisons']:>10,}")
    print(f"  Perfect matches:           {comparison_stats['perfect_matches']:>10,}")
    print(f"  Mismatches:                {comparison_stats['mismatches']:>10,}")
    
    match_rate = (comparison_stats['perfect_matches'] / max(comparison_stats['total_comparisons'], 1)) * 100
    print(f"  Match rate:                {match_rate:>10.2f}%\n")
    
    print("COLUMNS WITH MISMATCHES:")
    if comparison_stats['columns_with_mismatches']:
        for col in sorted(comparison_stats['columns_with_mismatches']):
            print(f"  - {col}")
    else:
        print("  (none)")
    
    mismatch_rows = len(mismatches)
    rows_with_diffs = alignment_stats['common_rows']
    mismatch_rate = (mismatch_rows / max(rows_with_diffs, 1)) * 100
    
    print(f"\nROW-LEVEL STATISTICS:")
    print(f"  Rows with differences:     {mismatch_rows:>10,}")
    print(f"  Rows compared:             {rows_with_diffs:>10,}")
    print(f"  Mismatch row rate:         {mismatch_rate:>10.2f}%")
    
    if mismatch_rate == 0:
        print("\n[SUCCESS] All rows match perfectly!")
    elif mismatch_rate < 1:
        print(f"\n[WARNING] {mismatch_rate:.2f}% of rows have mismatches")
    else:
        print(f"\n[ERROR] {mismatch_rate:.2f}% of rows have mismatches")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Compare Java and Python bug assignment outputs for validation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate.py --java-output ./Exp/Out/outDetails/exp1/file.tsv --python-output ./output.tsv
  python validate.py --java-output ./java_result.tsv --python-output ./python_result.tsv
        """,
    )
    
    parser.add_argument(
        '--java-output',
        type=str,
        required=True,
        help='Path to Java output TSV file',
    )
    
    parser.add_argument(
        '--python-output',
        type=str,
        required=True,
        help='Path to Python output TSV file',
    )
    
    parser.add_argument(
        '--show-mismatches',
        type=int,
        default=20,
        help='Number of mismatches to display in detail (default: 20)',
    )
    
    args = parser.parse_args()
    
    try:
        # Load files
        print("[STEP 1] Loading output files...")
        java_df = load_output_file(args.java_output, "Java output")
        python_df = load_output_file(args.python_output, "Python output")
        
        # Find natural key
        print("\n[STEP 2] Identifying natural key...")
        key_cols, key_desc = find_natural_key_columns(java_df, python_df)
        
        # Align dataframes
        print("\n[STEP 3] Aligning dataframes by natural key...")
        java_aligned, python_aligned, alignment_stats = align_dataframes(java_df, python_df, key_cols)
        
        if alignment_stats['only_java'] > 0:
            print(f"  [WARNING] {alignment_stats['only_java']} rows only in Java")
        if alignment_stats['only_python'] > 0:
            print(f"  [WARNING] {alignment_stats['only_python']} rows only in Python")
        
        # Compare
        print("\n[STEP 4] Comparing aligned dataframes...")
        mismatches, comparison_stats = compare_dataframes(java_aligned, python_aligned, key_cols)
        
        # Report
        print_mismatches(mismatches, key_cols, max_display=args.show_mismatches)
        print_summary(alignment_stats, comparison_stats, key_cols, mismatches)
        
        # Return appropriate exit code
        if mismatches:
            return 1
        return 0
    
    except FileNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
