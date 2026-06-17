from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional


class ProjectType(Enum):
    FASE_3__NO_PUBLIC_BUGS = "FASE_3__NO_PUBLIC_BUGS"
    FASE_13_EXTENSION__PROJECT_FAMILIES_OF_TWO_PROJECTS = "FASE_13_EXTENSION__PROJECT_FAMILIES_OF_TWO_PROJECTS"
    FASE_13 = "FASE_13"
    OTHERS_UNKNOWN = "OTHERS_UNKNOWN"


class SortOrder(Enum):
    ASCENDING_INTEGER = "ASCENDING_INTEGER"
    DESCENDING_INTEGER = "DESCENDING_INTEGER"
    DEFAULT_FOR_STRING = "DEFAULT_FOR_STRING"


class FieldType(Enum):
    LONG = "LONG"
    STRING = "STRING"
    NOT_IMPORTANT = "NOT_IMPORTANT"


class LogicalOperation(Enum):
    NO_CONDITION = "NO_CONDITION"
    AND = "AND"
    OR = "OR"
    IGNORE_THE_SECOND_OPERAND = "IGNORE_THE_SECOND_OPERAND"


class ConditionType(Enum):
    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    NOTHING = "NOTHING"
    GREATER_OR_EQUAL = "GREATER_OR_EQUAL"


class JoinType(Enum):
    INNER_JOIN = "INNER_JOIN"
    LEFT_JOIN = "LEFT_JOIN"
    RIGHT_JOIN = "RIGHT_JOIN"
    FULL_JOIN = "FULL_JOIN"


class AssignmentType(Enum):
    T1_AUTHOR = "T1_AUTHOR"
    T2_COAUTHOR = "T2_COAUTHOR"
    T3_ADMIN_CLOSER = "T3_ADMIN_CLOSER"
    T4_DRAFTED_A = "T4_DRAFTED_A"
    T5_ALL_TYPES = "T5_ALL_TYPES"


class EvidenceType(Enum):
    ASSIGNMENT_T1_AUTHOR = 0
    ASSIGNMENT_T2_COAUTHOR = 1
    ASSIGNMENT_T3_ADMIN_CLOSER = 2
    ASSIGNMENT_T4_DRAFTED_A = 3
    ASSIGNMENT_T5_ALL_TYPES = 4
    COMMIT = 11
    PR = 12
    BUG_COMMENT = 13
    COMMIT_COMMENT = 14
    PR_COMMENT = 15


class BTOption1WhatToAddToAllBugs(Enum):
    JUST_USE_BUG_TD = "JUST_USE_BUG_TD"
    ADD_PTD = "ADD_PTD"
    ADD_ML = "ADD_ML"
    ADD_PTD_ML = "ADD_PTD_ML"


class BTOption2W(Enum):
    NO_TERM_WEIGHTING = "NO_TERM_WEIGHTING"
    USE_TERM_WEIGHTING = "USE_TERM_WEIGHTING"


class BTOption3TF(Enum):
    ONE = "ONE"
    FREQ = "FREQ"
    FREQ__TOTAL_NUMBER_OF_TERMS = "FREQ__TOTAL_NUMBER_OF_TERMS"
    LOG_BASED = "LOG_BASED"


class BTOption4IDF(Enum):
    ONE = "ONE"
    FREQ = "FREQ"
    FREQ__TOTAL_NUMBER_OF_TERMS = "FREQ__TOTAL_NUMBER_OF_TERMS"
    LOG_BASED = "LOG_BASED"


class BTOption5PrioritizePAs(Enum):
    NO_PRIORITY = "NO_PRIORITY"
    PRIORITY_FOR_PREVIOUS_ASSIGNEES = "PRIORITY_FOR_PREVIOUS_ASSIGNEES"


class BTOption6WhatToAddToAllCommits(Enum):
    JUST_USE_COMMIT_M = "JUST_USE_COMMIT_M"
    ADD_PTD = "ADD_PTD"
    ADD_ML = "ADD_ML"
    ADD_PTD_ML = "ADD_PTD_ML"


class BTOption7WhenToCountTextLength(Enum):
    USE_TEXT_LENGTH_BEFORE_REMOVING_NON_SO_TAGS = "USE_TEXT_LENGTH_BEFORE_REMOVING_NON_SO_TAGS"
    USE_TEXT_LENGTH_AFTER_REMOVING_NON_SO_TAGS = "USE_TEXT_LENGTH_AFTER_REMOVING_NON_SO_TAGS"


class BTOption8Recency(Enum):
    NO_RECENCY = "NO_RECENCY"
    RECENCY1 = "RECENCY1"
    RECENCY2 = "RECENCY2"


class ExperimentType(Enum):
    CALCULATE_OUR_METRIC__TTBA = "CALCULATE_OUR_METRIC__TTBA"
    JUST_CALCULATE_ORIGINAL_TF_IDF = "JUST_CALCULATE_ORIGINAL_TF_IDF"
    JUST_CALCULATE_TIME_TF_IDF = "JUST_CALCULATE_TIME_TF_IDF"
    JUST_CALCULATE_TIME_TF_IDF2 = "JUST_CALCULATE_TIME_TF_IDF2"
    COMMIT_WORD2VEC = "COMMIT_WORD2VEC"
    CALCULATE_TBA = "CALCULATE_TBA"
    CALCULATE_VTBA_GH = "CALCULATE_VTBA_GH"
    CALCULATE_VTBA_GH__CALCULATE_WEIGHS_ONLINE = "CALCULATE_VTBA_GH__CALCULATE_WEIGHS_ONLINE"
    CALCULATE_VTBA_SOURCECODE = "CALCULATE_VTBA_SOURCECODE"


DATASET_OVERAL_DIRECTORY: str = "C:/2-Study/BugTriaging2/Data Set/Main"
DATASET_DIRECTORY_GH_JSON: str = DATASET_OVERAL_DIRECTORY + "/GH/AtLeastUpTo20161001/1-JSON"
DATASET_DIRECTORY_GH_2_TSV: str = DATASET_OVERAL_DIRECTORY + "/GH/AtLeastUpTo20161001/2-TSV/3- 16 projects + 2 project families (13 + 3 + 6 more projects)"
DATASET_DIRECTORY_GH_3_TSV: str = DATASET_OVERAL_DIRECTORY + "/GH/AtLeastUpTo20161001/3-TSV-Cleaned"
DATASET_DIRECTORY_GH_3_TSV_OUTPUT: str = DATASET_OVERAL_DIRECTORY + "/GH/AtLeastUpTo20161001/3-TSV-Cleaned/Output"
TOTAL_NUMBER_OF_SO_QUESTIONS: int = 12350818
DATASET_DIRECTORY_SO_1_XML_EXTERNAL: str = "/content/VTBA/Data Set/SO/20161110/1-XML"
DATASET_DIRECTORY_SO_2_TSV: str = DATASET_OVERAL_DIRECTORY + "/SO/20161110/2-TSV"
DATASET_DIRECTORY_SO_3_TSV_CLEANED: str = DATASET_OVERAL_DIRECTORY + "/SO/20161110/3-TSV-Cleaned"
DATASET_DIRECTORY_GH_4A1_TSV: str = DATASET_OVERAL_DIRECTORY + "/GH/AtLeastUpTo20161001/4A1-TSV"
DATASET_DIRECTORY_GH_4A2_TSV: str = DATASET_OVERAL_DIRECTORY + "/GH/AtLeastUpTo20161001/4A2-TSV"
DATASET_DIRECTORY_GH_4A3_TSV: str = DATASET_OVERAL_DIRECTORY + "/GH/AtLeastUpTo20161001/4A3-TSV"
DATASET_DIRECTORY_GH_4A4_ELASTICSEARCH_TSV: str = DATASET_OVERAL_DIRECTORY + "/GH/AtLeastUpTo20161001/4A4-elasticsearch-TSV"
DATASET_DIRECTORY_GH_4B1_TSV: str = DATASET_OVERAL_DIRECTORY + "/GH/AtLeastUpTo20161001/4B1-TSV"
DATASET_DIRECTORY_GH_4B2_TSV: str = DATASET_OVERAL_DIRECTORY + "/GH/AtLeastUpTo20161001/4B2-TSV"
DATASET_DIRECTORY_GH_4B3_TSV: str = DATASET_OVERAL_DIRECTORY + "/GH/AtLeastUpTo20161001/4B3-TSV"
DATASET_DIRECTORY_GH_4B4_ELASTICSEARCH_TSV: str = DATASET_OVERAL_DIRECTORY + "/GH/AtLeastUpTo20161001/4B4-elasticsearch-TSV"
DATASET_DIRECTORY_OUTPUT: str = DATASET_OVERAL_DIRECTORY + "/GH/AtLeastUpTo20161001/Output"
DATASET_DIRECTORY_BASE: str = "/content/VTBA"
DATASET_DIRECTORY_FOR_THE_ALGORITHM__GH__EXPERIMENT_MAIN: str = DATASET_DIRECTORY_BASE + "/Exp/In/GH/DSForMainExp"
DATASET_DIRECTORY_FOR_THE_ALGORITHM__GH__EXPERIMENT_TFIDF: str = DATASET_DIRECTORY_BASE + "/Exp/In/GH/DSForTFIDFExp"
DATASET_DIRECTORY_FOR_THE_ALGORITHM__SO__EXPERIMENT: str = DATASET_DIRECTORY_BASE + "/Exp/In/SO"
DATASET_DIRECTORY_FOR_THE_ALGORITHM__EXPERIMENT_OUTPUT: str = DATASET_DIRECTORY_BASE + "/Exp/Out"

ELASTIC_ELASTICSEARCH__PROJECT_NAME: str = "elastic/elasticsearch"
ASSIGNMENT_RESULTS_OVERAL_FOLDER_NAME: str = "outDetails"
TAGS_SEPARATOR: str = ";;"
FIELD_DELIMITER_FOR_JSON_OBJECT: str = "/&"
SEPARATOR_FOR_ARRAY_ITEMS: str = ";;"
MINOR_SEPARATOR_FOR_FIELDS_IN_OBJECT_IN_AN_ARRAY_ITEM: str = "^"
MINOR_SEPARATOR_FOR_FIELDS_IN_OBJECT_IN_AN_ARRAY_ITEM_REGEX: str = "/^"
ALL: str = "ALL"
TAB: str = "\t"
COMBINED_KEY_SEPARATOR: str = TAB
NUMBER_OF_TAB_CHARACTERS: int = 4
NUMBER_OF_LANGUAGES_TO_CONSIDER_IN_LANGUAGES_STUDY: int = 10
THIS_IS_A_SMALL_TEST: int = 200
THIS_IS_A_TEST: int = 10
THIS_IS_REAL: int = -1
ERROR: int = -1
AN_EXTREMELY_NEGATIVE_LONG: int = -9223372036854775808
AN_EXTREMELY_POSITIVE_LONG: int = 9223372036854775807
AN_EXTREMELY_POSITIVE_INT: int = 2147483647
SEQ_NUM____THIS_IS_NOT__B_A_EVIDENCE: int = -9223372036854775808
SEQ_NUM____NO_NEED_TO_TRIAGE_THIS_TYPE___OR___THIS_IS_NOT__NON_B_A_EVIDENCE: int = -9223372036854775808
NO_EXTRA_TEXTUAL_ELEMENT: int = -1

listOf13Projects: List[str] = [
    "rails",
    "yui3",
    "framework",
    "fog",
    "julia",
    "angular.js",
    "elasticsearch",
    "travis-ci",
    "salt",
    "khan-exercises",
    "brackets",
    "www.html5rocks.com",
    "ghost",
]

USEFUL_FIELDS_IN_JSON_FILES: Dict[str, List[str]] = {
    "bugs": ["_id", "url", "author", "createdAt{}$date", "labels[]name", "status", "title", "body"],
    "bugs:labels": ["id", "url", "author", "createdAt", "labels", "status", "title", "body"],
    "bugs:FieldsToRemoveInvalidCharacters": ["title", "body"],
    "comments": ["_id", "projectId", "createdAt{}$date", "user", "type", "commitSha", "issueNumber", "body"],
    "comments:labels": ["id", "projectId", "createdAt", "user", "type", "commitSha", "issueNumber", "body"],
    "comments:FieldsToRemoveInvalidCharacters": ["body"],
    "commits": ["_id", "projectId", "user", "createdAt{}$date", "url", "message"],
    "commits:labels": ["sha", "projectId", "user", "createdAt", "url", "commitMessage"],
    "commits:FieldsToRemoveInvalidCharacters": ["message"],
    "githubissues": ["_id", "bug", "project", "isPR", "number", "assignees[]username"],
    "githubissues:labels": ["id", "issue_Or_PRId_In_Bugs.tsv", "projectId", "isPR", "number", "assignees"],
    "githubissues:FieldsToRemoveInvalidCharacters": [],
    "githubprofiles": ["_id", "email", "createdAt{}$date", "updatedAt{}$date", "repositories"],
    "githubprofiles:labels": ["id", "email", "createdAt", "updatedAt", "repositories"],
    "githubprofiles:FieldsToRemoveInvalidCharacters": [],
    "projects": ["_id", "name", "description", "mainLanguagesPercentages", "languages[]_id&amount"],
    "projects:labels": ["id", "name", "description", "mainLanguagesPercentages", "[language^linesOfCode;;...]"],
    "projects:FieldsToRemoveInvalidCharacters": ["description"],
}

ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS: List[str] = [
    "T1_AUTHOR",
    "T2_COAUTHOR",
    "T3_ADMIN_CLOSER",
    "T4_DRAFTED_A",
    "T5_ALL_TYPES",
]

ASSIGNMENT_FILE_NAMES: List[str] = [
    f"9-ASSIGNMENTS_{ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS[0]}",
    f"9-ASSIGNMENTS_{ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS[1]}",
    f"9-ASSIGNMENTS_{ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS[2]}",
    f"9-ASSIGNMENTS_{ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS[3]}",
    f"9-ASSIGNMENTS_{ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS[4]}",
]

COMMUNITY_FILE_NAMES: List[str] = [
    f"10-COMMUNITY_{ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS[0]}",
    f"10-COMMUNITY_{ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS[1]}",
    f"10-COMMUNITY_{ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS[2]}",
    f"10-COMMUNITY_{ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS[3]}",
    f"10-COMMUNITY_{ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS[4]}",
]

COMMITS_DIFFS_TSV: str = "2-commits-diffs.tsv"
SIM_BRIDGE_SCRIPT: str = "/content/VTBA/sim_bridge.py"

HIGH_SCORES: List[float] = [0.0] * 10

allValidCharactersInSOQUESTION_AND_ANSWER_ForRegEx: str = "a-zA-Z0-9/./#/+/-/(/)/[/]/{/}/~/!/$/%/^/&/*/_/:/;/</>/,/./?///|/=/\"/'/`//"
allValidCharactersInSOURCECODE_Strict_ForRegEx: str = "[^a-zA-Z0-9/./#/+/-/_//]"
startsWithNumber_ForRegEx: str = "^[0-9].*"


def index_of_project_in_the_list_of_13_projects(project_name: Optional[str]) -> int:
    if project_name is None:
        return -1
    pn = project_name.lower()
    try:
        return listOf13Projects.index(pn)
    except ValueError:
        return -1


def get_difference_in_days(d1: datetime, d2: datetime) -> int:
    diff = d2 - d1
    return abs(diff.days)
