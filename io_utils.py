from __future__ import annotations

import csv
import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Union

import pandas as pd

from constants import ConditionType, FieldType, LogicalOperation, SortOrder


@dataclass
class FileManipulationResult:
    errors: int = 0
    processed: int = 0
    done_successfully: int = 0

    def add(self, other: FileManipulationResult) -> None:
        self.errors += other.errors
        self.processed += other.processed
        self.done_successfully += other.done_successfully


def indent(indentation_level: int) -> str:
    return " " * (4 * indentation_level)


def println(message: str, indentation_level: int = 0) -> None:
    print(f"{indent(indentation_level)}{message}")


def compare_two_strings_based_on_condition_type(
    value_a: str,
    condition_type: ConditionType,
    value_b: str,
    field_type: FieldType,
) -> bool:
    if condition_type == ConditionType.EQUALS:
        return value_a == value_b
    if condition_type == ConditionType.NOT_EQUALS:
        return value_a != value_b
    if condition_type == ConditionType.GREATER_OR_EQUAL:
        if field_type == FieldType.LONG:
            if value_a in {"", " "}:
                value_a = str(-9223372036854775808)
            return int(value_a) >= int(value_b)
        if field_type == FieldType.STRING:
            return value_a >= value_b
        println("Warning: GREATER_OR_EQUAL on NOT_IMPORTANT field type", 0)
        return True
    return False


def run_logical_comparison(
    logical_operation: LogicalOperation,
    value1a: str,
    condition1_type: ConditionType,
    value1b: str,
    field1_type: FieldType,
    value2a: str,
    condition2_type: ConditionType,
    value2b: str,
    field2_type: FieldType,
) -> bool:
    if logical_operation == LogicalOperation.NO_CONDITION:
        return True

    result_of_condition1 = compare_two_strings_based_on_condition_type(
        value1a, condition1_type, value1b, field1_type
    )
    if result_of_condition1:
        if logical_operation == LogicalOperation.AND:
            return compare_two_strings_based_on_condition_type(
                value2a, condition2_type, value2b, field2_type
            )
        return True
    if logical_operation == LogicalOperation.OR:
        return compare_two_strings_based_on_condition_type(
            value2a, condition2_type, value2b, field2_type
        )
    return False


def add_file_manipulation_results(
    first: FileManipulationResult, second: FileManipulationResult
) -> FileManipulationResult:
    result = FileManipulationResult()
    result.done_successfully = first.done_successfully + second.done_successfully
    result.processed = first.processed + second.processed
    result.errors = first.errors + second.errors
    return result


def concat_two_string_arrays(array1: List[str], array2: List[str]) -> List[str]:
    return array1 + array2


def delete_temporary_files(
    path: Union[str, Path],
    temporary_files_to_be_deleted: Iterable[str],
    show_error_message_if_a_file_does_not_exist: bool,
    indentation_level: int,
    write_message_step: str,
) -> FileManipulationResult:
    path = Path(path)
    result = FileManipulationResult()
    deleted = 0
    println(f"{write_message_step}- Deleting the temporary files ...", indentation_level)
    for filename in temporary_files_to_be_deleted:
        file_path = path / filename
        if file_path.exists():
            file_path.unlink()
            deleted += 1
        else:
            result.errors += 1
            if show_error_message_if_a_file_does_not_exist:
                println(f"Error: Cannot find file \"{filename}\" to delete it!", indentation_level)
    println(
        f"{indent(indentation_level+1)}Number of temporary files deleted: {deleted} / {len(list(temporary_files_to_be_deleted))}",
        0,
    )
    result.done_successfully = 1 if deleted == len(list(temporary_files_to_be_deleted)) else 0
    result.processed = len(list(temporary_files_to_be_deleted))
    return result


def copy_file(
    input_path: Union[str, Path],
    input_file_name: str,
    output_path: Union[str, Path],
    output_file_name: str,
    indentation_level: int,
    write_message_step: str,
) -> FileManipulationResult:
    source = Path(input_path) / input_file_name
    destination = Path(output_path) / output_file_name
    result = FileManipulationResult()
    println(f"{write_message_step}- Copying file \"{input_file_name}\" to \"{output_file_name}\"", indentation_level)
    try:
        shutil.copy2(source, destination)
        result.done_successfully = 1
        println("Copied successfully.", indentation_level + 1)
    except Exception as exc:
        result.errors = 1
        println(
            f"Error copying file from {source} to {destination}: {type(exc).__name__}: {exc}",
            indentation_level,
        )
    result.processed = 1
    return result


def rename_file(
    input_path: Union[str, Path],
    input_file_name: str,
    output_path: Union[str, Path],
    output_file_name: str,
    indentation_level: int,
    write_message_step: str,
) -> FileManipulationResult:
    source = Path(input_path) / input_file_name
    destination = Path(output_path) / output_file_name
    result = FileManipulationResult()
    println(f"{write_message_step}- Renaming file \"{input_file_name}\" to \"{output_file_name}\"", indentation_level)
    try:
        source.rename(destination)
        result.done_successfully = 1
    except Exception as exc:
        result.errors = 1
        println(
            f"Error renaming file from {source} to {destination}: {type(exc).__name__}: {exc}",
            indentation_level,
        )
    result.processed = 1
    return result


def create_folder_if_does_not_exist(
    path_and_folder_name: Union[str, Path],
    fmr: FileManipulationResult,
    indentation_level: int,
    write_message_step: str,
) -> None:
    path = Path(path_and_folder_name)
    if not path.exists():
        println(
            concat_two_write_message_steps(write_message_step, f"Creating directory \"{path_and_folder_name}\" if it does not exist ...."),
            indentation_level,
        )
        try:
            path.mkdir(parents=True, exist_ok=True)
            println("Folder created.", indentation_level + 1)
            fmr.done_successfully = 1
        except Exception as exc:
            fmr.errors += 1
            println(
                f"Error creating directory {path}: {type(exc).__name__}: {exc}",
                indentation_level + 1,
            )
    else:
        println("Folder currently exists. No need to re-create it.", indentation_level + 1)


def convert_array_list_of_string_to_delimiter_separated_string(values: List[str]) -> str:
    return "\t".join(values)


def concat_two_write_message_steps(prefix1: str, prefix2: str) -> str:
    if not prefix1:
        return prefix2
    if not prefix2:
        return prefix1
    return f"{prefix1}-{prefix2}"


def special_binary_search(a: List[int], key: int) -> int:
    lo = 0
    hi = len(a) - 1
    mid = 0
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        if key < a[mid]:
            hi = mid - 1
        elif key > a[mid]:
            lo = mid + 1
        else:
            return mid
    return mid - 1


def special_binary_search2(assignments: List[List[str]], index_of_date_field: int, key: str) -> int:
    lo = 0
    hi = len(assignments) - 1
    mid = 0
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        cmp = (key > assignments[mid][index_of_date_field]) - (key < assignments[mid][index_of_date_field])
        if cmp < 0:
            hi = mid - 1
        elif cmp > 0:
            lo = mid + 1
        else:
            return mid
    return mid - 1


def get_difference_in_days(d1: datetime, d2: datetime) -> int:
    return abs((d2 - d1).days)


def parse_iso_datetime(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")


def apply_regex_on_string(regex: str, value: str) -> str:
    import re

    cleaned = re.sub(f"[^{regex}]+", " ", value)
    return cleaned if cleaned else " "


def remove_extra_characters_from_the_end_of_record(tab_separated_record: str) -> str:
    if tab_separated_record.endswith(")\t"):
        return tab_separated_record[:-2]
    if tab_separated_record.endswith(");\t"):
        return tab_separated_record[:-3]
    return tab_separated_record


def remove_from_end(value: str, num: int) -> str:
    return value[:-num]


def _read_tsv_dataframe(
    input_path: Union[str, Path],
    input_file_name: str,
    test_or_real: int,
) -> pd.DataFrame:
    path = Path(input_path) / input_file_name
    
    # Try UTF-8 first, fall back to latin-1 if that fails
    try:
        df = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False, na_filter=False, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False, na_filter=False, encoding='latin-1')
    
    if test_or_real > -1:
        df = df.iloc[: int(test_or_real)]
    return df


def _select_fields(fields: List[str], field_numbers_string: str) -> List[str]:
    if field_numbers_string == "ALL":
        return fields
    indices = [int(x) for x in field_numbers_string.split("$") if x != ""]
    return [fields[i] for i in indices]


def _sort_dict_by_key(
    data: Dict[str, Any], sort_order: SortOrder, combined_key: bool = False
) -> Dict[str, Any]:
    if sort_order == SortOrder.DEFAULT_FOR_STRING:
        return {k: data[k] for k in sorted(data)}

    def parse_key(key: str) -> Tuple[int, ...]:
        if combined_key:
            parts = key.split("\t")
            return tuple(int(part) for part in parts)
        return (int(key),)

    reverse = sort_order != SortOrder.ASCENDING_INTEGER
    try:
        sorted_keys = sorted(data, key=parse_key, reverse=reverse)
    except ValueError:
        sorted_keys = sorted(data, reverse=reverse)
    return {k: data[k] for k in sorted_keys}


def read_unique_key_and_its_value_from_tsv(
    input_path: str,
    input_file_name: str,
    key_set_to_check_existence_of_key_field: Optional[Set[str]],
    key_field_number: int,
    total_fields_count: int,
    field_numbers_to_be_read_separated_by_dollar: str,
    logical_operation: LogicalOperation,
    field1_number: int,
    condition1_type: ConditionType,
    field1_value: str,
    field1_type: FieldType,
    field2_number: int,
    condition2_type: ConditionType,
    field2_value: str,
    field2_type: FieldType,
    wrap_output_in_lines: bool,
    show_progress_interval: int,
    indentation_level: int,
    test_or_real: int,
    write_message_step: str,
) -> Dict[str, List[str]]:
    if wrap_output_in_lines:
        println("-----------------------------------", indentation_level)
    df = _read_tsv_dataframe(input_path, input_file_name, test_or_real)
    result: Dict[str, List[str]] = {}
    if wrap_output_in_lines:
        println(f"{write_message_step}- Parsing {input_file_name}:", indentation_level)
        println("Started ...", indentation_level + 1)

    error1 = 0
    error2 = 0
    unmatched_records = 0
    matched_rec = 0
    
    # Convert show_progress_interval to int to avoid type issues
    show_progress_interval = int(show_progress_interval) if show_progress_interval else 0

    for row_idx, row in enumerate(df.values):
        fields = row.tolist()
        if len(fields) != total_fields_count:
            error1 += 1
            continue
        record_should_be_read = run_logical_comparison(
            logical_operation,
            fields[field1_number],
            condition1_type,
            field1_value,
            field1_type,
            fields[field2_number],
            condition2_type,
            field2_value,
            field2_type,
        )
        if not record_should_be_read:
            unmatched_records += 1
            continue
        key_field = fields[key_field_number]
        if key_set_to_check_existence_of_key_field is not None and key_field not in key_set_to_check_existence_of_key_field:
            continue
        matched_rec += 1
        if key_field in result:
            error2 += 1
            continue
        result[key_field] = _select_fields(fields, field_numbers_to_be_read_separated_by_dollar)
        if show_progress_interval and ((row_idx + 1) % show_progress_interval == 0):
            println(f"{indent(indentation_level+1)}{row_idx+1}", 0)

    if error1 > 0:
        println(
            f"{indent(indentation_level+1)}Error) Number of records with != {total_fields_count} fields: {error1}",
            0,
        )
    if error2 > 0:
        println(
            f"{indent(indentation_level+1)}Error) Number of records with repeated keyField: {error2}",
            0,
        )
    if logical_operation == LogicalOperation.NO_CONDITION:
        println(f"{indent(indentation_level+1)}Number of records read: {matched_rec}", 0)
    else:
        println(
            f"{indent(indentation_level+1)}Number of records read (matched with the provided conditions): {matched_rec}",
            0,
        )
        if unmatched_records == 0:
            println(f"{indent(indentation_level+1)}:-) No unmatched records with the conditions provided.", 0)
        else:
            println(
                f"{indent(indentation_level+1)}Number of ignored records (unmatched with the provided conditions): {unmatched_records}",
                0,
            )
    println(f"{indent(indentation_level+1)}Finished.", 0)
    if wrap_output_in_lines:
        println("-----------------------------------", indentation_level)
    return result


def read_unique_combined_key_and_its_value_from_tsv(
    input_path: str,
    input_file_name: str,
    fmr: FileManipulationResult,
    key_set_to_check_existence_of_key_field: Optional[Set[str]],
    key_field_numbers_separated_by_dollar: str,
    total_fields_count: int,
    field_numbers_to_be_read_separated_by_dollar: str,
    logical_operation: LogicalOperation,
    field1_number: int,
    condition1_type: ConditionType,
    field1_value: str,
    field1_type: FieldType,
    field2_number: int,
    condition2_type: ConditionType,
    field2_value: str,
    field2_type: FieldType,
    wrap_output_in_lines: bool,
    show_progress_interval: int,
    indentation_level: int,
    test_or_real: int,
    write_message_step: str,
) -> Dict[str, List[str]]:
    if wrap_output_in_lines:
        println("-----------------------------------", indentation_level)
    df = _read_tsv_dataframe(input_path, input_file_name, test_or_real)
    result: Dict[str, List[str]] = {}
    if wrap_output_in_lines:
        println(f"{write_message_step}- Parsing {input_file_name}:", indentation_level)
        println("Started ...", indentation_level + 1)

    error1 = 0
    error2 = 0
    unmatched_records = 0
    matched_rec = 0
    key_field_numbers = [int(x) for x in key_field_numbers_separated_by_dollar.split("$") if x != ""]
    key1_index, key2_index = key_field_numbers
    
    # Convert show_progress_interval to int to avoid type issues
    show_progress_interval = int(show_progress_interval) if show_progress_interval else 0

    for row_idx, row in enumerate(df.values):
        fields = row.tolist()
        if len(fields) != total_fields_count:
            error1 += 1
            continue
        record_should_be_read = run_logical_comparison(
            logical_operation,
            fields[field1_number],
            condition1_type,
            field1_value,
            field1_type,
            fields[field2_number],
            condition2_type,
            field2_value,
            field2_type,
        )
        if not record_should_be_read:
            unmatched_records += 1
            continue
        key_field = f"{fields[key1_index]}\t{fields[key2_index]}"
        if key_set_to_check_existence_of_key_field is not None and key_field not in key_set_to_check_existence_of_key_field:
            continue
        matched_rec += 1
        if key_field in result:
            error2 += 1
            continue
        result[key_field] = _select_fields(fields, field_numbers_to_be_read_separated_by_dollar)
        if show_progress_interval and ((row_idx + 1) % show_progress_interval == 0):
            println(f"{indent(indentation_level+1)}{row_idx+1}", 0)

    if error1 > 0:
        println(
            f"Error) Number of records with != {total_fields_count} fields: {error1}",
            indentation_level + 1,
        )
        fmr.errors = 1
    if error2 > 0:
        println(
            f"Error) Number of records with repeated keyField: {error2}",
            indentation_level + 1,
        )
        fmr.errors = 1
    if logical_operation == LogicalOperation.NO_CONDITION:
        println(f"{matched_rec} records have been read.", indentation_level + 1)
    else:
        println(
            f"{matched_rec} records have been read (matched with the provided conditions).",
            indentation_level + 1,
        )
        if unmatched_records == 0:
            println(":-) No unmatched records with the conditions provided.", indentation_level + 1)
        else:
            println(
                f"Number of ignored records (unmatched with the provided conditions): {unmatched_records}",
                indentation_level + 1,
            )
    println("Finished.", indentation_level + 1)
    if wrap_output_in_lines:
        println("-----------------------------------", indentation_level)
    return result


def read_non_unique_field_from_tsv_only_repeat_each_entry_once(
    input_path: str,
    input_file_name: str,
    key_field_number: int,
    total_fields_count: int,
    logical_operation: LogicalOperation,
    field1_number: int,
    condition1_type: ConditionType,
    field1_value: str,
    field1_type: FieldType,
    field2_number: int,
    condition2_type: ConditionType,
    field2_value: str,
    field2_type: FieldType,
    wrap_output_in_lines: bool,
    indentation_level: int,
    show_progress_interval: int,
    test_or_real: int,
    write_message_step: Union[str, int],
) -> Set[str]:
    if wrap_output_in_lines:
        println("-----------------------------------", indentation_level)
    df = _read_tsv_dataframe(input_path, input_file_name, test_or_real)
    result: Set[str] = set()
    if wrap_output_in_lines:
        println(f"{write_message_step}{indent(indentation_level)}- Parsing {input_file_name}:", 0)
        println("Started ...", indentation_level)

    error1 = 0
    unmatched_records = 0
    matched_rec = 0
    
    # Convert show_progress_interval to int to avoid type issues
    show_progress_interval = int(show_progress_interval) if show_progress_interval else 0

    for row_idx, row in enumerate(df.values):
        fields = row.tolist()
        if len(fields) != total_fields_count:
            error1 += 1
            continue
        record_should_be_read = run_logical_comparison(
            logical_operation,
            fields[field1_number],
            condition1_type,
            field1_value,
            field1_type,
            fields[field2_number],
            condition2_type,
            field2_value,
            field2_type,
        )
        if not record_should_be_read:
            unmatched_records += 1
            continue
        key_field = fields[key_field_number]
        if key_field not in result:
            result.add(key_field)
        matched_rec += 1
        if show_progress_interval and ((row_idx + 1) % show_progress_interval == 0):
            println(f"{indent(indentation_level)}{row_idx+1}", 0)

    if error1 > 0:
        println(
            f"{indent(indentation_level)}Error) Number of records with != {total_fields_count} fields: {error1}",
            0,
        )
    if logical_operation == LogicalOperation.NO_CONDITION:
        println(f"{indent(indentation_level)}Number of records read: {matched_rec}", 0)
    else:
        println(
            f"{indent(indentation_level)}Number of records read (matched with the provided conditions): {matched_rec}",
            0,
        )
        if unmatched_records == 0:
            println(f"{indent(indentation_level)}:-) No unmatched records with the conditions provided.", 0)
        else:
            println(
                f"{indent(indentation_level)}Number of ignored records (unmatched with the provided conditions): {unmatched_records}",
                0,
            )
    println("Finished.", indentation_level)
    if wrap_output_in_lines:
        println("-----------------------------------", indentation_level)
    return result


def read_unique_field_from_tsv(
    input_path: str,
    input_file_name: str,
    key_field_number: int,
    total_fields_count: int,
    logical_operation: LogicalOperation,
    field1_number: int,
    condition1_type: ConditionType,
    field1_value: str,
    field1_type: FieldType,
    field2_number: int,
    condition2_type: ConditionType,
    field2_value: str,
    field2_type: FieldType,
    wrap_output_in_lines: bool,
    indentation_level: int,
    show_progress_interval: int,
    test_or_real: int,
    write_message_step: str,
) -> Set[str]:
    if wrap_output_in_lines:
        println("-----------------------------------", indentation_level)
    df = _read_tsv_dataframe(input_path, input_file_name, test_or_real)
    result: Set[str] = set()
    if wrap_output_in_lines:
        println(f"{write_message_step}- Parsing {input_file_name}:", indentation_level)
        println("Started ...", indentation_level + 1)

    error1 = 0
    error2 = 0
    unmatched_records = 0
    matched_rec = 0
    
    # Convert show_progress_interval to int to avoid type issues
    show_progress_interval = int(show_progress_interval) if show_progress_interval else 0

    for row_idx, row in enumerate(df.values):
        fields = row.tolist()
        if len(fields) != total_fields_count:
            error1 += 1
            continue
        record_should_be_read = run_logical_comparison(
            logical_operation,
            fields[field1_number],
            condition1_type,
            field1_value,
            field1_type,
            fields[field2_number],
            condition2_type,
            field2_value,
            field2_type,
        )
        if not record_should_be_read:
            unmatched_records += 1
            continue
        key_field = fields[key_field_number]
        if key_field in result:
            error2 += 1
        else:
            result.add(key_field)
        matched_rec += 1
        if show_progress_interval and ((row_idx + 1) % show_progress_interval == 0):
            println(f"{indent(indentation_level)}{row_idx+1}", 0)

    if error1 > 0:
        println(
            f"{indent(indentation_level+1)}Error) Number of records with != {total_fields_count} fields: {error1}",
            0,
        )
    if error2 > 0:
        println(
            f"{indent(indentation_level+1)}Error) Number of records with duplicate keyfield: {error2}",
            0,
        )
    if logical_operation == LogicalOperation.NO_CONDITION:
        println(f"{indent(indentation_level+1)}Number of records read: {matched_rec}", 0)
    else:
        println(
            f"{indent(indentation_level+1)}Number of records read (matched with the provided conditions): {matched_rec}",
            0,
        )
        if unmatched_records == 0:
            println(f"{indent(indentation_level+1)}:-) No unmatched records with the conditions provided.", 0)
        else:
            println(
                f"{indent(indentation_level+1)}Number of ignored records (unmatched with the provided conditions): {unmatched_records}",
                0,
            )
    println("Finished.", indentation_level)
    if wrap_output_in_lines:
        println("-----------------------------------", indentation_level)
    return result


def _filter_df_by_conditions(
    df: pd.DataFrame,
    logical_operation: LogicalOperation,
    field1_number: int,
    condition1_type: ConditionType,
    field1_value: str,
    field1_type: FieldType,
    field2_number: int,
    condition2_type: ConditionType,
    field2_value: str,
    field2_type: FieldType,
) -> pd.DataFrame:
    if logical_operation == LogicalOperation.NO_CONDITION:
        return df
    mask = []
    for _, row in df.iterrows():
        if run_logical_comparison(
            logical_operation,
            row.iloc[field1_number],
            condition1_type,
            field1_value,
            field1_type,
            row.iloc[field2_number],
            condition2_type,
            field2_value,
            field2_type,
        ):
            mask.append(True)
        else:
            mask.append(False)
    return df[pd.Series(mask)]


def merge_two_tsv_fields_together(
    input_path: str,
    input_file_name: str,
    output_path_and_file_name: str,
    field1_number: int,
    field2_number: int,
    delimiter: str,
    total_fields_number: int,
    wrap_output_in_lines: bool,
    indentation_level: int,
    show_progress_interval: int,
    test_or_real: int,
    write_message_step: str,
) -> None:
    if wrap_output_in_lines:
        println("-----------------------------------", indentation_level)
    df = _read_tsv_dataframe(input_path, input_file_name, test_or_real)
    output_file = Path(output_path_and_file_name)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    merged_rows = []
    for _, row in df.iterrows():
        fields = row.tolist()
        if len(fields) != total_fields_number:
            continue
        fields[field1_number] = f"{fields[field1_number]}{delimiter}{fields[field2_number]}"
        merged_rows.append([f for j, f in enumerate(fields) if j != field2_number])
    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerows(merged_rows)
    if wrap_output_in_lines:
        println("-----------------------------------", indentation_level)


def read_non_unique_key_and_its_value_from_tsv(
    input_path: str,
    input_file_name: str,
    fmr: FileManipulationResult,
    key_set_to_check_existence_of_key_field: Optional[Set[str]],
    key_field_number: int,
    sort_order: SortOrder,
    total_fields_count: int,
    field_numbers_to_be_read_separated_by_dollar: str,
    titles_to_return: List[str],
    logical_operation: LogicalOperation,
    field1_number: int,
    condition1_type: ConditionType,
    field1_value: str,
    field1_type: FieldType,
    field2_number: int,
    condition2_type: ConditionType,
    field2_value: str,
    field2_type: FieldType,
    wrap_output_in_lines: bool,
    show_progress_interval: int,
    indentation_level: int,
    test_or_real: int,
    write_message_step: str,
) -> Dict[str, List[List[str]]]:
    if wrap_output_in_lines:
        println("-----------------------------------", indentation_level)
    
    try:
        df = _read_tsv_dataframe(input_path, input_file_name, test_or_real)
    except FileNotFoundError as e:
        fmr.errors = 1
        println(
            f"Error) File not found: {input_path}/{input_file_name} - {e}",
            indentation_level + 1,
        )
        return {}
    except Exception as e:
        fmr.errors = 1
        println(
            f"Error) Failed to read {input_file_name}: {type(e).__name__}: {e}",
            indentation_level + 1,
        )
        return {}
    
    result: Dict[str, List[List[str]]] = {}
    if wrap_output_in_lines:
        println(f"{indent(indentation_level)}{write_message_step}- Parsing {input_file_name}:", 0)
        println("Started ...", indentation_level + 1)

    if len(df.columns) < total_fields_count:
        fmr.errors = 1
        println(
            f"Error) Expected {total_fields_count} fields but got {len(df.columns)} in {input_file_name}",
            indentation_level + 1,
        )
        return result

    titles = df.columns.tolist()
    needed_indices = [int(x) for x in field_numbers_to_be_read_separated_by_dollar.split("$") if x != ""]
    for idx in needed_indices:
        titles_to_return.append(titles[idx])

    error = 0
    unmatched_records = 0
    equal_objects_found = 0
    matched_rec = 0
    
    # Convert show_progress_interval to int to avoid type issues
    show_progress_interval = int(show_progress_interval) if show_progress_interval else 0

    for row_idx, row in enumerate(df.values):
        fields = row.tolist()
        if len(fields) != total_fields_count:
            error += 1
            continue
        if not run_logical_comparison(
            logical_operation,
            fields[field1_number],
            condition1_type,
            field1_value,
            field1_type,
            fields[field2_number],
            condition2_type,
            field2_value,
            field2_type,
        ):
            unmatched_records += 1
            continue
        key_field = fields[key_field_number]
        if key_set_to_check_existence_of_key_field is not None and key_field not in key_set_to_check_existence_of_key_field:
            continue
        subset = _select_fields(fields, field_numbers_to_be_read_separated_by_dollar)
        if key_field not in result:
            result[key_field] = [subset]
        else:
            if subset not in result[key_field]:
                result[key_field].append(subset)
            else:
                equal_objects_found += 1
        matched_rec += 1
        if show_progress_interval and ((row_idx + 1) % show_progress_interval == 0):
            println(f"{indent(indentation_level+1)}{row_idx+1}", 0)

    if error > 0:
        println(f"Error) Number of records with != {total_fields_count} fields: {error}", indentation_level + 1)
    if equal_objects_found > 0:
        println(f"Hint) Number of repeated TSV records (ignored): {equal_objects_found}", indentation_level + 1)
    if logical_operation == LogicalOperation.NO_CONDITION:
        println(f"{matched_rec} records have been read.", indentation_level + 1)
    else:
        println(f"{matched_rec} records have been read (matched with the provided conditions).", indentation_level + 1)
        if unmatched_records == 0:
            println(":-) No unmatched records with the conditions provided.", indentation_level + 1)
        else:
            println(
                f"Number of ignored records (unmatched with the provided conditions): {unmatched_records}",
                indentation_level + 1,
            )
    fmr.errors = 0
    fmr.done_successfully = 1
    fmr.processed = 1
    if wrap_output_in_lines:
        println("-----------------------------------", indentation_level)
    return _sort_dict_by_key(result, sort_order)


def read_non_unique_key_and_its_value_as_treeset_from_tsv(
    input_path: str,
    input_file_name: str,
    fmr: FileManipulationResult,
    key_set_to_check_existence_of_key_field: Optional[Set[str]],
    key_field_number: int,
    sort_order: SortOrder,
    total_fields_count: int,
    value_field_number: int,
    logical_operation: LogicalOperation,
    field1_number: int,
    condition1_type: ConditionType,
    field1_value: str,
    field1_type: FieldType,
    field2_number: int,
    condition2_type: ConditionType,
    field2_value: str,
    field2_type: FieldType,
    wrap_output_in_lines: bool,
    show_progress_interval: int,
    indentation_level: int,
    test_or_real: int,
    write_message_step: str,
) -> Dict[str, Set[str]]:
    if wrap_output_in_lines:
        println("-----------------------------------", indentation_level)
    df = _read_tsv_dataframe(input_path, input_file_name, test_or_real)
    result: Dict[str, Set[str]] = {}
    if wrap_output_in_lines:
        println(f"{indent(indentation_level)}{write_message_step}- Parsing {input_file_name}:", 0)
        println("Started ...", indentation_level + 1)

    error = 0
    unmatched_records = 0
    equal_objects_found = 0
    matched_rec = 0
    number_of_key_values_read = 0
    
    # Convert show_progress_interval to int to avoid type issues
    show_progress_interval = int(show_progress_interval) if show_progress_interval else 0

    for row_idx, row in enumerate(df.values):
        fields = row.tolist()
        if len(fields) != total_fields_count:
            error += 1
            continue
        if not run_logical_comparison(
            logical_operation,
            fields[field1_number],
            condition1_type,
            field1_value,
            field1_type,
            fields[field2_number],
            condition2_type,
            field2_value,
            field2_type,
        ):
            unmatched_records += 1
            continue
        key_field = fields[key_field_number]
        value_field = fields[value_field_number]
        if value_field == " ":
            continue
        if key_set_to_check_existence_of_key_field is not None and key_field not in key_set_to_check_existence_of_key_field:
            continue
        if key_field not in result:
            result[key_field] = {value_field}
            number_of_key_values_read += 1
        else:
            if value_field in result[key_field]:
                equal_objects_found += 1
            else:
                result[key_field].add(value_field)
                number_of_key_values_read += 1
        matched_rec += 1
        if show_progress_interval and ((row_idx + 1) % show_progress_interval == 0):
            println(f"{indent(indentation_level+1)}{row_idx+1}", 0)

    if error > 0:
        println(f"Error) Number of records with != {total_fields_count} fields: {error}", indentation_level + 1)
    if equal_objects_found > 0:
        println(
            f"Hint) Number of repeated key-values in the TSV records (ignored): {equal_objects_found}",
            indentation_level + 1,
        )
    if logical_operation == LogicalOperation.NO_CONDITION:
        println(f"{indentation_level+1}Number of records read: {matched_rec}", 0)
    else:
        println(
            f"{indentation_level+1}Number of records read (matched with the provided conditions): {matched_rec}",
            0,
        )
        if unmatched_records == 0:
            println(":-) No unmatched records with the conditions provided.", indentation_level + 1)
        else:
            println(
                f"Number of ignored records (unmatched with the provided conditions): {unmatched_records}",
                indentation_level + 1,
            )
    fmr.errors = 0
    fmr.done_successfully = 1
    fmr.processed = 1
    if wrap_output_in_lines:
        println("-----------------------------------", indentation_level)
    return _sort_dict_by_key(result, sort_order)


def read_non_unique_combined_key_and_its_value_from_tsv(
    input_path: str,
    input_file_name: str,
    fmr: FileManipulationResult,
    key_set_to_check_existence_of_key_field: Optional[Set[str]],
    key_field_numbers_separated_by_dollar: str,
    sort_order: SortOrder,
    total_fields_count: int,
    field_numbers_to_be_read_separated_by_dollar: str,
    logical_operation: LogicalOperation,
    field1_number: int,
    condition1_type: ConditionType,
    field1_value: str,
    field1_type: FieldType,
    field2_number: int,
    condition2_type: ConditionType,
    field2_value: str,
    field2_type: FieldType,
    wrap_output_in_lines: bool,
    show_progress_interval: int,
    indentation_level: int,
    test_or_real: int,
    write_message_step: str,
) -> Dict[str, List[List[str]]]:
    if wrap_output_in_lines:
        println("-----------------------------------", indentation_level)
    df = _read_tsv_dataframe(input_path, input_file_name, test_or_real)
    result: Dict[str, List[List[str]]] = {}
    if wrap_output_in_lines:
        println(f"{indent(indentation_level)}{write_message_step}- Parsing {input_file_name}:", 0)
        println("Started ...", indentation_level + 1)

    key_indexes = [int(x) for x in key_field_numbers_separated_by_dollar.split("$") if x != ""]
    key1_index, key2_index = key_indexes
    error = 0
    unmatched_records = 0
    equal_objects_found = 0
    matched_rec = 0
    
    # Convert show_progress_interval to int to avoid type issues
    show_progress_interval = int(show_progress_interval) if show_progress_interval else 0

    for row_idx, row in enumerate(df.values):
        fields = row.tolist()
        if len(fields) != total_fields_count:
            error += 1
            continue
        if not run_logical_comparison(
            logical_operation,
            fields[field1_number],
            condition1_type,
            field1_value,
            field1_type,
            fields[field2_number],
            condition2_type,
            field2_value,
            field2_type,
        ):
            unmatched_records += 1
            continue
        key_field = f"{fields[key1_index]}\t{fields[key2_index]}"
        if key_set_to_check_existence_of_key_field is not None and key_field not in key_set_to_check_existence_of_key_field:
            continue
        subset = _select_fields(fields, field_numbers_to_be_read_separated_by_dollar)
        if key_field not in result:
            result[key_field] = [subset]
        else:
            if subset not in result[key_field]:
                result[key_field].append(subset)
            else:
                equal_objects_found += 1
        matched_rec += 1
        if show_progress_interval and ((row_idx + 1) % show_progress_interval == 0):
            println(f"{indent(indentation_level+1)}{row_idx+1}", 0)

    if error > 0:
        println(f"Error) Number of records with != {total_fields_count} fields: {error}", indentation_level + 1)
    if equal_objects_found > 0:
        println(f"Hint) Number of repeated TSV records (ignored): {equal_objects_found}", indentation_level + 1)
    if logical_operation == LogicalOperation.NO_CONDITION:
        println(f"{matched_rec} records have been read.", indentation_level + 1)
    else:
        println(f"{matched_rec} records have been read (matched with the provided conditions).", indentation_level + 1)
        if unmatched_records == 0:
            println(":-) No unmatched records with the conditions provided.", indentation_level + 1)
        else:
            println(
                f"Number of ignored records (unmatched with the provided conditions): {unmatched_records}",
                indentation_level + 1,
            )
    fmr.errors = 0
    fmr.done_successfully = 1
    fmr.processed = 1
    if wrap_output_in_lines:
        println("-----------------------------------", indentation_level)
    return _sort_dict_by_key(result, sort_order, combined_key=True)


def save_key_and_long_values_as_tsv_file(
    output_path: str,
    output_file_name: str,
    counts: Dict[str, int],
    titles: List[str],
    wrap_output_in_lines: bool,
    show_progress_interval: int,
    indentation_level: int,
    test_or_real: int,
    write_message_step: str,
) -> FileManipulationResult:
    return _save_dict_to_tsv(output_path, output_file_name, counts, titles, wrap_output_in_lines, show_progress_interval, indentation_level, write_message_step)


def save_key_and_double_values_as_tsv_file(
    output_path: str,
    output_file_name: str,
    counts: Dict[str, float],
    titles: List[str],
    wrap_output_in_lines: bool,
    show_progress_interval: int,
    indentation_level: int,
    test_or_real: int,
    write_message_step: str,
) -> FileManipulationResult:
    return _save_dict_to_tsv(output_path, output_file_name, counts, titles, wrap_output_in_lines, show_progress_interval, indentation_level, write_message_step)


def save_tree_map_to_tsv_file(
    output_path: str,
    output_file_name: str,
    data: Dict[str, List[List[str]]],
    titles: str,
    also_save_the_key: bool,
    index_for_key_field_to_save: int,
    wrap_output_in_lines: bool,
    show_progress_interval: int,
    indentation_level: int,
    test_or_real: int,
    write_message_step: str,
) -> FileManipulationResult:
    if wrap_output_in_lines:
        println("-----------------------------------", indentation_level)
    result = FileManipulationResult()
    try:
        path = Path(output_path)
        path.mkdir(parents=True, exist_ok=True)
        with (path / output_file_name).open("w", newline="", encoding="utf-8") as f:
            f.write(titles + "\n")
            written = 0
            for key, rows in data.items():
                for row in rows:
                    a_line = []
                    for k in range(index_for_key_field_to_save):
                        a_line.append(row[k])
                    if also_save_the_key:
                        a_line.append(key)
                    a_line.extend(row[index_for_key_field_to_save:])
                    f.write("\t".join(a_line) + "\n")
                    written += 1
                    if show_progress_interval and written % show_progress_interval == 0:
                        println(f"{indent(indentation_level+1)}{written}", 0)
        result.done_successfully = 1
    except Exception as exc:
        result.errors = 1
        println(
            f"Error saving TSV file {Path(output_path) / output_file_name}: {type(exc).__name__}: {exc}",
            indentation_level,
        )
    result.processed = 1
    if wrap_output_in_lines:
        println("-----------------------------------", indentation_level)
    return result


def save_tree_map_of_string_and_treeset_to_tsv_file(
    output_path: str,
    output_file_name: str,
    data: Dict[str, Set[str]],
    titles: str,
    wrap_output_in_lines: bool,
    show_progress_interval: int,
    indentation_level: int,
    test_or_real: int,
    write_message_step: str,
) -> FileManipulationResult:
    result = FileManipulationResult()
    if wrap_output_in_lines:
        println("-----------------------------------", indentation_level)
    try:
        path = Path(output_path)
        path.mkdir(parents=True, exist_ok=True)
        with (path / output_file_name).open("w", newline="", encoding="utf-8") as f:
            f.write(titles + "\n")
            i = 0
            j = 0
            for key, values in data.items():
                for value in values:
                    f.write(f"{key}\t{value}\n")
                    j += 1
                i += 1
                if show_progress_interval and i % show_progress_interval == 0:
                    println(f"{indent(indentation_level+1)}{i}", 0)
        result.done_successfully = 1
    except Exception:
        result.errors = 1
    result.processed = 1
    if wrap_output_in_lines:
        println("-----------------------------------", indentation_level)
    return result


def group_by_count_from_tsv(
    input_path: str,
    input_file_name: str,
    fmr_array: List[FileManipulationResult],
    key_set_to_check_existence_of_key_field: Optional[Set[str]],
    key_field: str,
    sort_order: SortOrder,
    total_fields_count: int,
    wrap_output_in_lines: bool,
    show_progress_interval: int,
    indentation_level: int,
    test_or_real: int,
    write_message_step: str,
) -> Dict[str, int]:
    if wrap_output_in_lines:
        println("-----------------------------------", indentation_level)
    df = _read_tsv_dataframe(input_path, input_file_name, test_or_real)
    if key_field not in df.columns:
        return {}
    if key_set_to_check_existence_of_key_field is not None:
        df = df[df[key_field].isin(key_set_to_check_existence_of_key_field)]
    counts = df[key_field].value_counts().to_dict()
    if sort_order != SortOrder.DEFAULT_FOR_STRING:
        reverse = sort_order != SortOrder.ASCENDING_INTEGER
        counts = dict(sorted(counts.items(), key=lambda x: int(x[0]) if x[0].isdigit() else x[0], reverse=reverse))
    if wrap_output_in_lines:
        println("-----------------------------------", indentation_level)
    return counts


def _save_dict_to_tsv(
    output_path: str,
    output_file_name: str,
    counts: Dict[str, Any],
    titles: List[str],
    wrap_output_in_lines: bool,
    show_progress_interval: int,
    indentation_level: int,
    write_message_step: str,
) -> FileManipulationResult:
    result = FileManipulationResult()
    if wrap_output_in_lines:
        println("-----------------------------------", indentation_level)
    try:
        path = Path(output_path)
        path.mkdir(parents=True, exist_ok=True)
        with (path / output_file_name).open("w", encoding="utf-8") as f:
            f.write("\t".join(titles) + "\n")
            i = 0
            for key, value in counts.items():
                f.write(f"{key}\t{value}\n")
                i += 1
                if show_progress_interval and i % show_progress_interval == 0:
                    println(f"{indent(indentation_level+1)}{i}", 0)
        result.done_successfully = 1
    except Exception as exc:
        result.errors = 1
        println(
            f"Error saving dict TSV file {Path(output_path) / output_file_name}: {type(exc).__name__}: {exc}",
            indentation_level,
        )
    result.processed = 1
    if wrap_output_in_lines:
        println("-----------------------------------", indentation_level)
    return result


def json_array_to_short_form(value: str, converted_correctly: Optional[bool] = None) -> str:
    try:
        data = json.loads(value)
        result_parts = []
        for item in data:
            if isinstance(item, dict) and "_id" in item and "amount" in item:
                result_parts.append(f"{item['_id']}:{item['amount']}")
        if converted_correctly is not None:
            converted_correctly = True
        return ",".join(result_parts)
    except Exception:
        if converted_correctly is not None:
            converted_correctly = False
        return ""


def clean_file(
    input_path_and_file_name: str,
    output_path_and_file_name: str,
    wrap_output_in_lines: bool,
    show_progress_interval: int,
    indentation_level: int,
    test_or_real: int,
    write_message_step: str,
) -> FileManipulationResult:
    result = FileManipulationResult()
    if wrap_output_in_lines:
        println("-----------------------------------", indentation_level)
    try:
        df = pd.read_csv(input_path_and_file_name, dtype=str, keep_default_na=False, na_filter=False)
        Path(output_path_and_file_name).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path_and_file_name, sep="\t", index=False)
        result.done_successfully = 1
    except Exception as exc:
        result.errors = 1
        println(
            f"Error cleaning file {input_path_and_file_name} -> {output_path_and_file_name}: {type(exc).__name__}: {exc}",
            indentation_level,
        )
    result.processed = 1
    if wrap_output_in_lines:
        println("-----------------------------------", indentation_level)
    return result
