from __future__ import annotations

import math
import re
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import w2v_utils
from constants import (
    ALL,
    BTOption1WhatToAddToAllBugs,
    BTOption2W,
    BTOption3TF,
    BTOption4IDF,
    BTOption5PrioritizePAs,
    BTOption6WhatToAddToAllCommits,
    BTOption7WhenToCountTextLength,
    BTOption8Recency,
    ExperimentType,
    SEQ_NUM____NO_NEED_TO_TRIAGE_THIS_TYPE___OR___THIS_IS_NOT__NON_B_A_EVIDENCE,
    SEQ_NUM____THIS_IS_NOT__B_A_EVIDENCE,
    TAGS_SEPARATOR,
    allValidCharactersInSOURCECODE_Strict_ForRegEx,
    TAB,
)
from io_utils import FileManipulationResult
from models import Assignment, Bug, Evidence, EvidenceType, Project

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
NUMBER_OF_ASSIGNEE_TYPES = 5
AN_EXTREMELY_POSITIVE_INT = 2_147_483_647


class CommitRecord:
    def __init__(self, sha: str, user: str, date: datetime, tag_scores: Dict[str, float]):
        self.sha = sha
        self.user = user
        self.date = date
        self.tag_scores = tag_scores


def indent(level: int) -> str:
    return " " * (4 * level)


def parse_datetime(date_str: str) -> datetime:
    return datetime.strptime(date_str, DATE_FORMAT)


def get_difference_in_days(d1: datetime, d2: datetime) -> int:
    return abs((d2 - d1).days)


def special_binary_search2(assignments: Sequence[Sequence[str]], index_of_date_field: int, key: str) -> int:
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


def get_main_languages(main_languages_percentages: str) -> Tuple[str, int]:
    if main_languages_percentages is None or main_languages_percentages == "[]":
        return "", 0
    items = main_languages_percentages[1:-1].split(";;")
    result = " ".join(item.split("^")[0] for item in items if "^" in item)
    return result, len(items)


def get_bug_text(
    project: Project,
    bug: Bug,
    original_number_of_words_in_text_array: List[int],
    option1: BTOption1WhatToAddToAllBugs,
) -> str:
    if option1 == BTOption1WhatToAddToAllBugs.ADD_PTD:
        original_number_of_words_in_text_array[0] = (bug.title_number_of_words or 0) + (bug.body_number_of_words or 0) + (project.description_number_of_words or 0)
        return f"{bug.title or ''} {bug.body or ''} {project.description or ''}".replace("  ", " ").strip()
    if option1 == BTOption1WhatToAddToAllBugs.ADD_ML:
        if project.main_language_percentages == "[]":
            original_number_of_words_in_text_array[0] = (bug.title_number_of_words or 0) + (bug.body_number_of_words or 0)
            return f"{bug.title or ''} {bug.body or ''}".replace("  ", " ").strip()
        main_languages, main_language_count = get_main_languages(project.main_language_percentages)
        original_number_of_words_in_text_array[0] = (bug.title_number_of_words or 0) + (bug.body_number_of_words or 0) + main_language_count
        return f"{bug.title or ''} {bug.body or ''} {main_languages}".replace("  ", " ").strip()
    if option1 == BTOption1WhatToAddToAllBugs.ADD_PTD_ML:
        if project.main_language_percentages == "[]":
            original_number_of_words_in_text_array[0] = (bug.title_number_of_words or 0) + (bug.body_number_of_words or 0) + (project.description_number_of_words or 0)
            return f"{bug.title or ''} {bug.body or ''} {project.description or ''}".replace("  ", " ").strip()
        main_languages, main_language_count = get_main_languages(project.main_language_percentages)
        original_number_of_words_in_text_array[0] = (
            (bug.title_number_of_words or 0)
            + (bug.body_number_of_words or 0)
            + (project.description_number_of_words or 0)
            + main_language_count
        )
        return f"{bug.title or ''} {bug.body or ''} {project.description or ''} {main_languages}".replace("  ", " ").strip()
    original_number_of_words_in_text_array[0] = (bug.title_number_of_words or 0) + (bug.body_number_of_words or 0)
    return f"{bug.title or ''} {bug.body or ''}".replace("  ", " ").strip()


def get_commit_text(
    project: Project,
    commit_message: str,
    original_number_of_words_in_text_array: List[int],
    option6: BTOption6WhatToAddToAllCommits,
) -> str:
    if option6 == BTOption6WhatToAddToAllCommits.ADD_PTD:
        original_number_of_words_in_text_array[0] = (original_number_of_words_in_text_array[0] or 0) + (project.description_number_of_words or 0)
        return f"{commit_message or ''} {project.description or ''}".replace("  ", " ").strip()
    if option6 == BTOption6WhatToAddToAllCommits.ADD_ML:
        if project.main_language_percentages == "[]":
            return commit_message
        main_languages, main_language_count = get_main_languages(project.main_language_percentages)
        original_number_of_words_in_text_array[0] = (original_number_of_words_in_text_array[0] or 0) + main_language_count
        return f"{commit_message or ''} {main_languages}".replace("  ", " ").strip()
    if option6 == BTOption6WhatToAddToAllCommits.ADD_PTD_ML:
        if project.main_language_percentages == "[]":
            original_number_of_words_in_text_array[0] = (original_number_of_words_in_text_array[0] or 0) + (project.description_number_of_words or 0)
            return f"{commit_message or ''} {project.description or ''}".replace("  ", " ").strip()
        main_languages, main_language_count = get_main_languages(project.main_language_percentages)
        original_number_of_words_in_text_array[0] = (
            (original_number_of_words_in_text_array[0] or 0)
            + (project.description_number_of_words or 0)
            + main_language_count
        )
        return f"{commit_message or ''} {project.description or ''} {main_languages}".replace("  ", " ").strip()
    return commit_message or ""


def _should_index_word(word: str, general_experiment_type: ExperimentType, graph: Any, graphs: Sequence[Any], project_index: int) -> bool:
    if not word:
        return False
    if general_experiment_type == ExperimentType.CALCULATE_OUR_METRIC__TTBA:
        return graph.has_node(word)
    if general_experiment_type in {
        ExperimentType.JUST_CALCULATE_ORIGINAL_TF_IDF,
        ExperimentType.JUST_CALCULATE_TIME_TF_IDF,
        ExperimentType.JUST_CALCULATE_TIME_TF_IDF2,
        ExperimentType.CALCULATE_TBA,
        ExperimentType.CALCULATE_VTBA_GH,
    }:
        return True
    if general_experiment_type == ExperimentType.CALCULATE_VTBA_GH__CALCULATE_WEIGHS_ONLINE:
        return True
    if general_experiment_type != ExperimentType.CALCULATE_VTBA_SOURCECODE:
        return graph.has_node(word)
    return graphs[project_index].has_node(word)


def _create_word2vec_score(word: str, so_tags: Optional[List[str]]) -> float:
    if not so_tags:
        return 0.0
    total = 0.0
    for tag in so_tags:
        total += w2v_utils.get_similarity(word, tag)
    return total


def add_to_index(
    evidence_text: str,
    evidence_type: int,
    seq_num: int,
    virtual_seq_num: List[int],
    original_number_of_words_in_the_text: int,
    graph: Any,
    graphs: Sequence[Any],
    project_id: str,
    project_name: str,
    login: str,
    date: str,
    project_id_login_tags_types_and_their_evidence: Dict[str, Dict[str, Dict[str, Dict[int, List[Evidence]]]]],
    option3_tf: BTOption3TF,
    option7_when_to_count_text_length: BTOption7WhenToCountTextLength,
    general_experiment_type: ExperimentType,
    fmr: FileManipulationResult,
    so_tags: Optional[List[str]] = None,
) -> None:
    words = evidence_text.split(" ")
    for j, word in enumerate(words):
        if not word:
            continue
        if not _should_index_word(word, general_experiment_type, graph, graphs, 0):
            continue
        if general_experiment_type == ExperimentType.CALCULATE_TBA and re.match(r"^[0-9].*", word):
            continue

        login_data = project_id_login_tags_types_and_their_evidence.setdefault(project_id, {})
        tags_types = login_data.setdefault(login, {})
        type_map = tags_types.setdefault(word, {})
        evidence_list = type_map.setdefault(evidence_type, [])

        freq = 1
        for k in range(j + 1, len(words)):
            if words[k] == word:
                freq += 1
                words[k] = ""

        number_of_words_in_text = (
            original_number_of_words_in_the_text
            if option7_when_to_count_text_length == BTOption7WhenToCountTextLength.USE_TEXT_LENGTH_BEFORE_REMOVING_NON_SO_TAGS
            else len(words)
        )

        tf = 1.0
        if option3_tf == BTOption3TF.FREQ:
            tf = float(freq)
        elif option3_tf == BTOption3TF.FREQ__TOTAL_NUMBER_OF_TERMS:
            tf = float(freq) / number_of_words_in_text if number_of_words_in_text else 0.0
        elif option3_tf == BTOption3TF.LOG_BASED:
            tf = 1.0 + math.log10(freq)

        try:
            evidence = Evidence(
                date=parse_datetime(date),
                b_a_seq_num=seq_num,
                non_ba_virtual_seq_num=list(virtual_seq_num),
                freq=freq,
                total_number_of_words_in_this_evidence=number_of_words_in_text,
                tf=tf,
            )
            evidence.word2vec_tf_score = _create_word2vec_score(word, so_tags)
            evidence_list.append(evidence)
        except ValueError:
            fmr.errors += 1


def index_assignment_evidence(
    evidence_type: int,
    projects_and_their_assignments: Dict[str, List[List[str]]],
    projects: Dict[str, Any],
    project_id_bug_number_and_their_bug_info: Dict[str, Any],
    project_id_login_tags_types_and_their_evidence: Dict[str, Dict[str, Dict[str, Dict[int, List[Evidence]]]]],
    graph: Any,
    graphs: Sequence[Any],
    fmr: FileManipulationResult,
    option1: BTOption1WhatToAddToAllBugs,
    option2_w: BTOption2W,
    option3_tf: BTOption3TF,
    option4_idf: BTOption4IDF,
    option5_prioritize_pas: BTOption5PrioritizePAs,
    option6_what_to_add_to_all_commits: BTOption6WhatToAddToAllCommits,
    option7_when_to_count_text_length: BTOption7WhenToCountTextLength,
    general_experiment_type: ExperimentType,
    wrap_output_in_lines: bool,
    show_progress_interval: int,
    indentation_level: int,
    write_message_step: str,
) -> None:
    if wrap_output_in_lines:
        print("-----------------------------------", end="\n")
    print(f"{indent(indentation_level)}{write_message_step} - Iterating over assignment evidence of type '{evidence_type}' and adding them to the evidence index:")
    print(f"{indent(indentation_level+1)}Started ...")

    try:
        for project_id, assignments_of_one_project in projects_and_their_assignments.items():
            i = 0
            for fields in assignments_of_one_project:
                bug_number = fields[0]
                date = fields[1]
                login = fields[2]
                bug_info_key = f"{project_id}{TAB}{bug_number}"
                bug_info = project_id_bug_number_and_their_bug_info.get(bug_info_key)
                project_info = projects.get(project_id)
                project_owner_repo = project_info[0] if isinstance(project_info, (list, tuple)) else str(project_info)
                project_name = project_owner_repo.split("/", 1)[1] if "/" in project_owner_repo else project_owner_repo
                project = Project(
                    id=project_id,
                    owner_repo=project_owner_repo,
                    description=project_info[1] if isinstance(project_info, (list, tuple)) and len(project_info) > 1 else "",
                    description_number_of_words=int(project_info[2]) if isinstance(project_info, (list, tuple)) and len(project_info) > 2 else 0,
                    main_language_percentages=project_info[3] if isinstance(project_info, (list, tuple)) and len(project_info) > 3 else "[]",
                )
                bug = Bug(
                    project_id=project_id,
                    number=bug_number,
                    title=bug_info[3] if bug_info and len(bug_info) > 3 else "",
                    title_number_of_words=int(bug_info[4]) if bug_info and len(bug_info) > 4 else 0,
                    body=bug_info[5] if bug_info and len(bug_info) > 5 else "",
                    body_number_of_words=int(bug_info[6]) if bug_info and len(bug_info) > 6 else 0,
                )

                original_number_of_words_in_text_array = [0]
                text = get_bug_text(project, bug, original_number_of_words_in_text_array, option1)
                if general_experiment_type == ExperimentType.CALCULATE_TBA:
                    text = re.sub(allValidCharactersInSOURCECODE_Strict_ForRegEx, " ", text.lower()).strip()
                original_number_of_words_in_text = original_number_of_words_in_text_array[0]

                if len(text) > 2:
                    virtual_seq_num = [SEQ_NUM____NO_NEED_TO_TRIAGE_THIS_TYPE___OR___THIS_IS_NOT__NON_B_A_EVIDENCE] * NUMBER_OF_ASSIGNEE_TYPES
                    add_to_index(
                        text,
                        evidence_type,
                        i + 1,
                        virtual_seq_num,
                        original_number_of_words_in_text,
                        graph,
                        graphs,
                        project_id,
                        project_name,
                        login,
                        date,
                        project_id_login_tags_types_and_their_evidence,
                        option3_tf,
                        option7_when_to_count_text_length,
                        general_experiment_type,
                        fmr,
                    )
                i += 1
                if show_progress_interval and i % show_progress_interval == 0:
                    print(f"{indent(indentation_level+2)}{i}")

            if i > 0:
                print(f"{indent(indentation_level+1)}{project_name} (projectId: {project_id}): expertise of {i} bug assignments indexed.")
            else:
                print(f"{indent(indentation_level+1)}{project_name} (projectId: {project_id}): Warning: Nothing indexed! No bug assignments to index their expertise!")

    except Exception as exc:
        fmr.errors += 1
        print("ERROR!", exc)
    finally:
        print(f"{indent(indentation_level+1)}Finished.")
        if wrap_output_in_lines:
            print("-----------------------------------")


def read_and_index_non_assignment_evidence(
    input_path: str,
    commits_input_file_name: str,
    prs_input_file_name: str,
    bug_comments_input_file_name: str,
    commit_comments_input_file_name: str,
    pr_comments_input_file_name: str,
    projects_and_their_assignments_al_for_different_assignment_types: List[Dict[str, List[List[str]]]],
    assignment_types_to_triage: Dict[int, bool],
    fmr: FileManipulationResult,
    evidence_types: Dict[int, bool],
    projects: Dict[str, Any],
    project_id_bug_number_and_their_bug_info: Dict[str, Any],
    project_id_login_tags_types_and_their_evidence: Dict[str, Dict[str, Dict[str, Dict[int, List[Evidence]]]]],
    graph: Any,
    graphs: Sequence[Any],
    option1: BTOption1WhatToAddToAllBugs,
    option2_w: BTOption2W,
    option3_tf: BTOption3TF,
    option4_idf: BTOption4IDF,
    option5_prioritize_pas: BTOption5PrioritizePAs,
    option6_what_to_add_to_all_commits: BTOption6WhatToAddToAllCommits,
    option7_when_to_count_text_length: BTOption7WhenToCountTextLength,
    general_experiment_type: ExperimentType,
    wrap_output_in_lines: bool,
    show_progress_interval: int,
    indentation_level: int,
    write_message_step: str,
    so_tags: Optional[List[str]] = None,
) -> None:
    if wrap_output_in_lines:
        print("-----------------------------------")
    print(f"{indent(indentation_level)}{write_message_step} - Reading non-assignment evidence in '{commits_input_file_name}' and indexing them:")
    print(f"{indent(indentation_level+1)}Started ...")

    try:
        if evidence_types.get(EvidenceType.COMMIT.value, False) and commits_input_file_name:
            path = Path(input_path) / commits_input_file_name
            with path.open("r", encoding="utf-8") as file:
                next(file, None)
                i = 0
                for line in file:
                    i += 1
                    fields = line.rstrip("\n").split("\t")
                    if len(fields) == 6:
                        _, project_id, committer, date, commit_message, original_number_of_words = fields
                        if committer != " ":
                            project_info = projects.get(project_id)
                            project_owner_repo = project_info[0] if isinstance(project_info, (list, tuple)) else str(project_info)
                            project_name = project_owner_repo.split("/", 1)[1] if "/" in project_owner_repo else project_owner_repo
                            project = Project(
                                id=project_id,
                                owner_repo=project_owner_repo,
                                description=project_info[1] if isinstance(project_info, (list, tuple)) and len(project_info) > 1 else "",
                                description_number_of_words=int(project_info[2]) if isinstance(project_info, (list, tuple)) and len(project_info) > 2 else 0,
                                main_language_percentages=project_info[3] if isinstance(project_info, (list, tuple)) and len(project_info) > 3 else "[]",
                            )
                            original_number_of_words_array = [int(original_number_of_words) if original_number_of_words.isdigit() else 0]
                            text = get_commit_text(project, commit_message, original_number_of_words_array, option6_what_to_add_to_all_commits)
                            original_number_of_words_in_text = original_number_of_words_array[0]
                            virtual_seq_num = [
                                SEQ_NUM____NO_NEED_TO_TRIAGE_THIS_TYPE___OR___THIS_IS_NOT__NON_B_A_EVIDENCE
                            ] * NUMBER_OF_ASSIGNEE_TYPES
                            if len(text) > 2:
                                add_to_index(
                                    text,
                                    EvidenceType.COMMIT.value,
                                    SEQ_NUM____THIS_IS_NOT__B_A_EVIDENCE,
                                    virtual_seq_num,
                                    original_number_of_words_in_text,
                                    graph,
                                    graphs,
                                    project_id,
                                    project_name,
                                    committer,
                                    date,
                                    project_id_login_tags_types_and_their_evidence,
                                    option3_tf,
                                    option7_when_to_count_text_length,
                                    general_experiment_type,
                                    fmr,
                                    so_tags,
                                )
                    else:
                        fmr.errors += 1
                    if show_progress_interval and i % show_progress_interval == 0:
                        print(f"{indent(indentation_level+2)}{i}")

    except Exception as exc:
        print("ERROR!", exc)
        fmr.errors += 1

    print(f"{indent(indentation_level+1)}Finished.")
    if wrap_output_in_lines:
        print("-----------------------------------")


def calculate_score_of_developer_for_bug_assignment(
    login: str,
    assignment: Assignment,
    graph: Any,
    updating_graph: Any,
    assignment_type_to_triage: int,
    evidence_types_to_consider: List[int],
    logins_tags_types_and_their_evidence_in_a_project: Dict[str, Dict[str, Dict[int, List[Evidence]]]],
    previous_assignees_in_this_project: Set[str],
    wac: Any,
    original_number_of_words_in_bug_text: int,
    seq_num: int,
    beginning_date_of_project: datetime,
    general_experiment_type: ExperimentType,
    number_of_community_members: int,
    words_and_the_developers_used_them_up_to_now_last_usage_date: Dict[str, Dict[str, datetime]],
    words_and_the_developers_used_them_up_to_now_all_usage_dates: Dict[str, Dict[str, Set[datetime]]],
    option2_w: BTOption2W,
    option4_idf: BTOption4IDF,
    option5_prioritize_pas: BTOption5PrioritizePAs,
    option8_recency: BTOption8Recency,
    indentation_level: int,
    developer_commit_index: Optional[Dict[str, List[CommitRecord]]],
) -> float:
    score = 0.0
    sub_score = 0.0

    if general_experiment_type in {
        ExperimentType.JUST_CALCULATE_ORIGINAL_TF_IDF,
        ExperimentType.JUST_CALCULATE_TIME_TF_IDF,
        ExperimentType.JUST_CALCULATE_TIME_TF_IDF2,
    }:
        error_A = 0
        developer_data = logins_tags_types_and_their_evidence_in_a_project.get(login, {})
        for i in range(wac.size):
            word = wac.words[i]
            if word not in developer_data:
                continue
            types_and_evidence = developer_data[word]
            for et in evidence_types_to_consider:
                if et not in types_and_evidence:
                    continue
                evidence_list = types_and_evidence[et]
                for e in evidence_list:
                    if e.date < assignment.date:
                        if word in words_and_the_developers_used_them_up_to_now_last_usage_date:
                            developers_last_usage_date = words_and_the_developers_used_them_up_to_now_last_usage_date[word]
                            number_of_developers_used_term = len(developers_last_usage_date)
                            if login in developers_last_usage_date:
                                if general_experiment_type == ExperimentType.JUST_CALCULATE_ORIGINAL_TF_IDF:
                                    sub_score += (
                                        wac.counts[i]
                                        * e.tf
                                        * math.log(number_of_community_members / number_of_developers_used_term)
                                    )
                                else:
                                    if general_experiment_type == ExperimentType.JUST_CALCULATE_TIME_TF_IDF:
                                        day_diff = get_difference_in_days(assignment.date, developers_last_usage_date[login])
                                        if day_diff == 0:
                                            day_diff = 1
                                        recency_for_time_tf_idf = 1.0 / number_of_developers_used_term + 1.0 / math.sqrt(day_diff)
                                        sub_score += (
                                            recency_for_time_tf_idf
                                            * wac.counts[i]
                                            * e.tf
                                            * math.log(number_of_community_members / number_of_developers_used_term)
                                        )
                            else:
                                error_A += 1
                                break
                        elif word in words_and_the_developers_used_them_up_to_now_all_usage_dates:
                            developers_all_usage_dates = words_and_the_developers_used_them_up_to_now_all_usage_dates[word]
                            number_of_developers_used_term = len(developers_all_usage_dates)
                            if login in developers_all_usage_dates:
                                if general_experiment_type == ExperimentType.JUST_CALCULATE_TIME_TF_IDF2:
                                    recency_for_time_tf_idf = 1.0 / number_of_developers_used_term
                                    all_usage_dates = developers_all_usage_dates[login]
                                    for d in all_usage_dates:
                                        day_diff = get_difference_in_days(assignment.date, d)
                                        if day_diff == 0:
                                            day_diff = 1
                                        recency_for_time_tf_idf += 1.0 / math.sqrt(day_diff)
                                    sub_score += (
                                        recency_for_time_tf_idf
                                        * wac.counts[i]
                                        * e.tf
                                        * math.log(number_of_community_members / number_of_developers_used_term)
                                    )
                            else:
                                error_A += 1
                                break
                        else:
                            error_A += 1
                            break
        if error_A > 0:
            print(f"{error_A} ERRORS-A in calculate_score_of_developer_for_bug_assignment(): the word entry is missing for calculating idf!")
        score = sub_score
        if option5_prioritize_pas == BTOption5PrioritizePAs.PRIORITY_FOR_PREVIOUS_ASSIGNEES and login in previous_assignees_in_this_project:
            score += 10000
        return score

    if general_experiment_type != ExperimentType.COMMIT_WORD2VEC:
        errors1 = 0
        errors2 = 0
        errors3_possibly = 0
        errors4_both_are_one = 0
        developer_data = logins_tags_types_and_their_evidence_in_a_project.get(login, {})
        assignment_date = assignment.date
        for i in range(wac.size):
            word = wac.words[i]
            if word not in developer_data:
                continue
            types_and_evidence = developer_data[word]
            term_weight = updating_graph.get_node_weight(word) if general_experiment_type == ExperimentType.CALCULATE_VTBA_GH__CALCULATE_WEIGHS_ONLINE else graph.get_node_weight(word)
            sub_score = 0.0
            for et in evidence_types_to_consider:
                if et not in types_and_evidence:
                    continue
                evidence_list = types_and_evidence[et]
                for e in evidence_list:
                    if e.date < assignment_date:
                        evidence_date = e.date
                        recency2 = 1.0
                        if et < NUMBER_OF_ASSIGNEE_TYPES:
                            if e.b_a_seq_num >= seq_num:
                                errors1 += 1
                            if option8_recency == BTOption8Recency.RECENCY2:
                                recency2 = 1.0 / (seq_num - e.b_a_seq_num)
                        else:
                            if e.non_ba_virtual_seq_num[assignment_type_to_triage] > seq_num:
                                errors2 += 1
                            if e.non_ba_virtual_seq_num[assignment_type_to_triage] == seq_num:
                                errors3_possibly += 1
                                if seq_num == 1:
                                    errors4_both_are_one += 1
                            if option8_recency == BTOption8Recency.RECENCY2:
                                recency2 = 1.0 / (seq_num - e.non_ba_virtual_seq_num[assignment_type_to_triage])

                        if option8_recency == BTOption8Recency.NO_RECENCY:
                            sub_score += e.tf
                        elif option8_recency == BTOption8Recency.RECENCY1:
                            recency1 = (
                                (evidence_date - beginning_date_of_project).total_seconds()
                                / (assignment_date - beginning_date_of_project).total_seconds()
                            )
                            sub_score += e.tf * recency1
                        elif option8_recency == BTOption8Recency.RECENCY2:
                            sub_score += e.tf * recency2
                    else:
                        break
            if option2_w == BTOption2W.NO_TERM_WEIGHTING:
                if option4_idf == BTOption4IDF.ONE:
                    score += sub_score
                elif option4_idf == BTOption4IDF.FREQ:
                    score += sub_score * wac.counts[i]
                elif option4_idf == BTOption4IDF.FREQ__TOTAL_NUMBER_OF_TERMS:
                    score += sub_score * wac.counts[i] / wac.total_number_of_words
                elif option4_idf == BTOption4IDF.LOG_BASED:
                    score += sub_score * (1 + math.log10(wac.counts[i]))
            else:
                if option4_idf == BTOption4IDF.ONE:
                    score += sub_score * term_weight
                elif option4_idf == BTOption4IDF.FREQ:
                    score += sub_score * term_weight * wac.counts[i]
                elif option4_idf == BTOption4IDF.FREQ__TOTAL_NUMBER_OF_TERMS:
                    score += sub_score * term_weight * wac.counts[i] / wac.total_number_of_words
                elif option4_idf == BTOption4IDF.LOG_BASED:
                    score += sub_score * term_weight * (1 + math.log10(wac.counts[i]))

        if errors1 > 0:
            print(f"{errors1} ERRORS1 in seqNum1: The sequence number of the assignment evidence is greater than the sequence number of the bug!")
        if errors2 > 0:
            print(f"{errors2} ERRORS2 in seqNum2: The sequence number of the non-assignment evidence is greater than the sequence number of the bug!")
        if errors3_possibly > 0:
            print(f"{errors3_possibly} Possible ERRORS3 in seqNum2: The sequence number of the non-assignment evidence is equal to the sequence number of the bug!")
        if errors4_both_are_one > 0:
            print(f"{errors4_both_are_one} Possible ERRORS4 in seqNum2: The sequence number of the non-assignment evidence is equal to the sequence number of the bug and both are equal to 1!")
        if (errors1 or errors2 or errors3_possibly or errors4_both_are_one) > 0:
            print("ERROR")
        if option5_prioritize_pas == BTOption5PrioritizePAs.PRIORITY_FOR_PREVIOUS_ASSIGNEES and login in previous_assignees_in_this_project:
            score += 10000
        return score

    if general_experiment_type == ExperimentType.COMMIT_WORD2VEC:
        if developer_commit_index and login in developer_commit_index:
            commits = developer_commit_index[login]
            commits_before_bug = [cr for cr in commits if cr.date < assignment.date]
            if commits_before_bug:
                earliest_date = commits_before_bug[0].date
                period_days = get_difference_in_days(assignment.date, earliest_date)
                avg_commits_per_period = len(commits_before_bug) / max(1, period_days)
                if avg_commits_per_period == 0.0:
                    avg_commits_per_period = 1.0
                for i in range(wac.size):
                    tag = wac.words[i]
                    term_weight = graph.get_node_weight(tag)
                    tag_agg_score = 0.0
                    for j, cr in enumerate(commits_before_bug):
                        commits_after = len(commits_before_bug) - 1 - j
                        recency = 1.0 / (1.0 + commits_after / avg_commits_per_period)
                        tag_agg_score += cr.tag_scores.get(tag, 0.0) * recency
                    score += wac.counts[i] * term_weight * tag_agg_score
                if option5_prioritize_pas == BTOption5PrioritizePAs.PRIORITY_FOR_PREVIOUS_ASSIGNEES and login in previous_assignees_in_this_project:
                    score += 10000
        return score

    return score
