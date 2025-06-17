import json
import os
import streamlit as st

LANG_PATH = os.path.join(os.path.dirname(__file__), "lang.json")

with open(LANG_PATH, "r", encoding="utf-8") as f:
    _LANGS = json.load(f)


def get_language() -> str:
    return st.session_state.get("lang", "en")


def set_language(lang: str) -> None:
    st.session_state["lang"] = lang


def translate(key: str) -> str:
    lang = get_language()
    return _LANGS.get(lang, {}).get(key, key)

