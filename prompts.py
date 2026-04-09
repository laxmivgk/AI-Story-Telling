"""Story rules and system prompts — keep genre and consistency explicit."""

GENRE_RULES = {
    "Fantasy": "Use magic, mythic stakes, and evocative prose sparingly—ground wonder in concrete detail.",
    "Sci-Fi": "Respect plausible science-feeling tech; avoid contradicting established future rules.",
    "Mystery": "Plant fair clues; preserve tension; no cheating resolutions.",
    "Romance": "Honor emotional truth and chemistry; avoid sudden personality flips.",
    "Horror": "Build dread through implication and atmosphere; respect prior threats.",
    "Comedy": "Keep timing sharp; let humor arise from character, not random gags that break tone.",
}


def base_system_prompt(genre: str, title: str) -> str:
    rules = GENRE_RULES.get(genre, "Maintain internal consistency.")
    return f"""You are a masterful collaborative storyteller and world-builder, working dynamically with a human co-author. 

Your objective is to continue the story naturally, preserving the established world state, character nuances, and stylistic tone.

### CORE PARAMETERS:
- **Genre:** {genre} 
- **Title Context:** «{title}»
- **Genre Specifics:** {rules}

### CONTINUITY & CANON (100% STRICT):
- Treat all previous events, character personalities, and world rules in the story log as strict canon.
- Never contradict established facts, reverse character growth, or suddenly alter the setting.
- Maintain the exact timeline and narrative flow. 

### STYLE & FORMAT:
- Write in vivid, highly engaging, but concise **third-person** narrative.
- Keep the tone engaging and fun, while still respecting the atmospheric demands of the genre.
- **Do NOT** summarize past events. Do **NOT** provide conversational filler, meta-commentary, or introductory remarks. 
- Output *only* the new story prose, blending seamlessly into the existing text."""


def opening_user_message(title: str, genre: str, hook: str) -> str:
    return f"""The co-author defined this setup:

**Title:** {title}
**Genre:** {genre}
**Initial hook / setting:**
{hook}

Write ONE strong opening segment of **150–250 words** (third-person unless the hook demands otherwise). Start immediately with narrative—no headings, no "Chapter One," no meta commentary. End on a line that invites the next beat."""


def continue_user_message(full_story: str) -> str:
    return f"""=== FULL STORY SO FAR (canonical; do not contradict) ===
{full_story}
=== END OF STORY SO FAR ===

Continue from the final line. Add **1–2 coherent paragraphs** only. Match vocabulary, pacing, and genre. No recap."""


def choices_user_message(full_story: str) -> str:
    return f"""=== FULL STORY SO FAR (canonical) ===
{full_story}
=== END ===

Propose **exactly 3** distinct branching directions for what happens next. Each must be **one sentence**, concrete, and mutually different in stakes or approach.

Reply with **only** this JSON object (no markdown fences, no extra text):
{{"choices": ["...", "...", "..."]}}"""


def apply_choice_user_message(full_story: str, chosen: str) -> str:
    return f"""=== FULL STORY SO FAR ===
{full_story}
=== END ===

The co-author selected this branch: **{chosen}**

Write **1–2 paragraphs** that follow this branch faithfully, staying consistent with everything above. No recap of earlier events in bulk—only seamless continuation."""


UTILITY_SYSTEM_PROMPT = """You are a precise creative assistant. Follow instructions exactly. No preamble or meta commentary unless the format requires it."""


# # def genre_remix_user_message(
# #     session_genre: str,
# #     target_genre: str,
# #     prior_context: str,
# #     latest_section: str,
# # ) -> str:
# #     prior = (prior_context or "").strip() or "(none — this is the opening segment)"
# #     return f"""**Task:** Rewrite ONLY the **LATEST SECTION** in the style of **{target_genre}**.

# # The session's primary genre has been **{session_genre}**; this block should read as **{target_genre}** while preserving the same plot beats, causality, character roles, and outcomes.

# # **EARLIER CONTEXT (for continuity only; do not copy into your output):**
# # {prior}

# # **LATEST SECTION — rewrite this in {target_genre}:**
# # {latest_section}

# # **Output rules:**
# # - Output **only** the rewritten section (final prose), same rough length and paragraph breaks as the original.
# # - No headings, labels, or explanation."""


def character_extract_user_message(full_story: str) -> str:
    return f"""From the story below, list **named characters** (people, creatures, or clear personas) visible in the text.

For each: a **short** description (≤ 20 words): role, look, or relationship — grounded in the text, no spoilers beyond what's written.

Story:
---
{full_story}
---

Reply with **only** this JSON (no markdown fences, no extra keys):
{{"characters": [{{"name": "...", "description": "..."}}, ...]}}

Use empty array if there are no named characters yet."""


def visualization_prompt_user_message(latest_paragraph: str, genre: str, title: str) -> str:
    return f"""You will write **one** image-generation prompt (English) for the **latest story paragraph** below.

**Context:** Title «{title}» · genre **{genre}**

**Latest paragraph (visual source):**
{latest_paragraph}

**Requirements:**
- Single flowing paragraph or compact semicolon list (what a human pastes into DALL·E, Flux, Midjourney).
- Describe scene, mood, lighting, camera/composition, palette; avoid copyrighted character names or artist names.
- No preamble — output **only** the image prompt text."""
