package main;

import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class WordVecSimilarity {
    public static final String DEFAULT_MODEL_DIR = "/content/models/w2v_model_5chunksaveing";
    public static final String MODEL_DIR = System.getProperty(
            "w2v.model.dir",
            System.getenv().getOrDefault("W2V_MODEL_DIR", DEFAULT_MODEL_DIR));
    public static final Path VOCAB_PATH = Paths.get(MODEL_DIR, "vocab.json");
    public static final Path VECTORS_PATH = Paths.get(MODEL_DIR, "vectors.bin");

    private static volatile WordVecSimilarity instance = null;
    private final W2VSimilarity index;

    private WordVecSimilarity() {
        try {
            this.index = new W2VSimilarity(VOCAB_PATH, VECTORS_PATH);
        } catch (IOException exc) {
            throw new RuntimeException("Failed to load W2V vectors from " + MODEL_DIR, exc);
        }
    }

    public static WordVecSimilarity getInstance() {
        WordVecSimilarity result = instance;
        if (result == null) {
            synchronized (WordVecSimilarity.class) {
                result = instance;
                if (result == null) {
                    result = new WordVecSimilarity();
                    instance = result;
                }
            }
        }
        return result;
    }

    public Map<String, Double> getSimilarities(List<String> tokens, List<String> tags) {
        Map<String, Double> result = new HashMap<>();
        if (tokens == null || tags == null || tokens.isEmpty() || tags.isEmpty()) {
            return result;
        }

        for (String token : tokens) {
            if (token == null) {
                continue;
            }
            int tokenIndex = index.indexOf(token);
            if (tokenIndex < 0) {
                continue;
            }
            for (String tag : tags) {
                if (tag == null) {
                    continue;
                }
                int tagIndex = index.indexOf(tag);
                if (tagIndex < 0) {
                    continue;
                }
                float sim = index.similarity(tokenIndex, tagIndex);
                // Preserve prior behavior: only positive similarities are kept.
                // If zero/negative similarities should be included, remove this filter.
                if (sim > 0.0f) {
                    result.put(token + "__" + tag, (double) sim);
                }
            }
        }
        return result;
    }
}
