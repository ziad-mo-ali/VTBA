package utils;

import java.text.DateFormat;
import java.text.DecimalFormat;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Date;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Random;

import com.google.common.collect.ImmutableMap;

import data.Evidence;
import main.AlgPrep;
import main.WordsAndCounts;
import utils.Constants.BTOption1_whatToAddToAllBugs;
import utils.Constants.BTOption2_w;
import utils.Constants.BTOption3_TF;
import utils.Constants.BTOption4_IDF;
import utils.Constants.BTOption5_prioritizePAs;
import utils.Constants.BTOption6_whatToAddToAllCommits;
import utils.FileManipulationResult;


public class Constants {
	public static final String DATASET_OVERAL_DIRECTORY = "C:/2-Study/BugTriaging2/Data Set/Main";
	public static final String DATASET_DIRECTORY_GH_JSON = DATASET_OVERAL_DIRECTORY + "/GH/AtLeastUpTo20161001/1-JSON";
	public static final String DATASET_DIRECTORY_GH_2_TSV = DATASET_OVERAL_DIRECTORY + "/GH/AtLeastUpTo20161001/2-TSV/3- 16 projects + 2 project families (13 + 3 + 6 more projects)";
	public static final String DATASET_DIRECTORY_GH_3_TSV = DATASET_OVERAL_DIRECTORY + "/GH/AtLeastUpTo20161001/3-TSV-Cleaned";
	public static final String DATASET_DIRECTORY_GH_3_TSV_OUTPUT = DATASET_OVERAL_DIRECTORY + "/GH/AtLeastUpTo20161001/3-TSV-Cleaned/Output";
	public static final long TOTAL_NUMBER_OF_SO_QUESTIONS = 12350818;
	public static final String DATASET_DIRECTORY_SO_1_XML_EXTERNAL = "/content/VTBA/Data Set/SO/20161110/1-XML";
	public static final String DATASET_DIRECTORY_SO_2_TSV = DATASET_OVERAL_DIRECTORY + "/SO/20161110/2-TSV";
	public static final String DATASET_DIRECTORY_SO_3_TSV_CLEANED = DATASET_OVERAL_DIRECTORY + "/SO/20161110/3-TSV-Cleaned";
	public static final String DATASET_DIRECTORY_GH_4A1_TSV = DATASET_OVERAL_DIRECTORY + "/GH/AtLeastUpTo20161001/4A1-TSV";
	public static final String DATASET_DIRECTORY_GH_4A2_TSV = DATASET_OVERAL_DIRECTORY + "/GH/AtLeastUpTo20161001/4A2-TSV";
	public static final String DATASET_DIRECTORY_GH_4A3_TSV = DATASET_OVERAL_DIRECTORY + "/GH/AtLeastUpTo20161001/4A3-TSV";
	public static final String DATASET_DIRECTORY_GH_4A4_ELASTICSEARCH_TSV = DATASET_OVERAL_DIRECTORY + "/GH/AtLeastUpTo20161001/4A4-elasticsearch-TSV";
	public static final String DATASET_DIRECTORY_GH_4B1_TSV = DATASET_OVERAL_DIRECTORY + "/GH/AtLeastUpTo20161001/4B1-TSV";
	public static final String DATASET_DIRECTORY_GH_4B2_TSV = DATASET_OVERAL_DIRECTORY + "/GH/AtLeastUpTo20161001/4B2-TSV";
	public static final String DATASET_DIRECTORY_GH_4B3_TSV = DATASET_OVERAL_DIRECTORY + "/GH/AtLeastUpTo20161001/4B3-TSV";
	public static final String DATASET_DIRECTORY_GH_4B4_ELASTICSEARCH_TSV = DATASET_OVERAL_DIRECTORY + "/GH/AtLeastUpTo20161001/4B4-elasticsearch-TSV";
	public static final String DATASET_DIRECTORY_OUTPUT = DATASET_OVERAL_DIRECTORY + "/GH/AtLeastUpTo20161001/Output";
	public static final String DATASET_DIRECTORY_BASE = "/content/VTBA";
	public static final String DATASET_DIRECTORY_FOR_THE_ALGORITHM__GH__EXPERIMENT_MAIN = DATASET_DIRECTORY_BASE + "/Exp/In/GH/DSForMainExp";
	public static final String DATASET_DIRECTORY_FOR_THE_ALGORITHM__GH__EXPERIMENT_TFIDF = DATASET_DIRECTORY_BASE + "/Exp/In/GH/DSForTFIDFExp";
	public static final String DATASET_DIRECTORY_FOR_THE_ALGORITHM__SO__EXPERIMENT = DATASET_DIRECTORY_BASE + "/Exp/In/SO";
	public static final String DATASET_DIRECTORY_FOR_THE_ALGORITHM__EXPERIMENT_OUTPUT = DATASET_DIRECTORY_BASE + "/Exp/Out";

	public enum ProjectType{
		FASE_3__NO_PUBLIC_BUGS,
		FASE_13_EXTENSION__PROJECT_FAMILIES_OF_TWO_PROJECTS,
		FASE_13,
		OTHERS_UNKNOWN
	}
	public static String ELASTIC_ELASTICSEARCH__PROJECT_NAME = "elastic/elasticsearch";
	public static final String ASSIGNMENT_RESULTS_OVERAL_FOLDER_NAME = "outDetails";
	public static final String TAGS_SEPARATOR = ";;";
	public static final String FIELD_DELIMITER_FOR_JSON_OBJECT = "/&";
	public static final Map<String, List<String>> USEFUL_FIELDS_IN_JSON_FILES = ImmutableMap.<String, List<String>> builder()
			.put("bugs", Arrays.asList(new String[] { "_id", "url", "author", "createdAt{}$date", "labels[]name", "status", "title", "body" }))
			.put("bugs:labels", Arrays.asList(new String[] { "id", "url", "author", "createdAt", "labels", "status", "title", "body" }))
			.put("bugs:FieldsToRemoveInvalidCharacters", Arrays.asList(new String[] { "title", "body" }))
			.put("comments", Arrays.asList(new String[] { "_id", "projectId", "createdAt{}$date", "user", "type", "commitSha", "issueNumber", "body" }))
			.put("comments:labels", Arrays.asList(new String[] { "id", "projectId", "createdAt", "user", "type", "commitSha", "issueNumber", "body" }))
			.put("comments:FieldsToRemoveInvalidCharacters", Arrays.asList(new String[] { "body" }))
			.put("commits", Arrays.asList(new String[] { "_id", "projectId", "user", "createdAt{}$date", "url", "message" }))
			.put("commits:labels", Arrays.asList(new String[] { "sha", "projectId", "user", "createdAt", "url", "commitMessage" }))
			.put("commits:FieldsToRemoveInvalidCharacters", Arrays.asList(new String[] { "message" }))
			.put("githubissues", Arrays.asList(new String[] { "_id", "bug", "project", "isPR", "number", "assignees[]username" }))
			.put("githubissues:labels", Arrays.asList(new String[] { "id", "issue_Or_PRId_In_Bugs.tsv", "projectId", "isPR", "number", "assignees" }))
			.put("githubissues:FieldsToRemoveInvalidCharacters", Arrays.asList(new String[] { }))
			.put("githubprofiles", Arrays.asList(new String[] { "_id", "email", "createdAt{}$date", "updatedAt{}$date", "repositories" }))
			.put("githubprofiles:labels", Arrays.asList(new String[] { "id", "email", "createdAt", "updatedAt", "repositories" }))
			.put("githubprofiles:FieldsToRemoveInvalidCharacters", Arrays.asList(new String[] { }))
			.put("projects", Arrays.asList(new String[] { "_id", "name", "description", "mainLanguagesPercentages", "languages[]_id&amount" }))
			.put("projects:labels", Arrays.asList(new String[] { "id", "name", "description", "mainLanguagesPercentages", "[language^linesOfCode;;...]" }))
			.put("projects:FieldsToRemoveInvalidCharacters", Arrays.asList(new String[] {"description"}))
			.build();

	public static final String SEPARATOR_FOR_ARRAY_ITEMS = ";;";
	public static final String MINOR_SEPARATOR_FOR_FIELDS_IN_OBJECT_IN_AN_ARRAY_ITEM = "^";
	public static final String MINOR_SEPARATOR_FOR_FIELDS_IN_OBJECT_IN_AN_ARRAY_ITEM_REGEX = "/^";
	public static final String allValidCharactersInSOQUESTION_AND_ANSWER_ForRegEx = "a-zA-Z0-9/./#/+/-/(/)/[/]/{/}/~/!/$/%/^/&/*/_/:/;/</>/,/./?///|/=/\"/'/`//";
	public static final String SEPARATOR_FOR_TABLE_AND_FIELD = ":";
	public static final String TAB = "\t";
	public static final String COMBINED_KEY_SEPARATOR = TAB;
	public static final DecimalFormat integerFormatter = new DecimalFormat("###,###");
	public static final DecimalFormat floatFormatter = new DecimalFormat("###,###.#");
	public static final DecimalFormat floatPercentageFormatter = new DecimalFormat("###,##0.00000");
	public static final DecimalFormat highPrecisionFloatFormatter = new DecimalFormat("###,###.######");
	public static final int NUMBER_OF_TAB_CHARACTERS = 4;
	public static final int NUMBER_OF_LANGUAGES_TO_CONSIDER_IN_LANGUAGES_STUDY = 10;
	public static final String ALL = "ALL";
	public static final long THIS_IS_A_SMALL_TEST = 200;
	public static final long THIS_IS_A_TEST = 10;
	public static final long THIS_IS_REAL = -1;
	public static final int ERROR = -1;
	public static final long AN_EXTREMELY_NEGATIVE_LONG = Long.MIN_VALUE;
	public static final long AN_EXTREMELY_POSITIVE_LONG = Long.MAX_VALUE;
	public static final int AN_EXTREMELY_POSITIVE_INT = Integer.MAX_VALUE;
	public static final int SEQ_NUM____THIS_IS_NOT__B_A_EVIDENCE = Integer.MIN_VALUE;
	public static final int SEQ_NUM____NO_NEED_TO_TRIAGE_THIS_TYPE___OR___THIS_IS_NOT__NON_B_A_EVIDENCE = Integer.MIN_VALUE;
	public static DateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'");

	public enum SortOrder{
		ASCENDING_INTEGER, DESCENDING_INTEGER, DEFAULT_FOR_STRING
	}
	public enum FieldType{
		LONG, STRING, NOT_IMPORTANT
	}
	public enum LogicalOperation {
		NO_CONDITION, AND, OR, IGNORE_THE_SECOND_OPERAND
	}
	public enum ConditionType {
		EQUALS, NOT_EQUALS, NOTHING, GREATER_OR_EQUAL
	}
	public enum JoinType{
		INNER_JOIN, LEFT_JOIN, RIGHT_JOIN, FULL_JOIN
	}

	public static final int NUMBER_OF_ASSIGNEE_TYPES = 5;

	public static enum ASSIGNMENT_TYPES_TO_TRIAGE{
		T1_AUTHOR,
		T2_COAUTHOR,
		T3_ADMIN_CLOSER,
		T4_DRAFTED_A,
		T5_ALL_TYPES
		};

	public static final int EVIDENCE_TYPE_COMMIT = 11;
	public static final int EVIDENCE_TYPE_PR = 12;
	public static final int EVIDENCE_TYPE_BUG_COMMENT = 13;
	public static final int EVIDENCE_TYPE_COMMIT_COMMENT = 14;
	public static final int EVIDENCE_TYPE_PR_COMMENT = 15;

	public static final int[] EVIDENCE_TYPE = {
			ASSIGNMENT_TYPES_TO_TRIAGE.T1_AUTHOR.ordinal(),
			ASSIGNMENT_TYPES_TO_TRIAGE.T2_COAUTHOR.ordinal(),
			ASSIGNMENT_TYPES_TO_TRIAGE.T3_ADMIN_CLOSER.ordinal(),
			ASSIGNMENT_TYPES_TO_TRIAGE.T4_DRAFTED_A.ordinal(),
			ASSIGNMENT_TYPES_TO_TRIAGE.T5_ALL_TYPES.ordinal(),
			EVIDENCE_TYPE_COMMIT,
			EVIDENCE_TYPE_PR,
			EVIDENCE_TYPE_BUG_COMMENT,
			EVIDENCE_TYPE_COMMIT_COMMENT,
			EVIDENCE_TYPE_PR_COMMENT,
			};
	public static Double[] TYPE_SIMILARITY = {
			1.0, 1.0, 1.0, 1.0, 1.0,
			0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
			0.3, 0.3, 0.6, 0.3, 0.1,
	};

	public static final String[] ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS = {
			"T1_AUTHOR", "T2_COAUTHOR", "T3_ADMIN_CLOSER", "T4_DRAFTED_A", "T5_ALL_TYPES",
			};

	public static final String[] ASSIGNMENT_FILE_NAMES = {
			"9-ASSIGNMENTS_"+ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS[0],
			"9-ASSIGNMENTS_"+ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS[1],
			"9-ASSIGNMENTS_"+ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS[2],
			"9-ASSIGNMENTS_"+ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS[3],
			"9-ASSIGNMENTS_"+ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS[4]
			};

	public static final String[] COMMUNITY_FILE_NAMES = {
			"10-COMMUNITY_"+ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS[0],
			"10-COMMUNITY_"+ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS[1],
			"10-COMMUNITY_"+ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS[2],
			"10-COMMUNITY_"+ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS[3],
			"10-COMMUNITY_"+ASSIGNED_BUGS_TYPES__SHORT_DESCRIPTIONS[4],
			};

	public static double[] highScores = new double[]{0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0};

	public enum BTOption1_whatToAddToAllBugs{
		JUST_USE_BUG_TD, ADD_PTD, ADD_ML, ADD_PTD_ML
	}
	public enum BTOption2_w{
		NO_TERM_WEIGHTING, USE_TERM_WEIGHTING
	}
	public enum BTOption3_TF{
		ONE, FREQ, FREQ__TOTAL_NUMBER_OF_TERMS, LOG_BASED
	}
	public enum BTOption4_IDF{
		ONE, FREQ, FREQ__TOTAL_NUMBER_OF_TERMS, LOG_BASED
	}
	public enum BTOption5_prioritizePAs{
		NO_PRIORITY, PRIORITY_FOR_PREVIOUS_ASSIGNEES
	}
	public enum BTOption6_whatToAddToAllCommits{
		JUST_USE_COMMIT_M, ADD_PTD, ADD_mL, ADD_PTD_mL
	}
	public enum BTOption7_whenToCountTextLength{
		USE_TEXT_LENGTH_BEFORE_REMOVING_NON_SO_TAGS,
		USE_TEXT_LENGTH_AFTER_REMOVING_NON_SO_TAGS
	}
	public enum BTOption8_recency{
		NO_RECENCY, RECENCY1, RECENCY2
	}
	public enum GeneralExperimentType{
		CALCULATE_OUR_METRIC__TTBA,
		JUST_CALCULATE_ORIGINAL_TF_IDF,
		JUST_CALCULATE_TIME_TF_IDF,
		JUST_CALCULATE_TIME_TF_IDF2,
		CALCULATE_TBA,
		CALCULATE_VTBA_GH,
		CALCULATE_VTBA_GH__CALCULATE_WEIGHS_ONLINE,
		CALCULATE_VTBA_SOURCECODE
	}

	public static final String[] listOf13Projects = new String[]{
			"rails", "yui3", "framework", "fog", "julia", "angular.js", "elasticsearch",
			"travis-ci", "salt", "khan-exercises", "brackets", "www.html5rocks.com", "ghost"
	};

	public static final int NO_EXTRA_TEXTUAL_ELEMENT = -1;

	public static final String allValidCharactersInSOURCECODE_Strict_ForRegEx = "[^a-zA-Z0-9/./#/+/-/_//]";

	public static final String startsWithNumber_ForRegEx = "^[0-9].*";

	public static int indexOfProjectInTheListOf13Projects(String projectName){
		if (projectName == null)
			return -1;
		String pn = projectName.toLowerCase();
		for (int i=0; i<listOf13Projects.length; i++){
			if (pn.equals(listOf13Projects[i]))
				return i;
		}
		return -1;
	}

	public static void f1(FileManipulationResult fMR){
		FileManipulationResult fMR2 = new FileManipulationResult();
		fMR2.errors++;
		if (fMR2.errors > 0)
			fMR.errors = fMR2.errors;
	}

	public static int getDifferenceInDays(Date d1, Date d2) {
	    int daysdiff = 0;
	    long diff = d2.getTime() - d1.getTime();
	    daysdiff = (int) Math.abs(diff / (24 * 60 * 60 * 1000));
	    return daysdiff;
	}

	public static void main(String[] args) {
		Date d1 = new Date();
		Date d2 = new Date();
		try {
			d1 = dateFormat.parse("2010-09-24T22:01:14.000Z");
			d2 = dateFormat.parse("2010-09-24T22:01:14.000Z");
		} catch (ParseException e) {
			e.printStackTrace();
		}
		System.out.println(getDifferenceInDays(d2, d1));
	}
}
