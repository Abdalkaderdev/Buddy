# -*- coding: utf-8 -*-
"""Instant interview/demo answers. Questions the examiner is likely to ask are
matched right after STT and answered from pre-generated cached audio — no LLM,
no TTS credits, identical every time. Everything else flows to Claude normally."""
import hashlib
import json
import os
import re

_QA_PATH = os.path.join(os.path.dirname(__file__), "interview_qa.json")
_CACHE_DIR = os.path.expanduser("~/.nebras_cache")

_DIAC = re.compile(r"[ً-ْـ]")


def _norm(t: str) -> str:
    t = _DIAC.sub("", t or "")
    for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ى", "ي"),
                 ("ؤ", "و"), ("ئ", "ي"), ("ة", "ه"), ("چ", "ك"), ("گ", "ك")):
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t).strip()


def load() -> list:
    try:
        with open(_QA_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[FAQ] load failed: {e}")
        return []


def _cache_path(entry: dict, voice: str, model: str) -> str:
    key = hashlib.sha1((entry["answer"] + voice + model).encode("utf-8")).hexdigest()[:16]
    return os.path.join(_CACHE_DIR, f"{entry['id']}_{key}.pcm")


def match(transcript: str, qa: list):
    """Return the matching entry, or None. A trigger is a list of keywords that
    must ALL appear (order-independent) in the normalized transcript."""
    n = _norm(transcript)
    if not n:
        return None
    for e in qa:
        for trig in e.get("triggers", []):
            kws = [_norm(k) for k in (trig if isinstance(trig, list) else [trig])]
            if kws and all(k in n for k in kws):
                return e
    return None


def pregenerate(qa: list, gen_pcm, voice: str, model: str) -> int:
    """gen_pcm(text) -> raw s16le bytes. Caches each answer's audio to disk.
    Sets entry['_cache']. Returns how many were freshly generated."""
    os.makedirs(_CACHE_DIR, exist_ok=True)
    made = 0
    for e in qa:
        p = _cache_path(e, voice, model)
        e["_cache"] = p
        if os.path.exists(p) and os.path.getsize(p) > 2000:
            continue
        try:
            pcm = gen_pcm(e["answer"])
            if pcm and len(pcm) > 2000:
                with open(p, "wb") as f:
                    f.write(pcm)
                made += 1
        except Exception as ex:
            print(f"[FAQ] pregen '{e.get('id')}' failed: {ex}")
    return made
