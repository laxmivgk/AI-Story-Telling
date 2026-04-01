# AI-Story-Telling
pip install -r requirements.txt
## Project Structure

- `app/` - Core Python app (Groq SDK client, prompts, schemas, story generator)
- `ui/` - Streamlit frontend (`streamlit_app.py`)
- `configs/` - Environment templates
- `tests/` - Tests (optional)
- `docs/` - Architecture and technical notes
- `scripts/` - Local helper scripts

## Environment (.env)

Set `GROQ_API_KEY` (and optionally `GROQ_MODEL`) in a local `.env` file at the repo root (preferred) or in `configs/.env`.
An example is in `configs/.env.example`.