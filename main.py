#!/usr/bin/env python3
"""
Entry point for the Python bug assignment prediction system.

Usage:
    python main.py --experiment COMMIT_WORD2VEC --input /path/to/input --output /path/to/output
    python main.py --experiment TTBA --input /path/to/input --output /path/to/output --w2v-model /path/to/model
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

import algorithm
import w2v_utils
from constants import (
    DATASET_DIRECTORY_FOR_THE_ALGORITHM__EXPERIMENT_OUTPUT,
    DATASET_DIRECTORY_FOR_THE_ALGORITHM__GH__EXPERIMENT_MAIN,
    DATASET_DIRECTORY_FOR_THE_ALGORITHM__GH__EXPERIMENT_TFIDF,
    DATASET_DIRECTORY_FOR_THE_ALGORITHM__SO__EXPERIMENT,
    ExperimentType,
)


def map_experiment_name_to_type(name: str) -> ExperimentType:
    """Map user-friendly experiment names to ExperimentType enum values."""
    mapping = {
        "TTBA": ExperimentType.CALCULATE_OUR_METRIC__TTBA,
        "ORIGINAL_TFIDF": ExperimentType.JUST_CALCULATE_ORIGINAL_TF_IDF,
        "TIME_TFIDF": ExperimentType.JUST_CALCULATE_TIME_TF_IDF,
        "TIME_TFIDF2": ExperimentType.JUST_CALCULATE_TIME_TF_IDF2,
        "TBA": ExperimentType.CALCULATE_TBA,
        "VTBA_GH": ExperimentType.CALCULATE_VTBA_GH,
        "VTBA_GH_ONLINE": ExperimentType.CALCULATE_VTBA_GH__CALCULATE_WEIGHS_ONLINE,
        "VTBA_SOURCECODE": ExperimentType.CALCULATE_VTBA_SOURCECODE,
        "COMMIT_WORD2VEC": ExperimentType.COMMIT_WORD2VEC,
    }
    if name not in mapping:
        raise ValueError(
            f"Unknown experiment type '{name}'. Choose from: {', '.join(mapping.keys())}"
        )
    return mapping[name]


def resolve_dataset_paths(
    experiment_type: ExperimentType,
    input_path: str,
    node_weights_path: Optional[str] = None,
    node_weights_file: str = "nodeWeights.tsv",
) -> tuple[str, str, str, str, str]:
    """Resolve dataset paths based on experiment type."""
    input_dir = Path(input_path).resolve()
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    if experiment_type == ExperimentType.CALCULATE_OUR_METRIC__TTBA:
        node_weights_input_path = node_weights_path or str(DATASET_DIRECTORY_FOR_THE_ALGORITHM__SO__EXPERIMENT)
        additional_node_weights_input_path = ""
        additional_node_weights_input_file_name_prefix = ""
    elif experiment_type in {
        ExperimentType.JUST_CALCULATE_ORIGINAL_TF_IDF,
        ExperimentType.JUST_CALCULATE_TIME_TF_IDF,
        ExperimentType.JUST_CALCULATE_TIME_TF_IDF2,
        ExperimentType.CALCULATE_TBA,
    }:
        node_weights_input_path = node_weights_path or str(DATASET_DIRECTORY_FOR_THE_ALGORITHM__SO__EXPERIMENT)
        additional_node_weights_input_path = ""
        additional_node_weights_input_file_name_prefix = ""
    elif experiment_type in {
        ExperimentType.CALCULATE_VTBA_GH,
        ExperimentType.CALCULATE_VTBA_GH__CALCULATE_WEIGHS_ONLINE,
    }:
        node_weights_input_path = node_weights_path or str(DATASET_DIRECTORY_FOR_THE_ALGORITHM__GH__EXPERIMENT_MAIN)
        node_weights_file = "nodeWeights2-bugsAndCommitsAndPRsEtc.tsv"
        additional_node_weights_input_path = ""
        additional_node_weights_input_file_name_prefix = ""
    elif experiment_type == ExperimentType.CALCULATE_VTBA_SOURCECODE:
        node_weights_input_path = node_weights_path or str(DATASET_DIRECTORY_FOR_THE_ALGORITHM__SO__EXPERIMENT)
        additional_node_weights_input_path = str(DATASET_DIRECTORY_FOR_THE_ALGORITHM__GH__EXPERIMENT_MAIN)
        additional_node_weights_input_file_name_prefix = "nodeWeights3-sourceCode-"
    elif experiment_type == ExperimentType.COMMIT_WORD2VEC:
        node_weights_input_path = node_weights_path or str(DATASET_DIRECTORY_FOR_THE_ALGORITHM__GH__EXPERIMENT_MAIN)
        additional_node_weights_input_path = ""
        additional_node_weights_input_file_name_prefix = ""
    else:
        node_weights_input_path = node_weights_path or str(DATASET_DIRECTORY_FOR_THE_ALGORITHM__SO__EXPERIMENT)
        additional_node_weights_input_path = ""
        additional_node_weights_input_file_name_prefix = ""

    return (
        str(input_dir),
        node_weights_input_path,
        node_weights_file,
        additional_node_weights_input_path,
        additional_node_weights_input_file_name_prefix,
    )


def main() -> int:
    """Main entry point for the bug assignment prediction system."""
    parser = argparse.ArgumentParser(
        description="Run bug assignment prediction experiments using various methodologies.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --experiment COMMIT_WORD2VEC --input ./data --output ./results
  python main.py --experiment TTBA --input ./data --output ./results --w2v-model ./model.bin
  python main.py --experiment ORIGINAL_TFIDF --input ./data --output ./results
        """,
    )

    parser.add_argument(
        "--experiment",
        type=str,
        required=True,
        help=(
            "Experiment type. One of: TTBA, ORIGINAL_TFIDF, TIME_TFIDF, TIME_TFIDF2, TBA, "
            "VTBA_GH, VTBA_GH_ONLINE, VTBA_SOURCECODE, COMMIT_WORD2VEC"
        ),
    )

    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input directory path containing TSV files (e.g., 7-projects.tsv, 1-bugs-*.tsv, etc.)",
    )

    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output directory where results will be written.",
    )

    parser.add_argument(
        "--node-weights-path",
        type=str,
        default=None,
        help=(
            "Path to node weights directory (e.g., StackOverflow dataset directory). "
            "If not provided, uses defaults based on experiment type."
        ),
    )

    parser.add_argument(
        "--w2v-model",
        type=str,
        default=None,
        help="Path to Word2Vec model file (gensim format). If provided, loads it for similarity calculations.",
    )

    parser.add_argument(
        "--is-main-run",
        action="store_true",
        default=True,
        help="Run on all projects (default: True)",
    )

    parser.add_argument(
        "--is-tuning",
        action="store_true",
        default=False,
        help="Run on tuning projects only (overrides --is-main-run)",
    )

    parser.add_argument(
        "--developer-threshold",
        type=int,
        default=1,
        help="Minimum number of bugs a developer must have fixed to be considered (default: 1)",
    )

    parser.add_argument(
        "--show-progress-interval",
        type=int,
        default=5000,
        help="Print progress every N processed items (default: 5000)",
    )

    parser.add_argument(
        "--wrap-output",
        action="store_true",
        default=False,
        help="Wrap output with visual separators.",
    )

    args = parser.parse_args()

    try:
        experiment_type = map_experiment_name_to_type(args.experiment)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"Error: Input directory not found: {input_path}", file=sys.stderr)
        return 1

    output_path = Path(args.output).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    if args.w2v_model:
        w2v_model_path = Path(args.w2v_model).resolve()
        if not w2v_model_path.exists():
            print(f"Error: Word2Vec model file not found: {w2v_model_path}", file=sys.stderr)
            return 1
        print(f"Loading Word2Vec model from: {w2v_model_path}")
        w2v_utils.load_model(w2v_model_path)
    else:
        print("Note: No Word2Vec model specified. Using default or environment path.")

    try:
        (
            input_dir,
            node_weights_input_path,
            node_weights_file,
            additional_node_weights_input_path,
            additional_node_weights_input_file_name_prefix,
        ) = resolve_dataset_paths(
            experiment_type, str(input_path), args.node_weights_path
        )
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    is_main_run = not args.is_tuning

    print(f"Starting experiment: {args.experiment}")
    print(f"  Input directory: {input_dir}")
    print(f"  Output directory: {output_path}")
    print(f"  Node weights path: {node_weights_input_path}")
    print(f"  Node weights file: {node_weights_file}")
    print(f"  Is main run: {is_main_run}")
    print()

    try:
        algorithm.experiment(
            general_experiment_type=experiment_type,
            input_dir=input_dir,
            node_weights_input_path=node_weights_input_path,
            node_weights_input_file=node_weights_file,
            additional_node_weights_input_path=additional_node_weights_input_path,
            additional_node_weights_input_file_name_prefix=additional_node_weights_input_file_name_prefix,
            output_path=str(output_path),
            is_main_run=is_main_run,
            developer_filteration_threshold_least_number_of_bugs_to_fix_to_be_considered=args.developer_threshold,
            wrap_output_in_lines=args.wrap_output,
            show_progress_interval=args.show_progress_interval,
            indentation_level=0,
        )
        print("\nExperiment completed successfully.")
        return 0
    except Exception as e:
        print(f"Error during experiment execution: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
