package main;

import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.deeplearning4j.models.embeddings.loader.WordVectorSerializer;
import org.deeplearning4j.models.word2vec.Word2Vec;

public class WordVecSimilarity {
    public static final String MODEL_PATH = "/content/models/w2v_model_5chunksaveing/word2vec.bin";

    private static WordVecSimilarity instance = null;
    private final Word2Vec model;

    private WordVecSimilarity() {
        File modelFile = new File(MODEL_PATH);
        if (!modelFile.exists()) {
            throw new RuntimeException("Word2Vec model file not found at " + MODEL_PATH);
        }

        try {
            this.model = WordVectorSerializer.readWord2VecModel(modelFile);
        } catch (Exception exc) {
            throw new RuntimeException("Failed to load Word2Vec model from " + MODEL_PATH, exc);
        }
    }

    public static synchronized WordVecSimilarity getInstance() {
        if (instance == null) {
            instance = new WordVecSimilarity();
        }
        return instance;
    }

    public synchronized Map<String, Double> getSimilarities(List<String> tokens, List<String> tags) {
        Map<String, Double> result = new HashMap<>();
        if (tokens == null || tags == null || tokens.isEmpty() || tags.isEmpty()) {
            return result;
        }

        for (String token : tokens) {
            if (token == null || !model.hasWord(token)) {
                continue;
            }
            for (String tag : tags) {
                if (tag == null || !model.hasWord(tag)) {
                    continue;
                }
                double sim = model.similarity(token, tag);
                if (sim > 0.0) {
                    result.put(token + "__" + tag, sim);
                }
            }
        }
        return result;
    }
}
