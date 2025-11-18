from __future__ import annotations
from pathlib import Path
import json, unicodedata
import numpy as np
import pandas as pd
from django.conf import settings
import joblib

MODEL_DIR   = Path(settings.BASE_DIR) / "model"
MODEL_PATH  = MODEL_DIR / "vida_saludable_clf.joblib"
META_PATH   = MODEL_DIR / "metadata.json"

_MODEL = None
_META  = None
_META_FEATURES = None 

def _norm(s: str) -> str:
    s = str(s)
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return "".join(ch for ch in s.lower() if ch.isalnum())

def _load_metadata():
    global _META, _META_FEATURES
    if META_PATH.exists():
        with open(META_PATH, "r", encoding="utf-8") as f:
            _META = json.load(f)
        if "features" in _META and isinstance(_META["features"], list):
            _META_FEATURES = list(_META["features"])
        else:
            num = _META.get("num_cols", []) or _META.get("numericas", [])
            cat = _META.get("cat_cols", []) or _META.get("categoricas", [])
            _META_FEATURES = list(num) + list(cat)
    else:
        _META = None
        _META_FEATURES = None

def model_loaded() -> bool:
    global _MODEL
    if _MODEL is not None and _META is not None:
        return True
    if not MODEL_PATH.exists():
        return False
    try:
        _MODEL = joblib.load(MODEL_PATH)
    except Exception:
        _MODEL = None
        return False
    _load_metadata()
    return _MODEL is not None

def debug_ready() -> dict:
    return {
        "model_path": str(MODEL_PATH),
        "meta_path": str(META_PATH),
        "exists_model": MODEL_PATH.exists(),
        "exists_meta": META_PATH.exists(),
        "loaded": _MODEL is not None,
        "meta_features": _META_FEATURES,
    }

_FORM_FIELDS = [
    "genero","peso","altura","promedio_latidos","reposo_latidos",
    "duracion_sesion","agua_litros","frecuencia","porcentaje_grasa",
    "tipo_entrenamiento"
]
_NUM_CANDIDATES = {
    "peso","altura","promedio_latidos","reposo_latidos",
    "duracion_sesion","agua_litros","frecuencia","porcentaje_grasa"
}

def _coerce_types(d: dict) -> dict:
    out = {}
    for k, v in d.items():
        if k in _NUM_CANDIDATES:
            try:
                out[k] = float(v) if v is not None and v != "" else np.nan
            except Exception:
                out[k] = np.nan
        else:
            out[k] = None if v is None else str(v)
    return out

def _build_input_row(data: dict) -> pd.DataFrame | None:
    if _META_FEATURES is None:

        return pd.DataFrame([_coerce_types(data)])
    meta_norm = {_norm(feat): feat for feat in _META_FEATURES}
    row = {}
    d = _coerce_types(data)

    for fk, fv in d.items():
        nk = _norm(fk)
        if nk in meta_norm:
            row[meta_norm[nk]] = fv

    for feat in _META_FEATURES:
        if feat not in row:
            row[feat] = np.nan
    return pd.DataFrame([row], columns=_META_FEATURES)

def predict_estado_salud(data: dict) -> tuple[str|None, float|None]:
    if not model_loaded():
        return (None, None)
    X = _build_input_row(data)
    if X is None:
        return (None, None)

    if _META and ("cat_cols" in _META or "categoricas" in _META):
        cat = _META.get("cat_cols") or _META.get("categoricas") or []
        for c in cat:
            if c in X.columns:
                X[c] = X[c].astype("string")
    try:

        if hasattr(_MODEL, "predict_proba"):
            proba = _MODEL.predict_proba(X)[0]
            classes = getattr(_MODEL, "classes_", None)
            idx = int(np.argmax(proba))
            label = classes[idx] if classes is not None else str(idx)
            return (str(label), float(proba[idx]))
        else:
            label = _MODEL.predict(X)[0]
            return (str(label), None)
    except Exception:
        return (None, None)