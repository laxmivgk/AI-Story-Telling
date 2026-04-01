"""
Collaborative Story — Streamlit prototype.
Project folder: OneDrive/AI_ML/AI-Story-Telling — run: streamlit run app.py
"""
from __future__ import annotations

import hashlib
import html

import streamlit as st
from dotenv import load_dotenv

from llm import chat_completion, parse_characters_json, parse_choices_json
from prompts import (
    GENRE_RULES,
    UTILITY_SYSTEM_PROMPT,
    apply_choice_user_message,
    base_system_prompt,
    character_extract_user_message,
    choices_user_message,
    continue_user_message,
    # genre_remix_user_message,
    opening_user_message,
    visualization_prompt_user_message,
)

load_dotenv()

GENRES = ["Fantasy", "Sci-Fi", "Mystery", "Romance", "Horror", "Comedy"]
_UNDO_LIMIT = 20


def _story_fingerprint(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _prefix_and_latest_section(story: str) -> tuple[str, str]:
    s = (story or "").strip()
    if not s:
        return "", ""
    parts = re_split_paragraphs(s)
    if len(parts) <= 1:
        return "", parts[0] if parts else ""
    return "\n\n".join(parts[:-1]).strip(), parts[-1].strip()


def re_split_paragraphs(s: str) -> list[str]:
    return [p.strip() for p in s.split("\n\n") if p.strip()]


def _latest_paragraph(story: str) -> str:
    parts = re_split_paragraphs(story or "")
    return parts[-1] if parts else (story or "").strip()


def push_ai_undo():
    st.session_state.setdefault("ai_undo_stack", [])
    st.session_state.ai_undo_stack.append(
        {
            "story": st.session_state.story,
            "choice_options": st.session_state.choice_options,
        }
    )
    if len(st.session_state.ai_undo_stack) > _UNDO_LIMIT:
        st.session_state.ai_undo_stack = st.session_state.ai_undo_stack[-_UNDO_LIMIT:]


def init_state():
    defaults = {
        "phase": "setup",
        "title": "",
        "genre": "Fantasy",
        "hook": "",
        "story": "",
        "temp": 0.85,
        "choice_options": None,
        "characters_catalog": [],
        "_char_fp": "",
        "viz_prompt_last": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def system() -> str:
    return base_system_prompt(st.session_state.genre, st.session_state.title)


def show_error(e: Exception):
    st.error(str(e))


def _maybe_sync_characters(retry_slot_factory):
    if st.session_state.phase != "story":
        return
    body = (st.session_state.story or "").strip()
    if not body:
        st.session_state.characters_catalog = []
        st.session_state._char_fp = ""
        return
    fp = _story_fingerprint(body)
    if st.session_state.get("_char_fp") == fp:
        return
    slot = retry_slot_factory()
    try:
        raw = chat_completion(
            UTILITY_SYSTEM_PROMPT,
            character_extract_user_message(body),
            temperature=0.2,
            max_tokens=900,
            on_retry_countdown=lambda s: slot.caption(f"Character tracker: rate limited — retrying in **{s}s**…"),
        )
        slot.empty()
        st.session_state.characters_catalog = parse_characters_json(raw)
        st.session_state._char_fp = fp
    except Exception as e:
        slot.empty()
        st.session_state.char_error = str(e)
        st.session_state._char_fp = fp


def _build_markdown_export() -> str:
    title = (st.session_state.title or "Untitled").strip()
    genre = st.session_state.genre or ""
    story = (st.session_state.story or "").strip()
    lines = [f"# {title}", "", f"**Genre:** {genre}", ""]
    if story:
        lines.extend(["## Story", "", story])
    return "\n".join(lines)


def main():
    st.set_page_config(page_title="AI-Story-Telling", page_icon="📖", layout="wide")
    init_state()

    top_retry_placeholder = st.empty()
    _maybe_sync_characters(lambda: top_retry_placeholder)

    st.title("📖 AI-Story-Telling")
    st.caption("Define your tale, then co-author with AI—full context on every request.")

    with st.sidebar:
        st.subheader("Creativity")
        st.session_state.temp = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.5,
            value=float(st.session_state.temp),
            step=0.05,
            help="Higher = more surprising; lower = steadier continuation.",
        )
        st.subheader("Session")
        st.markdown(f"**Genre:** `{st.session_state.genre}`")
        rule = GENRE_RULES.get(st.session_state.genre, "")
        st.markdown("**Story rules (genre)**")
        st.info(rule)

        if st.session_state.phase == "story":
            st.subheader("Character tracker")
            err = st.session_state.pop("char_error", None)
            if err:
                st.warning(err)
            chars = st.session_state.get("characters_catalog") or []
            if not chars:
                st.caption("Characters appear here after the model scans the story.")
            else:
                for c in chars:
                    st.markdown(f"**{html.escape(c['name'])}** — {html.escape(c['description'])}")

            st.subheader("Export")
            md = _build_markdown_export()
            st.download_button(
                label="Download story (.md)",
                data=md.encode("utf-8"),
                file_name="story.md",
                mime="text/markdown",
            )

            undo_stack = st.session_state.get("ai_undo_stack") or []
            if st.button("↩ Undo last AI turn", disabled=len(undo_stack) == 0):
                snap = undo_stack.pop()
                st.session_state.story = snap["story"]
                st.session_state.choice_options = snap["choice_options"]
                st.session_state._char_fp = ""
                st.session_state.viz_prompt_last = ""
                st.rerun()

        if st.session_state.phase == "story" and st.button("← New story (reset)", type="secondary"):
            for k in (
                "phase",
                "title",
                "genre",
                "hook",
                "story",
                "choice_options",
                "ai_undo_stack",
                "characters_catalog",
                "_char_fp",
                "viz_prompt_last",
            ):
                st.session_state.pop(k, None)
            init_state()
            st.rerun()

    if st.session_state.phase == "setup":
        setup_screen()
    else:
        story_screen()


def setup_screen():
    col1, col2 = st.columns([1, 1])
    with col1:
        st.session_state.title = st.text_input("Title", value=st.session_state.title, placeholder="Working title")
        st.session_state.genre = st.selectbox(
            "Genre",
            GENRES,
            index=GENRES.index(st.session_state.genre) if st.session_state.genre in GENRES else 0,
        )
    with col2:
        st.session_state.hook = st.text_area(
            "Initial hook / setting",
            value=st.session_state.hook,
            height=180,
            placeholder="Where are we? Who matters? What tension or question opens the tale?",
        )

    if st.button("Start the Story", type="primary"):
        if not (st.session_state.title or "").strip():
            st.warning("Add a title (or a placeholder) to anchor the session.")
            return
        if not (st.session_state.hook or "").strip():
            st.warning("Describe an initial hook or setting so the opening has something to build on.")
            return
        try:
            retry_ui = st.empty()
            st.session_state.ai_undo_stack = []
            with st.spinner("Drafting opening…"):
                push_ai_undo()
                opening = chat_completion(
                    system(),
                    opening_user_message(
                        st.session_state.title.strip(),
                        st.session_state.genre,
                        st.session_state.hook.strip(),
                    ),
                    temperature=st.session_state.temp,
                    max_tokens=900,
                    on_retry_countdown=lambda s: retry_ui.caption(f"Rate limited — retrying in **{s}s**…"),
                )
            retry_ui.empty()
            st.session_state.story = opening.strip()
            st.session_state.phase = "story"
            st.session_state.choice_options = None
            st.session_state._char_fp = ""
            st.session_state.viz_prompt_last = ""
            st.rerun()
        except Exception as e:
            if st.session_state.get("ai_undo_stack"):
                st.session_state.ai_undo_stack.pop()
            show_error(e)


def story_screen():
    st.subheader(st.session_state.title or "Untitled")

    story_box = st.container()
    with story_box:
        st.markdown("### Story so far")
        safe = html.escape(st.session_state.story)
        scroll = (
            '<div style="max-height:420px;overflow-y:auto;padding:1rem 1.25rem;'
            'background:linear-gradient(180deg,var(--secondary-background-color,#f7f7f7) 0%,transparent 100%);'
            'border-radius:12px;border:1px solid rgba(128,128,128,0.25);'
            'font-size:1.05rem;line-height:1.65;white-space:pre-wrap;">'
            f"{safe}</div>"
        )
        st.markdown(scroll, unsafe_allow_html=True)

    # st.divider()

  
if __name__ == "__main__":
    main()
