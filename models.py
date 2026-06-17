from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


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


@dataclass
class Bug:
    project_id: Optional[str] = None
    number: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    labels: Optional[str] = None
    title: Optional[str] = None
    title_number_of_words: Optional[int] = None
    body: Optional[str] = None
    body_number_of_words: Optional[int] = None


@dataclass
class Evidence:
    date: Optional[datetime] = None
    b_a_seq_num: Optional[int] = None
    non_ba_virtual_seq_num: Optional[List[int]] = field(default_factory=list)
    freq: Optional[int] = None
    total_number_of_words_in_this_evidence: Optional[int] = None
    tf: Optional[float] = None
    word2vec_tf_score: float = 0.0


@dataclass
class Assignment:
    bug_number: Optional[str] = None
    date: Optional[datetime] = None
    login: Optional[str] = None


@dataclass
class Assignee:
    login: Optional[str] = None
    rank: Optional[int] = None


@dataclass
class Project:
    id: Optional[str] = None
    owner_repo: Optional[str] = None
    description: Optional[str] = None
    description_number_of_words: Optional[int] = None
    main_language_percentages: Optional[str] = None
    languages_and_their_lines_of_code: Optional[str] = None
    bugs_starting_date: Optional[datetime] = None
    commits_starting_date: Optional[datetime] = None
    p_rs_starting_date: Optional[datetime] = None
    bug_comments_starting_date: Optional[datetime] = None
    commit_comments_starting_date: Optional[datetime] = None
    p_r_comments_starting_date: Optional[datetime] = None
    bug_events_starting_date: Optional[datetime] = None
    overal_starting_date: Optional[datetime] = None
