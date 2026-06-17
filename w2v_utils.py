from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Union

from gensim.models import KeyedVectors, Word2Vec

MODEL_PATH_ENV = "W2V_MODEL_PATH"
DEFAULT_MODEL_PATH = Path(os.getenv(MODEL_PATH_ENV, Path("w2v_model") / "word2vec.model"))

_model: Optional[Union[Word2Vec, KeyedVectors]] = None
_model_path: Path = DEFAULT_MODEL_PATH


def _load_model_from_path(model_path: Path) -> Union[Word2Vec, KeyedVectors]:
    if not model_path.exists():
        raise FileNotFoundError(f"Word2Vec model not found at {model_path}")

    try:
        return Word2Vec.load(model_path)
    except Exception:
        return KeyedVectors.load(model_path)


def configure_model_path(path: Union[str, Path]) -> None:
    global _model_path
    _model_path = Path(path)


def load_model(path: Optional[Union[str, Path]] = None) -> None:
    global _model, _model_path
    if path is not None:
        _model_path = Path(path)
    if _model_path is None:
        raise ValueError("No Word2Vec model path configured")
    _model = _load_model_from_path(_model_path)


def get_similarity(token: str, tag: str) -> float:
    global _model
    if not token or not tag:
        return 0.0
    if _model is None:
        load_model()

    if token not in _model.wv.key_to_index or tag not in _model.wv.key_to_index:
        return 0.0

    try:
        return float(_model.wv.similarity(token, tag))
    except Exception:
        return 0.0


def is_model_loaded() -> bool:
    return _model is not None


def model_path() -> str:
    return str(_model_path)
