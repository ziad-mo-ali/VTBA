# validate.py - Output Comparison Tool

Compares Java and Python bug assignment outputs to validate the Python migration.

## Quick Start

```bash
python validate.py \
  --java-output ./Exp/Out/outDetails/experiment_folder/output.tsv \
  --python-output ./python_output.tsv
```

## Arguments

- `--java-output` (required): Path to the existing Java output TSV file
- `--python-output` (required): Path to the Python output TSV file
- `--show-mismatches` (optional): Number of mismatches to display in detail (default: 20)

## Output

The script produces:

1. **File Loading**: Confirms both files loaded successfully with column names
2. **Natural Key Detection**: Identifies the composite key (project, bugNumber, assignmentDate)
3. **Alignment Report**: Shows which rows exist in both files vs. only in one
4. **Detailed Mismatches**: Lists field-by-field differences for each mismatched row
5. **Summary Statistics**:
   - Alignment statistics (rows matched, alignment rate %)
   - Comparison statistics (total comparisons, match rate %)
   - Columns with mismatches
   - Row-level mismatch rate

## Exit Codes

- **0**: All rows match perfectly (no mismatches)
- **1**: Mismatches found

## Example Usage

### Compare single experiment output
```bash
python validate.py \
  --java-output "./Exp/Out/outDetails/1- (bTDmL - ...)/output_T5_ALL_TYPES.tsv" \
  --python-output "./python_results/T5_ALL_TYPES.tsv"
```

### Show more detailed mismatch information
```bash
python validate.py \
  --java-output ./java_output.tsv \
  --python-output ./python_output.tsv \
  --show-mismatches 50
```

## Supported Natural Keys

The script automatically detects natural keys in this priority order:

1. `(project, bugNumber, assignmentDate)`
2. `(projectId, bugNumber, assignmentDate)`
3. `(project, bugNumber)`
4. `(projectId, bugNumber)`

If none of these are found, it fails with an error listing available columns.

## Output Format

Both Java and Python TSV files must be tab-separated with matching columns for:
- Project identifier (project or projectId)
- Bug number/ID
- Assignment date (if available)
- Prediction fields (assignee, rank, scores, etc.)

## Example Output

```
====================================================================================================
VALIDATION SUMMARY
====================================================================================================

ALIGNMENT STATISTICS:
  Java output total rows:           1000
  Python output total rows:         1000
  Aligned common rows:              1000
  Only in Java:                        0
  Only in Python:                      0
  Alignment rate:                100.00%

COMPARISON STATISTICS:
  Natural key columns:       project, bugNumber, assignmentDate
  Total field comparisons:          8000
  Perfect matches:                  8000
  Mismatches:                          0
  Match rate:                    100.00%

COLUMNS WITH MISMATCHES:
  (none)

ROW-LEVEL STATISTICS:
  Rows with differences:              0
  Rows compared:                   1000
  Mismatch row rate:               0.00%

[SUCCESS] All rows match perfectly!
```

## Common Issues

### FileNotFoundError
Verify both file paths are absolute or relative to current working directory.

### "Could not identify a suitable natural key"
The files may be missing expected columns. Run again to see available columns.

### Alignment mismatches
If "Only in Java" or "Only in Python" is non-zero, the datasets have different rows by the natural key.
This may indicate a difference in input data or filtering between implementations.

## Dependencies

- pandas >= 2.0.0
