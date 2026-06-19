package main;

import java.io.IOException;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.nio.MappedByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;

public final class W2VSimilarity {

    public static final int DIM = 300;
    private static final int CHUNK_SIZE = 1 << 30; // 1 GiB chunks, must be a multiple of 4

    private final Map<String, Integer> vocab;
    private final float[] allVectors;

    public W2VSimilarity(Path vocabPath, Path vectorsPath) throws IOException {
        String json = Files.readString(vocabPath, StandardCharsets.UTF_8);
        Map<String, Integer> loaded = parseVocabJson(json);
        this.vocab = Collections.unmodifiableMap(loaded);

        long expectedFloats = (long) vocab.size() * DIM;
        this.allVectors = new float[Math.toIntExact(expectedFloats)];

        try (FileChannel channel = FileChannel.open(vectorsPath, StandardOpenOption.READ)) {
            long fileSize = channel.size();
            if (fileSize % Integer.BYTES != 0) {
                throw new IllegalStateException("vectors.bin size is not a multiple of 4 bytes");
            }

            long actualFloats = fileSize / Integer.BYTES;
            if (actualFloats != expectedFloats) {
                throw new IllegalStateException(
                    "vectors.bin size mismatch: expected " + expectedFloats +
                    " floats for vocab size " + vocab.size() +
                    " (dim=" + DIM + "), got " + actualFloats +
                    ". Did the export script and DIM constant get out of sync?");
            }

            int numChunks = (int) ((fileSize + CHUNK_SIZE - 1) / CHUNK_SIZE);
            long position = 0;
            int destOffset = 0;
            for (int i = 0; i < numChunks; i++) {
                int size = (int) Math.min(CHUNK_SIZE, fileSize - position);
                MappedByteBuffer buf = channel.map(FileChannel.MapMode.READ_ONLY, position, size);
                buf.order(ByteOrder.LITTLE_ENDIAN);
                FloatBuffer floatBuf = buf.asFloatBuffer();
                int chunkFloats = size / Integer.BYTES;
                floatBuf.get(allVectors, destOffset, chunkFloats);
                destOffset += chunkFloats;
                position += size;
            }
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

    public void readRow(int rowIndex, float[] dest) {
        if (dest.length != DIM) {
            throw new IllegalArgumentException("Destination array must have length " + DIM);
        }
        int srcOffset = rowIndex * DIM;
        System.arraycopy(allVectors, srcOffset, dest, 0, DIM);
    }

    private static Map<String, Integer> parseVocabJson(String json) {
        Map<String, Integer> result = new HashMap<>();
        String trimmed = json.trim();
        if (!trimmed.startsWith("{") || !trimmed.endsWith("}")) {
            throw new IllegalArgumentException("Invalid vocab.json format");
        }
        trimmed = trimmed.substring(1, trimmed.length() - 1).trim();
        if (trimmed.isEmpty()) {
            return result;
        }

        int i = 0;
        int len = trimmed.length();
        while (i < len) {
            while (i < len && Character.isWhitespace(trimmed.charAt(i))) {
                i++;
            }
            if (i >= len) {
                break;
            }
            if (trimmed.charAt(i) == ',') {
                i++;
                continue;
            }
            if (trimmed.charAt(i) != '"') {
                throw new IllegalArgumentException("Invalid vocab.json entry at position " + i);
            }
            i++;
            StringBuilder key = new StringBuilder();
            while (i < len) {
                char c = trimmed.charAt(i);
                if (c == '\\') {
                    i++;
                    if (i >= len) {
                        throw new IllegalArgumentException("Invalid escape in vocab.json");
                    }
                    key.append(trimmed.charAt(i));
                } else if (c == '"') {
                    i++;
                    break;
                } else {
                    key.append(c);
                }
                i++;
            }
            while (i < len && Character.isWhitespace(trimmed.charAt(i))) {
                i++;
            }
            if (i >= len || trimmed.charAt(i) != ':') {
                throw new IllegalArgumentException("Invalid vocab.json key/value separator");
            }
            i++;
            while (i < len && Character.isWhitespace(trimmed.charAt(i))) {
                i++;
            }
            if (i >= len) {
                throw new IllegalArgumentException("Invalid vocab.json value");
            }
            int sign = 1;
            if (trimmed.charAt(i) == '-') {
                sign = -1;
                i++;
            }
            if (i >= len || !Character.isDigit(trimmed.charAt(i))) {
                throw new IllegalArgumentException("Invalid vocab.json integer value");
            }
            int value = 0;
            while (i < len && Character.isDigit(trimmed.charAt(i))) {
                value = value * 10 + (trimmed.charAt(i) - '0');
                i++;
            }
            result.put(key.toString(), value * sign);
            while (i < len && Character.isWhitespace(trimmed.charAt(i))) {
                i++;
            }
            if (i < len && trimmed.charAt(i) == ',') {
                i++;
            }
        }
        return result;
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
            out[c] = dot(i, j);
        }
        return out;
    }

    private float dot(int row1, int row2) {
        int off1 = row1 * DIM;
        int off2 = row2 * DIM;
        float sum = 0f;
        for (int k = 0; k < DIM; k++) {
            sum += allVectors[off1 + k] * allVectors[off2 + k];
        }
        return sum;
    }

    public float dot(float[] vector, int rowIndex) {
        if (vector.length != DIM) {
            throw new IllegalArgumentException("vector length must be " + DIM);
        }
        int off2 = rowIndex * DIM;
        float sum = 0f;
        for (int k = 0; k < DIM; k++) {
            sum += vector[k] * allVectors[off2 + k];
        }
        return sum;
    }
}
