from __future__ import annotations

import math
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set

import alg_prep
import io_utils
from constants import (
    ALL,
    ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS,
    ASSIGNMENT_FILE_NAMES,
    COMMUNITY_FILE_NAMES,
    DATASET_DIRECTORY_FOR_THE_ALGORITHM__EXPERIMENT_OUTPUT,
    EvidenceType,
    ExperimentType,
    ProjectType,
    BTOption1WhatToAddToAllBugs,
    BTOption2W,
    BTOption3TF,
    BTOption4IDF,
    BTOption5PrioritizePAs,
    BTOption6WhatToAddToAllCommits,
    BTOption7WhenToCountTextLength,
    BTOption8Recency,
    TAGS_SEPARATOR,
    allValidCharactersInSOURCECODE_Strict_ForRegEx,
    ASSIGNMENT_RESULTS_OVERAL_FOLDER_NAME,
    DATASET_DIRECTORY_FOR_THE_ALGORITHM__GH__EXPERIMENT_TFIDF,
    DATASET_DIRECTORY_FOR_THE_ALGORITHM__SO__EXPERIMENT,
    DATASET_DIRECTORY_FOR_THE_ALGORITHM__GH__EXPERIMENT_MAIN,
    DATASET_DIRECTORY_FOR_THE_ALGORITHM__EXPERIMENT_OUTPUT,
    THIS_IS_REAL,
    THIS_IS_A_TEST,
    SEQ_NUM____NO_NEED_TO_TRIAGE_THIS_TYPE___OR___THIS_IS_NOT__NON_B_A_EVIDENCE,
    SEQ_NUM____THIS_IS_NOT__B_A_EVIDENCE,
)
from io_utils import FileManipulationResult
from models import Assignment, Assignee, Bug, Project


# Minimal runtime support for the Algorithm driver.
class Graph:
    def __init__(self) -> None:
        self.node_weights: Dict[str, float] = {}

    def load_graph(
        self,
        input_path: str,
        input_file_name: str,
        no_edges: str,
        fmr: FileManipulationResult,
        wrap_output_in_lines: bool,
        show_progress_interval: int,
        indentation_level: int,
        test_or_real: int,
        write_message_step: str,
    ) -> None:
        path = Path(input_path) / input_file_name
        if not path.exists():
            fmr.errors += 1
            print(
                f"{write_message_step}- Error: Graph file not found: {path} (operation: load_graph)"
            )
            return
        try:
            df = io_utils._read_tsv_dataframe(input_path, input_file_name, test_or_real)
            for row in df.itertuples(index=False):
                if len(row) >= 2:
                    token = str(row[0])
                    try:
                        weight = float(row[1])
                    except (ValueError, TypeError):
                        weight = 0.0
                    self.node_weights[token] = weight
        except Exception as exc:
            fmr.errors += 1
            print(
                f"{write_message_step}- Error loading graph from {path} (operation: load_graph): {type(exc).__name__}: {exc}"
            )

    def has_node(self, token: str) -> bool:
        return token in self.node_weights

    def get_node_weight(self, token: str) -> float:
        return self.node_weights.get(token, 0.0)

    def get_node_names(self) -> List[str]:
        return list(self.node_weights.keys())

    def set_node_weight(self, token: str, weight: float) -> None:
        self.node_weights[token] = weight


class WordsAndCounts:
    def __init__(
        self,
        text: str,
        option_when_to_count_text_length: BTOption7WhenToCountTextLength,
        original_number_of_words: int,
        stop_words: Optional[Set[str]],
    ) -> None:
        tokens = [w for w in text.split() if w]
        if stop_words:
            tokens = [w for w in tokens if w not in stop_words]
        self.total_number_of_words = original_number_of_words if option_when_to_count_text_length == BTOption7WhenToCountTextLength.USE_TEXT_LENGTH_BEFORE_REMOVING_NON_SO_TAGS else len(tokens)
        counter = Counter(tokens)
        self.words = list(counter.keys())
        self.counts = [counter[word] for word in self.words]
        self.size = len(self.words)


@dataclass
class AssignmentStat:
    bug_number: str
    date: datetime
    login: str
    rank: int
    real_assignees_ranks: Dict[str, int]


def indent(level: int) -> str:
    return " " * (4 * level)


def concat_two_write_message_steps(prefix1: str, prefix2: str) -> str:
    if not prefix1:
        return prefix2
    if not prefix2:
        return prefix1
    return f"{prefix1}-{prefix2}"


def sanitize_folder_name(name: str) -> str:
    return re.sub(r"[\\/:*?\"<>|]+", "_", name)


def create_folder_for_results(
    base_output_path: str,
    assignment_results_folder_name: str,
    experiment_title: str,
    is_main_run: bool,
    fmr: FileManipulationResult,
    indentation_level: int,
) -> str:
    folder_name = sanitize_folder_name(experiment_title)
    subfolder_name = "main" if is_main_run else "tuning"
    result_folder = Path(base_output_path) / assignment_results_folder_name / f"{folder_name}-{subfolder_name}"
    result_folder.mkdir(parents=True, exist_ok=True)
    return str(result_folder)


def write_assignment_stats(
    output_path: str,
    output_summaries_tsv_file_name: str,
    assignment_results_overall_folder_name: str,
    detailed_assignment_results_subfolder_name: str,
    assignment_type_description: str,
    projects_and_their_assignment_stats: Dict[str, List[AssignmentStat]],
    project_names_and_their_ids_ordered_by_name: Dict[str, str],
    projects_and_their_communities: Dict[str, List[List[str]]],
    experiment_details: str,
    fmr: FileManipulationResult,
    total_running_time_for_this_assignment_type_in_the_loop: float,
    wrap_output_in_lines: bool,
    show_progress_interval: int,
    indentation_level: int,
    write_message_step: str,
) -> None:
    # Ensure main output dir exists
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create (or ensure) the assignment-results overall folder (e.g., outDetails)
    assignment_results_dir = output_dir / assignment_results_overall_folder_name
    assignment_results_dir.mkdir(parents=True, exist_ok=True)

    # detailed_assignment_results_subfolder_name may be either a full path (returned by
    # create_folder_for_results) or just a folder name; handle both cases.
    detailed_dir = Path(detailed_assignment_results_subfolder_name)
    if not detailed_dir.is_absolute():
        detailed_dir = assignment_results_dir / detailed_assignment_results_subfolder_name
    detailed_dir.mkdir(parents=True, exist_ok=True)

    # Java version writes a detailed file named: <folderName> - <assignment_type_description>.tsv
    detailed_folder_name = detailed_dir.name
    detailed_file = detailed_dir / f"{detailed_folder_name} - {sanitize_folder_name(assignment_type_description)}.tsv"

    # Main overall summary file (per-assignment-type) in the top-level output dir
    overall_file = output_dir / f"{output_summaries_tsv_file_name} - {sanitize_folder_name(assignment_type_description)}.tsv"

    # Combined overall file for ALL assigned types
    combined_file = output_dir / f"{output_summaries_tsv_file_name} - ALL_ASSIGNED_TYPES.tsv"

    try:
        # Write detailed stats using the exact Java column names and data structure
        header = (
            "project\tbugNumber\tassignmentDate\tourTopRecommendedRealAssignee\t"
            "ourTopRecommendedRealAssigneeRank\ttotalCommunityMembers\trealAssigneesTillNow\n"
        )
        with detailed_file.open("w", encoding="utf-8") as writer:
            writer.write(header)
            # Iterate owner_repo->project_id in the same order as provided
            for owner_repo, project_id in project_names_and_their_ids_ordered_by_name.items():
                # Normalize key types for lookup (handle both string and potential int keys)
                possible_keys = [project_id, str(project_id)]
                assignment_stats = None
                for k in possible_keys:
                    if k in projects_and_their_assignment_stats:
                        assignment_stats = projects_and_their_assignment_stats[k]
                        break
                if assignment_stats is None:
                    assignment_stats = []

                community = None
                for k in possible_keys:
                    if k in projects_and_their_communities:
                        community = projects_and_their_communities[k]
                        break
                community_size = len(community) if community is not None else 0

                for stat in assignment_stats:
                    # Format assignment date: use isoformat if available
                    assignment_date = (
                        stat.date.isoformat()
                        if hasattr(stat.date, "isoformat")
                        else str(stat.date)
                    )
                    our_assignee = stat.login
                    our_rank = stat.rank
                    # Real assignees: comma-separated logins from the dict keys
                    real_assignees = (
                        ", ".join(list(stat.real_assignees_ranks.keys()))
                        if stat.real_assignees_ranks
                        else ""
                    )
                    writer.write(
                        f"{owner_repo}\t{stat.bug_number}\t{assignment_date}\t{our_assignee}\t{our_rank}\t{community_size}\t{real_assignees}\n"
                    )

        # Append (or create) the per-assignment-type overall summary file. Use append to match Java.
        need_header = not overall_file.exists()
        with overall_file.open("a", encoding="utf-8") as writer2:
            if need_header:
                writer2.write(header)
            for owner_repo, project_id in project_names_and_their_ids_ordered_by_name.items():
                possible_keys = [project_id, str(project_id)]
                assignment_stats = None
                for k in possible_keys:
                    if k in projects_and_their_assignment_stats:
                        assignment_stats = projects_and_their_assignment_stats[k]
                        break
                if assignment_stats is None:
                    assignment_stats = []

                community = None
                for k in possible_keys:
                    if k in projects_and_their_communities:
                        community = projects_and_their_communities[k]
                        break
                community_size = len(community) if community is not None else 0

                for stat in assignment_stats:
                    assignment_date = (
                        stat.date.isoformat()
                        if hasattr(stat.date, "isoformat")
                        else str(stat.date)
                    )
                    our_assignee = stat.login
                    our_rank = stat.rank
                    real_assignees = (
                        ", ".join(list(stat.real_assignees_ranks.keys()))
                        if stat.real_assignees_ranks
                        else ""
                    )
                    writer2.write(
                        f"{owner_repo}\t{stat.bug_number}\t{assignment_date}\t{our_assignee}\t{our_rank}\t{community_size}\t{real_assignees}\n"
                    )

        # Ensure combined file exists (Java writes more complex headers and summaries; create placeholder if missing)
        if not combined_file.exists():
            with combined_file.open("w", encoding="utf-8") as writer3:
                writer3.write("Experiment title\tTIME\tMRR\tMAP\tTop1\tTop5\tTop10\t...\n")

        fmr.done_successfully += 1
    except Exception as exc:
        fmr.errors += 1
        print(f"{write_message_step}- Error writing assignment stats to {detailed_file} (operation: write_assignment_stats): {type(exc).__name__}: {exc}")


def project_type(project_id: str, owner_repo: str) -> ProjectType:
    if owner_repo in list(ALL) if isinstance(ALL, str) else False:
        return ProjectType.FASE_13
    if owner_repo in [proj.lower() for proj in ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS]:
        return ProjectType.FASE_13
    return ProjectType.OTHERS_UNKNOWN


def is_a_project_which_is_used_for_main_run(project_id: str, owner_repo: str) -> bool:
    return True


def is_a_project_which_is_used_for_tuning(project_id: str, owner_repo: str) -> bool:
    return True


def remove_assignments_of_developers_who_fixed_at_least_n_bugs(
    assignments_of_this_project: List[List[str]],
    threshold: int,
    logins_tags_types_and_their_evidence: Dict[str, Dict[str, Dict[int, List[Any]]]],
    indentation_level: int,
    fmr: FileManipulationResult,
) -> None:
    return


def update_rank_of_real_assignees_and_return_the_best_assignee(
    real_assignees: Dict[str, Dict[str, int]],
    bug_number: str,
    scores: Dict[str, float],
    rnd: random.Random,
) -> Assignee:
    current_ranks = real_assignees.setdefault(bug_number, {})
    ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    best_login = ordered[0][0] if ordered else ""
    rank = 1
    for login, _score in ordered:
        if login in current_ranks:
            current_ranks[login] = rank
        rank += 1
    best_rank = current_ranks.get(best_login, rank if best_login else -1)
    return Assignee(login=best_login, rank=best_rank)


def read_and_index_commit_diff_evidence(
    input_path: str,
    project_id: str,
    projects: Dict[str, Any],
    fmr: FileManipulationResult,
    developer_commit_index: Dict[str, List[Any]],
    so_tags: List[str],
    indentation_level: int,
) -> None:
    return


def build_evidence_types_to_consider(
    evidence_types: Sequence[int],
    assignment_evidence_type: int,
) -> List[int]:
    evidence_types_to_consider: List[int] = []
    if evidence_types[0] == 1:
        evidence_types_to_consider.append(assignment_evidence_type)
    non_assignment_map = {
        1: EvidenceType.COMMIT.value,
        2: EvidenceType.PR.value,
        3: EvidenceType.BUG_COMMENT.value,
        4: EvidenceType.COMMIT_COMMENT.value,
        5: EvidenceType.PR_COMMENT.value,
    }
    for index in range(1, len(evidence_types)):
        if evidence_types[index] == 1:
            evidence_types_to_consider.append(non_assignment_map[index])
    return evidence_types_to_consider


def parse_boolean_list(values: Sequence[int]) -> List[bool]:
    return [bool(v) for v in values]


def maybe_int(value: Optional[str]) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def maybe_float(value: Optional[str]) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def parse_iso_datetime_or_now(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            return datetime.now()


def bug_assignment(
    input_path: str,
    node_weights_input_path: str,
    node_weights_file_name: str,
    additional_node_weights_input_path: str,
    additional_node_weights_input_file_name_prefix: str,
    output_path: str,
    output_summaries_tsv_file_name: str,
    is_main_run: bool,
    assignment_types_to_triage: Sequence[int],
    evidence_types: Sequence[int],
    total_evidence_types_count: int,
    experiment_title: str,
    experiment_details: str,
    option1_what_to_add_to_all_bugs: BTOption1WhatToAddToAllBugs,
    option2_w: BTOption2W,
    option3_tf: BTOption3TF,
    option4_idf: BTOption4IDF,
    option5_prioritize_pas: BTOption5PrioritizePAs,
    option6_what_to_add_to_all_commits: BTOption6WhatToAddToAllCommits,
    option7_when_to_count_text_length: BTOption7WhenToCountTextLength,
    option8_recency: BTOption8Recency,
    general_experiment_type: ExperimentType,
    developer_filteration_threshold_least_number_of_bugs_to_fix_to_be_considered: int,
    fmr: FileManipulationResult,
    wrap_output_in_lines: bool,
    show_progress_interval: int,
    indentation_level: int,
    test_or_real: int,
    write_message_step: str,
) -> None:
    # Open debug log file
    debug_log_path = Path(output_path) / "debug_log.txt"
    debug_log_file = debug_log_path.open("w", encoding="utf-8")
    
    print(f"{indent(indentation_level)}-----------------------------------")
    print(f"{indent(indentation_level)}{concat_two_write_message_steps(write_message_step, 'Bug assignment experiment:')}")
    print(f"{indent(indentation_level+1)}Started ...")

    loop_extra_time_reading_communities = 0.0
    initial_extra_time_reading_graph_bugs_and_projects_info = 0.0
    initial_extra_time_reading_assignments_and_reading_and_indexing_non_assignment_evidence = 0.0
    loop_extra_time_reading_assignment_evidence_indexing = 0.0
    d1 = datetime.now()

    local_fmr = FileManipulationResult()
    total_fmr = FileManipulationResult()
    Path(output_path).mkdir(parents=True, exist_ok=True)

    print(f"{indent(indentation_level)}{concat_two_write_message_steps(write_message_step, '1- Reading main graph and 13 project-specific graphs:')}")
    print(f"{indent(indentation_level+1)}Started ...")

    graph = Graph()
    graph.load_graph(
        node_weights_input_path,
        node_weights_file_name,
        "",
        local_fmr,
        wrap_output_in_lines,
        show_progress_interval * 1000,
        indentation_level + 1,
        test_or_real,
        concat_two_write_message_steps(write_message_step, "1-1- Main graph"),
    )

    graphs: List[Graph] = []
    if general_experiment_type == ExperimentType.CALCULATE_VTBA_SOURCECODE:
        for i in range(13):
            subgraph = Graph()
            file_name = f"{additional_node_weights_input_file_name_prefix}{i}.tsv"
            subgraph.load_graph(
                additional_node_weights_input_path,
                file_name,
                "",
                local_fmr,
                wrap_output_in_lines,
                show_progress_interval * 1000,
                indentation_level + 1,
                test_or_real,
                concat_two_write_message_steps(write_message_step, f"1-{i+2}"),
            )
            graphs.append(subgraph)
    print(f"{indent(indentation_level+1)}Finished.")

    total_fmr = io_utils.add_file_manipulation_results(total_fmr, local_fmr)
    debug_msg = f"[DEBUG-1] After loading graphs: errors={total_fmr.errors}, done_successfully={total_fmr.done_successfully}, processed={total_fmr.processed}"
    debug_log_file.write(debug_msg + "\n")
    print(debug_msg)
    stop_words: Set[str] = set()
    if general_experiment_type in {
        ExperimentType.JUST_CALCULATE_ORIGINAL_TF_IDF,
        ExperimentType.JUST_CALCULATE_TIME_TF_IDF,
        ExperimentType.JUST_CALCULATE_TIME_TF_IDF2,
        ExperimentType.CALCULATE_TBA,
        ExperimentType.CALCULATE_VTBA_GH,
        ExperimentType.CALCULATE_VTBA_GH__CALCULATE_WEIGHS_ONLINE,
        ExperimentType.CALCULATE_VTBA_SOURCECODE,
    }:
        stop_words = io_utils.read_unique_field_from_tsv(
            node_weights_input_path,
            "stopWords.tsv",
            0,
            1,
            io_utils.LogicalOperation.NO_CONDITION,
            0,
            io_utils.ConditionType.NOTHING,
            "",
            io_utils.FieldType.NOT_IMPORTANT,
            0,
            io_utils.ConditionType.NOTHING,
            "",
            io_utils.FieldType.NOT_IMPORTANT,
            True,
            indentation_level + 1,
            100000,
            test_or_real,
            concat_two_write_message_steps(write_message_step, "2"),
        )

    projects = io_utils.read_unique_key_and_its_value_from_tsv(
        input_path,
        "7-projects.tsv",
        None,
        0,
        14,
        "1$2$3$4$5$6$7$8$9$10$11$12$13",
        io_utils.LogicalOperation.NO_CONDITION,
        0,
        io_utils.ConditionType.NOTHING,
        "",
        io_utils.FieldType.NOT_IMPORTANT,
        0,
        io_utils.ConditionType.NOTHING,
        "",
        io_utils.FieldType.NOT_IMPORTANT,
        wrap_output_in_lines,
        show_progress_interval,
        indentation_level + 1,
        test_or_real,
        concat_two_write_message_steps(write_message_step, "3"),
    )

    project_id_bug_number_and_their_bug_info = io_utils.read_unique_combined_key_and_its_value_from_tsv(
        input_path,
        f"1-bugs-{ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS[4]}.tsv",
        local_fmr,
        None,
        "0$1",
        9,
        "2$3$4$5$6$7$8",
        io_utils.LogicalOperation.NO_CONDITION,
        0,
        io_utils.ConditionType.NOTHING,
        "",
        io_utils.FieldType.NOT_IMPORTANT,
        0,
        io_utils.ConditionType.NOTHING,
        "",
        io_utils.FieldType.NOT_IMPORTANT,
        wrap_output_in_lines,
        show_progress_interval * 1000,
        indentation_level + 1,
        test_or_real,
        "4",
    )
    total_fmr = io_utils.add_file_manipulation_results(total_fmr, local_fmr)
    debug_msg = f"[DEBUG-2] After reading projects: errors={total_fmr.errors}, done_successfully={total_fmr.done_successfully}, processed={total_fmr.processed}"
    debug_log_file.write(debug_msg + "\n")
    print(debug_msg)

    evidence_types_to_consider_count = 0
    for j in range(total_evidence_types_count):
        if evidence_types[j] == 1:
            evidence_types_to_consider_count += 1
    evidence_types_to_consider: List[Optional[int]] = []
    if evidence_types[0] == 1:
        evidence_types_to_consider.append(None)
    for j in range(1, total_evidence_types_count):
        if evidence_types[j] == 1:
            non_assignment_type = {
                1: EvidenceType.COMMIT.value,
                2: EvidenceType.PR.value,
                3: EvidenceType.BUG_COMMENT.value,
                4: EvidenceType.COMMIT_COMMENT.value,
                5: EvidenceType.PR_COMMENT.value,
            }[j]
            evidence_types_to_consider.append(non_assignment_type)

    if wrap_output_in_lines:
        print(f"{indent(indentation_level+1)}-----------------------------------")
    print(f"{indent(indentation_level+1)}{concat_two_write_message_steps(write_message_step, '5- Reading needed assignment file(s):')}")
    print(f"{indent(indentation_level+2)}Started ...")

    projects_and_their_assignments_al_for_different_assignment_types: List[Dict[str, List[List[str]]]] = []
    for i in range(len(assignment_types_to_triage)):
        if assignment_types_to_triage[i] == 1:
            projects_and_their_assignments = io_utils.read_non_unique_key_and_its_value_from_tsv(
                input_path,
                f"{ASSIGNMENT_FILE_NAMES[i]}.tsv",
                local_fmr,
                None,
                0,
                io_utils.SortOrder.DEFAULT_FOR_STRING,
                7,
                "1$2$3",
                [],
                io_utils.LogicalOperation.NO_CONDITION,
                0,
                io_utils.ConditionType.NOTHING,
                "",
                io_utils.FieldType.NOT_IMPORTANT,
                0,
                io_utils.ConditionType.NOTHING,
                "",
                io_utils.FieldType.NOT_IMPORTANT,
                wrap_output_in_lines,
                show_progress_interval * 1000,
                indentation_level + 2,
                test_or_real,
                concat_two_write_message_steps(write_message_step, f"5-{i+1}-{ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS[i]}"),
            )
            total_fmr = io_utils.add_file_manipulation_results(total_fmr, local_fmr)
            debug_msg = f"[DEBUG-3] After reading assignments (assignment_type={i}): errors={total_fmr.errors}, done_successfully={total_fmr.done_successfully}, processed={total_fmr.processed}"
            debug_log_file.write(debug_msg + "\n")
            print(debug_msg)
        else:
            projects_and_their_assignments = {}
            print(
                f"{indent(indentation_level+2)}{concat_two_write_message_steps(write_message_step, f'5-{i+1}- \"{ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS[i]}\" --> is not configured to use or run the prediction algorithm on.')}")
        projects_and_their_assignments_al_for_different_assignment_types.append(projects_and_their_assignments)
    print(f"{indent(indentation_level+2)}Finished.")
    if wrap_output_in_lines:
        print(f"{indent(indentation_level+1)}-----------------------------------")

    project_id_login_tags_types_and_their_evidence: Dict[str, Any] = {}
    alg_prep.read_and_index_non_assignment_evidence(
        input_path,
        "2-commits.tsv",
        "3-PRs.tsv",
        "4-bugComments.tsv",
        "5-commitComments.tsv",
        "6-PRComments.tsv",
        projects_and_their_assignments_al_for_different_assignment_types,
        {i: assignment_types_to_triage[i] == 1 for i in range(len(assignment_types_to_triage))},
        local_fmr,
        {i: evidence_types[i] == 1 for i in range(len(evidence_types))},
        projects,
        None,
        project_id_login_tags_types_and_their_evidence,
        graph,
        graphs,
        option1_what_to_add_to_all_bugs,
        option2_w,
        option3_tf,
        option4_idf,
        option5_prioritize_pas,
        option6_what_to_add_to_all_commits,
        option7_when_to_count_text_length,
        general_experiment_type,
        wrap_output_in_lines,
        show_progress_interval * 100,
        indentation_level + 1,
        concat_two_write_message_steps(write_message_step, "6"),
    )
    total_fmr = io_utils.add_file_manipulation_results(total_fmr, local_fmr)
    debug_msg = f"[DEBUG-4a] After indexing evidence: errors={total_fmr.errors}, done_successfully={total_fmr.done_successfully}, processed={total_fmr.processed}"
    debug_log_file.write(debug_msg + "\n")
    print(debug_msg)
    total_fmr = io_utils.add_file_manipulation_results(total_fmr, local_fmr)
    debug_msg = f"[DEBUG-4b] After second evidence update: errors={total_fmr.errors}, done_successfully={total_fmr.done_successfully}, processed={total_fmr.processed}"
    debug_log_file.write(debug_msg + "\n")
    print(debug_msg)

    detailed_assignment_results_subfolder_name = create_folder_for_results(
        output_path,
        ASSIGNMENT_RESULTS_OVERAL_FOLDER_NAME,
        experiment_title,
        is_main_run,
        local_fmr,
        indentation_level,
    )
    total_fmr = io_utils.add_file_manipulation_results(total_fmr, local_fmr)
    debug_msg = f"[DEBUG-5] After creating results folder: errors={total_fmr.errors}, done_successfully={total_fmr.done_successfully}, processed={total_fmr.processed}"
    debug_log_file.write(debug_msg + "\n")
    print(debug_msg)
    d3 = datetime.now()

    if total_fmr.errors > 0:
        print(f"{indent(indentation_level+3)}There are errors! Stopping ...")
    else:
        initial_extra_time_reading_assignments_and_reading_and_indexing_non_assignment_evidence = (d3 - d1).total_seconds()
        if wrap_output_in_lines:
            print(f"{indent(indentation_level+1)}-----------------------------------")
        total_assignment_types_to_triage = sum(1 for x in assignment_types_to_triage if x == 1)
        print(f"{indent(indentation_level+1)}{concat_two_write_message_steps(write_message_step, f'7- Running prediction algorithm for {total_assignment_types_to_triage} assignment file(s):')}")
        print(f"{indent(indentation_level+2)}Started ...")

        for i in range(len(assignment_types_to_triage)):
            step = concat_two_write_message_steps(write_message_step, f"7-{i+1}")
            if assignment_types_to_triage[i] != 1:
                print(f"{indent(indentation_level+2)}{step}- Assignments of \"{ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS[i]}\" --> is not configured to run the prediction algorithm on.")
                continue

            d4 = datetime.now()
            if wrap_output_in_lines:
                print(f"{indent(indentation_level+2)}-----------------------------------")
            print(f"{indent(indentation_level+2)}{step}- Predicting \"{ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS[i]}\" assignments:")
            print(f"{indent(indentation_level+3)}Started ...")

            if evidence_types[0] == 1:
                evidence_types_to_consider[0] = i

            projects_and_their_communities = io_utils.read_non_unique_key_and_its_value_from_tsv(
                input_path,
                f"{COMMUNITY_FILE_NAMES[i]}.tsv",
                local_fmr,
                None,
                0,
                io_utils.SortOrder.DEFAULT_FOR_STRING,
                2,
                "1",
                [],
                io_utils.LogicalOperation.NO_CONDITION,
                0,
                io_utils.ConditionType.NOTHING,
                "",
                io_utils.FieldType.NOT_IMPORTANT,
                0,
                io_utils.ConditionType.NOTHING,
                "",
                io_utils.FieldType.NOT_IMPORTANT,
                wrap_output_in_lines,
                show_progress_interval * 1000,
                indentation_level + 3,
                test_or_real,
                concat_two_write_message_steps(write_message_step, f"{step}-2"),
            )
            total_fmr = io_utils.add_file_manipulation_results(total_fmr, local_fmr)
            debug_msg = f"[DEBUG-6] After reading communities (assignment_type={i}): errors={total_fmr.errors}, done_successfully={total_fmr.done_successfully}, processed={total_fmr.processed}"
            debug_log_file.write(debug_msg + "\n")
            print(debug_msg)

            d5 = datetime.now()
            loop_extra_time_reading_communities += (d5 - d4).total_seconds()

            if evidence_types[0] == 1:
                alg_prep.index_assignment_evidence(
                    i,
                    projects_and_their_assignments_al_for_different_assignment_types[i],
                    projects,
                    project_id_bug_number_and_their_bug_info,
                    project_id_login_tags_types_and_their_evidence,
                    graph,
                    graphs,
                    local_fmr,
                    option1_what_to_add_to_all_bugs,
                    option2_w,
                    option3_tf,
                    option4_idf,
                    option5_prioritize_pas,
                    option6_what_to_add_to_all_commits,
                    option7_when_to_count_text_length,
                    general_experiment_type,
                    wrap_output_in_lines,
                    show_progress_interval * 100,
                    indentation_level + 3,
                    concat_two_write_message_steps(write_message_step, f"{step}-3"),
                )
                total_fmr = io_utils.add_file_manipulation_results(total_fmr, local_fmr)
                debug_msg = f"[DEBUG-7] After indexing assignment evidence (assignment_type={i}): errors={total_fmr.errors}, done_successfully={total_fmr.done_successfully}, processed={total_fmr.processed}"
                debug_log_file.write(debug_msg + "\n")
                print(debug_msg)
                if total_fmr.errors > 0:
                    print(f"{indent(indentation_level+3)}There are errors! Breaking ...")
                    print(f"{indent(indentation_level+3)}ERROR DETAILS: {total_fmr.errors} error(s) during processing")
                    print(f"{indent(indentation_level+3)}Processed: {total_fmr.processed}, Done successfully: {total_fmr.done_successfully}")
                    break

            d6 = datetime.now()
            loop_extra_time_reading_assignment_evidence_indexing += (d6 - d5).total_seconds()

            if wrap_output_in_lines:
                print(f"{indent(indentation_level+3)}-----------------------------------")
            print(f"{indent(indentation_level+3)}{step}-4- Assigning:")
            print(f"{indent(indentation_level+4)}Started ...")

            projects_and_their_assignment_stats: Dict[str, List[AssignmentStat]] = {}
            project_names_and_their_ids_ordered_by_name: Dict[str, str] = {}
            project_counter = 1
            rnd = random.Random()
            projects_and_their_assignments = projects_and_their_assignments_al_for_different_assignment_types[i]

            for project_id, assignments_of_this_project in projects_and_their_assignments.items():
                project_info = projects.get(project_id)
                if project_info is None:
                    continue
                project_owner_repo = project_info[0] if isinstance(project_info, (list, tuple)) else str(project_info)
                project = Project(
                    id=project_id,
                    owner_repo=project_owner_repo,
                    description=project_info[1] if isinstance(project_info, (list, tuple)) and len(project_info) > 1 else "",
                    description_number_of_words=maybe_int(project_info[2]) if isinstance(project_info, (list, tuple)) and len(project_info) > 2 else 0,
                    main_language_percentages=project_info[3] if isinstance(project_info, (list, tuple)) and len(project_info) > 3 else "[]",
                    overal_starting_date=datetime(1970, 1, 1),
                )
                if project_type(project_id, project.owner_repo) == ProjectType.FASE_13:
                    project_names_and_their_ids_ordered_by_name[project.owner_repo] = project_id
                    if (
                        (is_main_run and is_a_project_which_is_used_for_main_run(project_id, project.owner_repo))
                        or (not is_main_run and is_a_project_which_is_used_for_tuning(project_id, project.owner_repo))
                    ):
                        if wrap_output_in_lines:
                            print(f"{indent(indentation_level+4)}-----------------------------------")
                        print(f"{indent(indentation_level+4)}{concat_two_write_message_steps(step, str(project_counter))}- {project.owner_repo} (projectId: {project_id})")

                        updating_graph = Graph()
                        occurrences: Dict[str, int] = {}
                        max_number_of_occurrences_for_a_keyword = 0

                        community = projects_and_their_communities.get(project_id, [])
                        real_assignees: Dict[str, Dict[str, int]] = {}
                        logins_tags_types_and_their_evidence = project_id_login_tags_types_and_their_evidence.get(project_id, {})
                        words_and_the_developers_used_them_up_to_now_last_usage_date: Dict[str, Dict[str, datetime]] = {}
                        words_and_the_developers_used_them_up_to_now_all_usage_dates: Dict[str, Dict[str, Set[datetime]]] = {}

                        number_of_bugs_processed = 0
                        previous_assignees_in_this_project: Set[str] = set()
                        remove_assignments_of_developers_who_fixed_at_least_n_bugs(
                            assignments_of_this_project,
                            developer_filteration_threshold_least_number_of_bugs_to_fix_to_be_considered,
                            logins_tags_types_and_their_evidence,
                            indentation_level + 5,
                            local_fmr,
                        )
                        total_fmr = io_utils.add_file_manipulation_results(total_fmr, local_fmr)
                        debug_msg = f"[DEBUG-8] After removing assignments (assignment_type={i}, project_id={project_id}): errors={total_fmr.errors}, done_successfully={total_fmr.done_successfully}, processed={total_fmr.processed}"
                        debug_log_file.write(debug_msg + "\n")
                        print(debug_msg)

                        for j, assignment_fields in enumerate(assignments_of_this_project):
                            a = Assignment(
                                bug_number=assignment_fields[0],
                                date=parse_iso_datetime_or_now(assignment_fields[1]),
                                login=assignment_fields[2],
                            )
                            scores: Dict[str, float] = {}

                            bug_info_key = f"{project_id}\t{a.bug_number}"
                            bug_info = project_id_bug_number_and_their_bug_info.get(bug_info_key)
                            query_bug = Bug(
                                project_id=project_id,
                                number=a.bug_number,
                                title=bug_info[3] if bug_info and len(bug_info) > 3 else "",
                                title_number_of_words=maybe_int(bug_info[4]) if bug_info and len(bug_info) > 4 else 0,
                                body=bug_info[5] if bug_info and len(bug_info) > 5 else "",
                                body_number_of_words=maybe_int(bug_info[6]) if bug_info and len(bug_info) > 6 else 0,
                            )

                            original_number_of_words_in_bug_text_array = [0]
                            bug_text = alg_prep.get_bug_text(
                                project,
                                query_bug,
                                original_number_of_words_in_bug_text_array,
                                option1_what_to_add_to_all_bugs,
                            )
                            original_number_of_words_in_bug_text = original_number_of_words_in_bug_text_array[0]
                            if general_experiment_type == ExperimentType.CALCULATE_TBA:
                                bug_text = re.sub(allValidCharactersInSOURCECODE_Strict_ForRegEx, " ", bug_text.lower()).strip()

                            wac = WordsAndCounts(
                                bug_text,
                                option7_when_to_count_text_length,
                                original_number_of_words_in_bug_text,
                                stop_words,
                            )
                            if wac.size == 0:
                                print(f"{indent(indentation_level+5)}Warning: Empty bug text!")

                            if general_experiment_type == ExperimentType.CALCULATE_VTBA_GH__CALCULATE_WEIGHS_ONLINE:
                                bug_text2 = re.sub(allValidCharactersInSOURCECODE_Strict_ForRegEx, " ", bug_text).lower()
                                words1 = bug_text2.split()
                                # The Java version updates occurrences and node weights online; this is a placeholder.
                                for keyword in words1:
                                    occurrences[keyword] = occurrences.get(keyword, 0) + 1
                                    if occurrences[keyword] > 0:
                                        node_weight = math.log10((1 + occurrences[keyword]) / occurrences[keyword]) / math.log10(1 + occurrences[keyword])
                                        updating_graph.set_node_weight(keyword, node_weight)

                            for community_member in community:
                                login = community_member[0]
                                scores[login] = alg_prep.calculate_score_of_developer_for_bug_assignment(
                                    login,
                                    a,
                                    graph,
                                    updating_graph,
                                    i,
                                    [et for et in evidence_types_to_consider if et is not None],
                                    logins_tags_types_and_their_evidence,
                                    previous_assignees_in_this_project,
                                    wac,
                                    original_number_of_words_in_bug_text,
                                    j + 1,
                                    project.overal_starting_date or datetime(1970, 1, 1),
                                    general_experiment_type,
                                    len(community),
                                    words_and_the_developers_used_them_up_to_now_last_usage_date,
                                    words_and_the_developers_used_them_up_to_now_all_usage_dates,
                                    option2_w,
                                    option4_idf,
                                    option5_prioritize_pas,
                                    option8_recency,
                                    indentation_level + 5,
                                    None,
                                )

                            previous_assignees_of_this_bug_and_their_ranks = real_assignees.get(a.bug_number)
                            if previous_assignees_of_this_bug_and_their_ranks is not None:
                                for login in previous_assignees_of_this_bug_and_their_ranks:
                                    previous_assignees_of_this_bug_and_their_ranks[login] = -1
                            else:
                                previous_assignees_of_this_bug_and_their_ranks = {}
                                real_assignees[a.bug_number] = previous_assignees_of_this_bug_and_their_ranks
                            previous_assignees_of_this_bug_and_their_ranks[a.login] = -1

                            ra = update_rank_of_real_assignees_and_return_the_best_assignee(
                                real_assignees, a.bug_number, scores, rnd
                            )

                            if general_experiment_type in {
                                ExperimentType.JUST_CALCULATE_ORIGINAL_TF_IDF,
                                ExperimentType.JUST_CALCULATE_TIME_TF_IDF,
                            }:
                                for k in range(wac.size):
                                    word = wac.words[k]
                                    developers_last_usage_date = words_and_the_developers_used_them_up_to_now_last_usage_date.setdefault(word, {})
                                    developers_last_usage_date[a.login] = a.date

                            if general_experiment_type == ExperimentType.JUST_CALCULATE_TIME_TF_IDF2:
                                for k in range(wac.size):
                                    word = wac.words[k]
                                    developers_all_usage_dates = words_and_the_developers_used_them_up_to_now_all_usage_dates.setdefault(word, {})
                                    dates = developers_all_usage_dates.setdefault(a.login, set())
                                    dates.add(a.date)

                            assignment_stat = AssignmentStat(
                                bug_number=a.bug_number,
                                date=a.date,
                                login=ra.login,
                                rank=ra.rank or -1,
                                real_assignees_ranks=real_assignees[a.bug_number].copy(),
                            )
                            projects_and_their_assignment_stats.setdefault(project_id, []).append(assignment_stat)

                            number_of_bugs_processed += 1
                            if show_progress_interval and number_of_bugs_processed % show_progress_interval == 0:
                                print(f"{indent(indentation_level+5)}{number_of_bugs_processed} bug assignments ...")
                            if test_or_real == THIS_IS_A_TEST and j >= test_or_real:
                                break
                            if total_fmr.errors > 0:
                                print(f"{indent(indentation_level+3)}There are errors! Breaking ...")
                                print(f"{indent(indentation_level+3)}ERROR DETAILS: {total_fmr.errors} error(s) during processing")
                                print(f"{indent(indentation_level+3)}Processed: {total_fmr.processed}, Done successfully: {total_fmr.done_successfully}")
                                break
                            previous_assignees_in_this_project.add(a.login)

                        print(f"{indent(indentation_level+5)}{number_of_bugs_processed} bug assignments predicted.")
                        project_counter += 1
                        if test_or_real == THIS_IS_A_TEST:
                            break
                        if wrap_output_in_lines:
                            print(f"{indent(indentation_level+4)}-----------------------------------")
            print(f"{indent(indentation_level+4)}Finished.")
            if wrap_output_in_lines:
                print(f"{indent(indentation_level+3)}-----------------------------------")

            d7 = datetime.now()
            total_running_time_for_this_assignment_type_in_the_loop = (d7 - d4).total_seconds()
            debug_msg = (
                f"[DEBUG-7.5] Before write_assignment_stats: "
                f"len(projects_and_their_assignment_stats)={len(projects_and_their_assignment_stats)}, "
                f"len(project_names_and_their_ids_ordered_by_name)={len(project_names_and_their_ids_ordered_by_name)}, "
                f"sample_project_ids={list(projects_and_their_assignment_stats.keys())[:5]}, "
                f"sample_projects_by_name={list(project_names_and_their_ids_ordered_by_name.items())[:5]}"
            )
            debug_log_file.write(debug_msg + "\n")
            print(debug_msg)
            if projects_and_their_assignment_stats:
                sample_stats = [
                    (project_id, len(stats))
                    for project_id, stats in list(projects_and_their_assignment_stats.items())[:5]
                ]
                debug_msg2 = f"[DEBUG-7.5] sample assignment counts per project: {sample_stats}"
                debug_log_file.write(debug_msg2 + "\n")
                print(debug_msg2)
            write_assignment_stats(
                output_path,
                output_summaries_tsv_file_name,
                ASSIGNMENT_RESULTS_OVERAL_FOLDER_NAME,
                detailed_assignment_results_subfolder_name,
                ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS[i],
                projects_and_their_assignment_stats,
                project_names_and_their_ids_ordered_by_name,
                projects_and_their_communities,
                experiment_details,
                local_fmr,
                total_running_time_for_this_assignment_type_in_the_loop,
                wrap_output_in_lines,
                show_progress_interval * 100,
                indentation_level + 3,
                concat_two_write_message_steps(write_message_step, f"{step}-5"),
            )
            total_fmr = io_utils.add_file_manipulation_results(total_fmr, local_fmr)
            debug_msg = f"[DEBUG-9] After writing assignment stats (assignment_type={i}): errors={total_fmr.errors}, done_successfully={total_fmr.done_successfully}, processed={total_fmr.processed}"
            debug_log_file.write(debug_msg + "\n")
            print(debug_msg)
            if total_fmr.errors > 0:
                print(f"{indent(indentation_level+3)}There are errors! Breaking ...")
                break
            print(f"{indent(indentation_level+3)}Finished.")
            if wrap_output_in_lines:
                print(f"{indent(indentation_level+2)}-----------------------------------")

        if total_fmr.errors == 0:
            print(f"{indent(indentation_level+2)}Finished.")
        else:
            print(f"{indent(indentation_level+3)}There are errors! Process stopped!")
        print(f"{indent(indentation_level+2)}Finished.")
        if wrap_output_in_lines:
            print(f"{indent(indentation_level+1)}-----------------------------------")

    d8 = datetime.now()
    total_loop_time = (d8 - d3).total_seconds()
    net_assignment_time = total_loop_time - loop_extra_time_reading_communities - loop_extra_time_reading_assignment_evidence_indexing

    if total_fmr.errors == 0:
        print(f"{indent(indentation_level+1)}Finished.")
    else:
        print(f"{indent(indentation_level+1)}Finished with {total_fmr.errors} critical errors handling i/o files.")
        print(f"{indent(indentation_level+1)}ERRORS! ERRORS! ERRORS!")
        fmr.errors = total_fmr.errors

    print(f"{indent(indentation_level)}-----------------------------------")
    print(f"Summary (time, etc.):")
    print(f"{indent(indentation_level)}Total time: {total_loop_time:.2f} seconds.")
    print(f"{indent(indentation_level+1)}Initial time (Reading graph, bug and project info, before the loop): {initial_extra_time_reading_graph_bugs_and_projects_info:.2f}")
    print(f"{indent(indentation_level+1)}Initial time (Reading assignments, and, reading and indexing non-assignment evidence, before the loop): {initial_extra_time_reading_assignments_and_reading_and_indexing_non_assignment_evidence:.2f}")
    print(f"{indent(indentation_level+1)}Whole loop time: {total_loop_time:.2f} seconds.")
    print(f"{indent(indentation_level+2)}Reading communities files (in the loop): {loop_extra_time_reading_communities:.2f}")
    print(f"{indent(indentation_level+2)}Reading bugs and indexing extra time (in the loop): {loop_extra_time_reading_assignment_evidence_indexing:.2f}")
    print(f"{indent(indentation_level+2)}Net assignment time (in the loop): {net_assignment_time:.2f} seconds.")
    print(f"{indent(indentation_level)}-----------------------------------")
    print(f"{indent(indentation_level)}-----------------------------------")
    
    # Close debug log file
    debug_log_file.close()


def experiment(
    general_experiment_type: ExperimentType,
    input_dir: str,
    node_weights_input_path: str,
    node_weights_input_file: str,
    additional_node_weights_input_path: str,
    additional_node_weights_input_file_name_prefix: str,
    output_path: str,
    is_main_run: bool = True,
    developer_filteration_threshold_least_number_of_bugs_to_fix_to_be_considered: int = 1,
    wrap_output_in_lines: bool = False,
    show_progress_interval: int = 5000,
    indentation_level: int = 0,
) -> None:
    assignment_types_to_triage = [0, 0, 0, 0, 1]
    evidence_types = [1, 0, 0, 0, 0, 0]
    total_evidence_types_count = 6

    option1 = BTOption1WhatToAddToAllBugs.ADD_ML
    option2 = BTOption2W.NO_TERM_WEIGHTING
    option3 = BTOption3TF.FREQ__TOTAL_NUMBER_OF_TERMS
    option4 = BTOption4IDF.FREQ
    option5 = BTOption5PrioritizePAs.PRIORITY_FOR_PREVIOUS_ASSIGNEES
    option6 = BTOption6WhatToAddToAllCommits.JUST_USE_COMMIT_M
    option7 = BTOption7WhenToCountTextLength.USE_TEXT_LENGTH_BEFORE_REMOVING_NON_SO_TAGS
    option8 = BTOption8Recency.RECENCY2

    assigned_bug_and_used_bug_as_evidence_text = "bTD"
    if evidence_types[0] == 1:
        if option1 in {BTOption1WhatToAddToAllBugs.ADD_PTD, BTOption1WhatToAddToAllBugs.ADD_PTD_ML}:
            assigned_bug_and_used_bug_as_evidence_text += "pTD"
        if option1 in {BTOption1WhatToAddToAllBugs.ADD_ML, BTOption1WhatToAddToAllBugs.ADD_PTD_ML}:
            assigned_bug_and_used_bug_as_evidence_text += "mL"
    used_commit_as_evidence_text = "c"
    if evidence_types[1] == 1:
        if option6 in {BTOption6WhatToAddToAllCommits.ADD_PTD, BTOption6WhatToAddToAllCommits.ADD_PTD_ML}:
            used_commit_as_evidence_text += "pTD"
        if option6 in {BTOption6WhatToAddToAllCommits.ADD_ML, BTOption6WhatToAddToAllCommits.ADD_PTD_ML}:
            used_commit_as_evidence_text += "mL"

    methodology = general_experiment_type.name
    if option2 == BTOption2W.NO_TERM_WEIGHTING:
        methodology += "+noW"
    else:
        methodology += "+w__"
    if option3 == BTOption3TF.ONE:
        methodology += "+TF_one"
    elif option3 == BTOption3TF.FREQ:
        methodology += "+TF_fre"
    elif option3 == BTOption3TF.FREQ__TOTAL_NUMBER_OF_TERMS:
        methodology += "+TF_F_T"
    elif option3 == BTOption3TF.LOG_BASED:
        methodology += "+TF_Log"
    if option4 == BTOption4IDF.ONE:
        methodology += "+IDF_one"
    elif option4 == BTOption4IDF.FREQ:
        methodology += "+IDF_fre"
    elif option4 == BTOption4IDF.FREQ__TOTAL_NUMBER_OF_TERMS:
        methodology += "+IDF_F_T"
    elif option4 == BTOption4IDF.LOG_BASED:
        methodology += "+IDF_log"
    if option5 == BTOption5PrioritizePAs.NO_PRIORITY:
        methodology += "+noP"
    else:
        methodology += "+pri"
    if option7 == BTOption7WhenToCountTextLength.USE_TEXT_LENGTH_BEFORE_REMOVING_NON_SO_TAGS:
        methodology += "+tL_b"
    else:
        methodology += "+tL_a"
    if option8 == BTOption8Recency.NO_RECENCY:
        methodology += "+nR"
    elif option8 == BTOption8Recency.RECENCY1:
        methodology += "+r1"
    else:
        methodology += "+r2"

    evidence_types_text = [
        assigned_bug_and_used_bug_as_evidence_text,
        used_commit_as_evidence_text,
        "p",
        "bc",
        "cC",
        "pC",
    ]
    experiment_title = "+".join(
        evidence_types_text[index] for index in range(total_evidence_types_count) if evidence_types[index] == 1
    )
    experiment_title = f"{assigned_bug_and_used_bug_as_evidence_text} - {experiment_title} - {methodology}"

    fmr = FileManipulationResult()
    bug_assignment(
        input_dir,
        node_weights_input_path,
        node_weights_input_file,
        additional_node_weights_input_path,
        additional_node_weights_input_file_name_prefix,
        output_path,
        "outSum",
        is_main_run,
        assignment_types_to_triage,
        evidence_types,
        total_evidence_types_count,
        experiment_title,
        "-",
        option1,
        option2,
        option3,
        option4,
        option5,
        option6,
        option7,
        option8,
        general_experiment_type,
        developer_filteration_threshold_least_number_of_bugs_to_fix_to_be_considered,
        fmr,
        wrap_output_in_lines,
        show_progress_interval,
        indentation_level,
        THIS_IS_REAL,
        "",
    )
    if fmr.errors > 0:
        print("Error in experiment()!")


if __name__ == "__main__":
    experiment(
        general_experiment_type=ExperimentType.COMMIT_WORD2VEC,
        input_dir=DATASET_DIRECTORY_FOR_THE_ALGORITHM__GH__EXPERIMENT_TFIDF,
        node_weights_input_path=DATASET_DIRECTORY_FOR_THE_ALGORITHM__SO__EXPERIMENT,
        node_weights_input_file="nodeWeights.tsv",
        additional_node_weights_input_path=DATASET_DIRECTORY_FOR_THE_ALGORITHM__GH__EXPERIMENT_MAIN,
        additional_node_weights_input_file_name_prefix="nodeWeights3-sourceCode-",
        output_path=DATASET_DIRECTORY_FOR_THE_ALGORITHM__EXPERIMENT_OUTPUT,
        is_main_run=True,
    )
