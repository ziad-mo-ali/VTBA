package data;

import java.util.Date;

import utils.Constants;
import utils.Constants.ASSIGNMENT_TYPES_TO_TRIAGE;
import utils.Constants.BTOption3_TF;

public class Evidence {
    public Date date;
    public int bASeqNum; // if the evidence is a bugAssignment, this is the BA sequence number.
                         // Otherwise Constants.SEQ_NUM____THIS_IS_NOT__B_A_EVIDENCE.
    public int[] nonBA_virtualSeqNum; // If the evidence is a bug assignment, these are
                                      // Constants.SEQ_NUM____NO_NEED_TO_TRIAGE_THIS_TYPE___OR___THIS_IS_NOT__NON_B_A_EVIDENCE.
                                      // Otherwise the sequence number of the last bug assignment before this evidence.
    public int freq;
    public int totalNumberOfWordsInThisEvidence;
    public double tf;

    // ── NEW FIELD ─────────────────────────────────────────────────────────────────
    // When this evidence originates from CodeBERT source-code analysis, tf is set
    // directly to the confidence score (0.0–1.0) and this flag is set to true.
    // For all traditional text evidence this flag is false.
    public boolean isCodeBERTEvidence;
    // ─────────────────────────────────────────────────────────────────────────────

    // ── CONSTRUCTOR: traditional text evidence (unchanged behaviour) ───────────
    public Evidence(Date date, int seqNum, int[] virtualSeqNum,
                    int freq, int totalNumberOfWordsInThisEvidence,
                    BTOption3_TF option3_TF) {
        this.date = date;
        this.bASeqNum = seqNum;
        this.nonBA_virtualSeqNum = new int[Constants.NUMBER_OF_ASSIGNEE_TYPES];
        for (int i = ASSIGNMENT_TYPES_TO_TRIAGE.T1_AUTHOR.ordinal();
             i <= ASSIGNMENT_TYPES_TO_TRIAGE.T5_ALL_TYPES.ordinal(); i++)
            this.nonBA_virtualSeqNum[i] = virtualSeqNum[i];
        this.freq = freq;
        this.totalNumberOfWordsInThisEvidence = totalNumberOfWordsInThisEvidence;
        this.isCodeBERTEvidence = false;

        // NOTE: the original switch is missing 'break' statements, so every case
        // falls through and tf ends up as the LOG_BASED value regardless.
        // That existing behaviour is preserved here intentionally – fixing it is a
        // separate concern.
        switch (option3_TF) {
            case ONE:
                tf = 1;
            case FREQ:
                tf = freq;
            case FREQ__TOTAL_NUMBER_OF_TERMS:
                tf = (double) freq / totalNumberOfWordsInThisEvidence;
            case LOG_BASED:
                tf = 1 + (double) Math.log10(freq);
        }
    }

    // ── CONSTRUCTOR: CodeBERT source-code evidence ────────────────────────────
    /**
     * Creates an Evidence object whose tf value IS the CodeBERT confidence score.
     * The traditional freq / totalNumberOfWordsInThisEvidence fields are set to
     * sentinel values (-1) because they are not meaningful for this evidence type.
     *
     * @param date              Date of the commit whose code was analysed.
     * @param seqNum            Bug-assignment sequence number (same semantics as
     *                          the traditional constructor).
     * @param virtualSeqNum     Non-BA virtual sequence numbers (same semantics).
     * @param confidenceScore   CodeBERT output: probability in [0.0, 1.0] that
     *                          the developer's code relates to the SO tag.
     */
    public Evidence(Date date, int seqNum, int[] virtualSeqNum, double confidenceScore) {
        this.date = date;
        this.bASeqNum = seqNum;
        this.nonBA_virtualSeqNum = new int[Constants.NUMBER_OF_ASSIGNEE_TYPES];
        for (int i = ASSIGNMENT_TYPES_TO_TRIAGE.T1_AUTHOR.ordinal();
             i <= ASSIGNMENT_TYPES_TO_TRIAGE.T5_ALL_TYPES.ordinal(); i++)
            this.nonBA_virtualSeqNum[i] = virtualSeqNum[i];
        this.freq = -1;                           // not applicable
        this.totalNumberOfWordsInThisEvidence = -1; // not applicable
        this.tf = confidenceScore;                // confidence IS the tf substitute
        this.isCodeBERTEvidence = true;
    }
}
