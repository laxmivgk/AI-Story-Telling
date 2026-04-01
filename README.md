# AI-Story-Telling
pip install -r requirements.txt

streamlit run app.py

## Project Structure

| File | Role |
|------|------|
| `app.py` | Streamlit UI, session state, bonus actions |
| `llm.py` | Groq client, retries, JSON parsers |
| `prompts.py` | All system/user prompt templates |
| `requirements.txt` | Dependencies |



## Environment (.env)

Set `GROQ_API_KEY`,`GROQ_MODEL` in a local `.env` file at the repo root (preferred)
GROQ_API_KEY= `your API key`
GROQ_MODEL=llama-3.1-8b-instant
