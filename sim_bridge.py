#!/usr/bin/env python3
"""Bridge script for COMMIT_WORD2VEC token-tag similarity requests."""

import json
import sys
import os

MODEL_DIR = "/content/VTBA/w2v_model"
MODEL_SUBDIR = "w2v_model_5chunksaveing"
MODEL_PATH = os.path.join(MODEL_DIR, MODEL_SUBDIR, "word2vec.model")


def load_model():
    """Load Word2Vec model."""
    try:
        from gensim.models import Word2Vec
        model = Word2Vec.load(MODEL_PATH)
        return model
    except Exception as exc:
        print(json.dumps({"error": f"Model load failed: {str(exc)}"}))
        return None


def main():
    # Ensure model is available
    if not os.path.exists(MODEL_PATH):
        print(f"ERROR: Model not found at {MODEL_PATH}", file=sys.stderr)
        sys.exit(1)

    # Load model
    model = load_model()
    if model is None:
        sys.exit(1)

    print("READY")
    sys.stdout.flush()

    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if line == "":
            continue
        if line == "EXIT":
            break

        try:
            request = json.loads(line)
            tokens = request.get("tokens", [])
            tags = request.get("tags", [])
            if not isinstance(tokens, list) or not isinstance(tags, list):
                print(json.dumps({"error": "Invalid tokens or tags format"}))
                sys.stdout.flush()
                continue

            output = {}
            for token in tokens:
                if not isinstance(token, str):
                    continue
                if token not in model.wv:
                    continue
                for tag in tags:
                    if not isinstance(tag, str):
                        continue
                    if tag not in model.wv:
                        continue
                    key = f"{token}__{tag}"
                    try:
                        score = float(model.wv.similarity(token, tag))
                    except Exception:
                        continue
                    if score > 0.0:
                        output[key] = score

            print(json.dumps(output))
            sys.stdout.flush()
        except json.JSONDecodeError as exc:
            print(json.dumps({"error": f"JSON decode error: {str(exc)}"}))
            sys.stdout.flush()
        except Exception as exc:
            print(json.dumps({"error": f"Processing error: {str(exc)}"}))
            sys.stdout.flush()


if __name__ == "__main__":
    main()
