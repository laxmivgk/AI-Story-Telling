# 📖 AI Story-Telling

A collaborative, genre-aware storytelling application built with Python, Streamlit, and the Groq LLM API.

## 1. Setup Instructions

1. **Clone or navigate** to the project directory.
2. **Create a Virtual Environment** and activate it:
   ```bash
   python3 -m venv .myvenv
   source .myvenv/bin/activate
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Environment Variables**: Create a `.env` file in the root directory and add your API key:
   ```env
   GROQ_API_KEY=your_api_key_here
   GROQ_MODEL=llama-3.3-70b-versatile
   ```
5. **Run the Application**:
   ```bash
   python -m streamlit run app.py
   ```

## 2. Model & Provider Used
This project utilizes the **Groq API** SDK as the provider, specifically optimized for speed. The default model utilized is `llama-3.3-70b-versatile` (or `llama-3.1-8b-instant`), chosen for its excellent instruction-following capabilities and rapid inference speeds for a smooth user experience.

## 3. Final System Prompt
The LLM logic utilizes heavily parameterized templates. Below is the final core system prompt that strictly enforces the rules:

```text
You are a masterful collaborative storyteller and world-builder, working dynamically with a human co-author. 

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
- Output *only* the new story prose, blending seamlessly into the existing text.
```

## 4. Memory / Consistency Strategy
The application ensures flawless continuity by treating the entire generated story log as a **single canonical source of truth**. 
Instead of relying on summary memory (which drops details), the application passes the full `st.session_state.story` variable into the prompt context on *every single request*. Combined with the strict system bounds, this guarantees the AI cannot forget character names, previously established settings, or the story's timeline.

## 5. Bonus Features Implemented
* **Robust Rate-Limit Handling**: Includes a custom exponential backoff wrapper (`llm.py`) that catches `RateLimitErrors` (429) and network timeouts. Rather than crashing, it displays a live countdown spinner to the user dynamically.
* **Character Tracker**: A background LLM call runs silently to parse character names and descriptions from the text, rendering an updated character catalog in the sidebar.
* **Undo Functionality**: An `ai_undo_stack` tracks the previous states (`push_ai_undo()`), allowing the user to seamlessly roll back the story with the click of a button if they dislike a generation.
* **Markdown Export**: Users can download their finished collaborative story directly as a `.md` file.

## 6. What Didn't Work Well at First
Initially, managing Streamlit's stateless UI alongside branch options ("Give me choices") caused glitches. If a user clicked a button to generate choices, rendering the choices and preventing the core UI from resetting required complex state handling. 
**The Fix:** I decoupled the UI by heavily relying on `st.session_state`. When the LLM outputs its JSON response for branching choices, the array is saved into `st.session_state.choice_options`. The UI conditionally checks for this array; if it exists, it hides the standard inputs and exclusively renders the option buttons. Clicking an option clears the state and calls `st.rerun()`, creating a seamless loop without widget conflicts.

With high temperatures story was not deterministic.
**The fix** Reduced temperature to 0.10. Out of 3 attempts with this temperature, same input genre, title and hook, story came exactly same all the times.
## 7. What I'd Improve with Another Day
* **Database Persistence**: Currently, memory drops if the browser session hard-refreshes. I would add SQLite or PostgreSQL integration to save "Sessions" so users can return to ongoing stories later.
* **DALL-E / Image Generation**: Hooking into an image-generation API to automatically generate establishing shots or character portraits every few paragraphs to make the storytelling visually immersive.
* **Multi-branch visualization**: Use a graphing library to visually map out the diverging story paths a user has taken.
* **Undo last AI Turn**: If it's clicked after all Undo's, it should go back to the homepage instead of showing empty 'story so far' section
* **improve UI add chat sessions.
* **Use rich text editor** for story writing - like WYSWYG editor
*classification* of the story, keywords highlighting - use some roberta mode.
