# -*- coding: utf-8 -*-
"""Durable, cross-session memory for Nebras: a small student profile persisted
to disk and woven into the system prompt. Not conversation logging — just the
few durable facts (name, what they study, ongoing concerns)."""
import json
import os
import threading

_PATH = os.path.expanduser("~/.nebras_memory.json")
_lock = threading.Lock()


def load() -> dict:
    try:
        with open(_PATH, encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict):
            d.setdefault("name", None)
            d.setdefault("notes", [])
            return d
    except Exception:
        pass
    return {"name": None, "notes": []}


def save(data: dict) -> None:
    try:
        with _lock:
            tmp = _PATH + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, _PATH)
    except Exception as e:
        print(f"[MEMORY] save failed: {e}")


def prompt_block(data: dict) -> str:
    """A short Arabic block to append to the system prompt. Empty when unknown."""
    if not data or (not data.get("name") and not data.get("notes")):
        return ""
    lines = ["", "", "=== شنو تتذكره عن هذا الطالب (من جلسات سابقة) ==="]
    if data.get("name"):
        lines.append(f"- اسمه: {data['name']}")
    for n in (data.get("notes") or [])[:8]:
        lines.append(f"- {n}")
    lines.append("استعمل هذي المعلومات بشكل طبيعي وياه، لا تسردها عليه سرد.")
    return "\n".join(lines)
