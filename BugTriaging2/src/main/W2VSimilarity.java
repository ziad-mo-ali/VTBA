package main;

import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.nio.MappedByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.Arrays;
import java.util.Collections;
import java.util.Map;
import java.util.Set;

public final class W2VSimilarity implements AutoCloseable {

    private static final int DIM = 300;

    private final Map<String, Integer> vocab;
    private final FloatBuffer vectors;
    private final FileChannel channel; // kept open for the life of the mmap

    public W2VSimilarity(Path vocabPath, Path vectorsPath) throws IOException {
        ObjectMapper mapper = new ObjectMapper();
        @SuppressWarnings("unchecked")
        Map<String, Integer> loaded = mapper.readValue(vocabPath.toFile(), Map.class);
        this.vocab = Collections.unmodifiableMap(loaded);

        this.channel = FileChannel.open(vectorsPath, StandardOpenOption.READ);
        MappedByteBuffer buf = channel.map(FileChannel.MapMode.READ_ONLY, 0, channel.size());
        buf.order(ByteOrder.LITTLE_ENDIAN);
        this.vectors = buf.asFloatBuffer();

        long expectedFloats = (long) vocab.size() * DIM;
        if (vectors.capacity() != expectedFloats) {
            throw new IllegalStateException(
                "vectors.bin size mismatch: expected " + expectedFloats +
                " floats for vocab size " + vocab.size() +
                " (dim=" + DIM + "), got " + vectors.capacity() +
                ". Did the export script and DIM constant get out of sync?");
        }
    }

    /** Row index of a token, or -1 if out-of-vocabulary. */
    public int indexOf(String token) {
        Integer idx = vocab.get(token);
        return idx == null ? -1 : idx;
    }

    public boolean contains(String token) {
        return vocab.containsKey(token);
    }

    public int vocabSize() {
        return vocab.size();
    }

    /** Read-only view of all known tokens (e.g. for sampling/benchmarking). */
    public Set<String> tokens() {
        return vocab.keySet();
    }

    /**
     * Cosine similarity between two token indexes.
     */
    public float similarity(int tokenIndex, int tagIndex) {
        return dot(tokenIndex, tagIndex);
    }

    /**
     * Cosine similarity between two tokens.
     *
     * @return similarity in [-1, 1], or Float.NaN if either token is OOV.
     */
    public float similarity(String t1, String t2) {
        int i = indexOf(t1);
        int j = indexOf(t2);
        if (i < 0 || j < 0) return Float.NaN;
        return dot(i, j);
    }

    /** Same as similarity(), but throws on OOV instead of returning NaN. */
    public float similarityStrict(String t1, String t2) {
        int i = indexOf(t1);
        if (i < 0) throw new IllegalArgumentException("OOV token: " + t1);
        int j = indexOf(t2);
        if (j < 0) throw new IllegalArgumentException("OOV token: " + t2);
        return dot(i, j);
    }

    /**
     * Hot-path helper: looks up t1's offset once, then scores it against many
     * candidates (e.g. ranking candidates for a query token). OOV candidates
     * get NaN in the output, at the same index as the input.
     */
    public float[] similarityBatch(String t1, String[] candidates) {
        float[] out = new float[candidates.length];
        int i = indexOf(t1);
        if (i < 0) {
            Arrays.fill(out, Float.NaN);
            return out;
        }
        int off1 = i * DIM;
        for (int c = 0; c < candidates.length; c++) {
            int j = indexOf(candidates[c]);
            if (j < 0) {
                out[c] = Float.NaN;
                continue;
            }
            out[c] = dotByOffset(off1, j * DIM);
        }
        return out;
    }

    private float dot(int row1, int row2) {
        return dotByOffset(row1 * DIM, row2 * DIM);
    }

    private float dotByOffset(int off1, int off2) {
        float sum = 0f;
        for (int k = 0; k < DIM; k++) {
            sum += vectors.get(off1 + k) * vectors.get(off2 + k);
        }
        return sum;
    }

    @Override
    public void close() throws IOException {
        channel.close();
    }
}
