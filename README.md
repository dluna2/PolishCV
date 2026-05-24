# PolishCV
Our product uses an LLM to tailor resumes to job descriptions.

## How to run

1. Go to the project folder:


2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install requirements.txt
```

4. Create/update `.env` with your keys:

```env
HF_TOKEN=your_huggingface_token
LLAMA_MODEL=your_huggingface_model_id
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=your_openai_model
```

5. Start the Streamlit app:

```bash
streamlit run app.py
```

6. Open the local URL shown in terminal (usually `http://localhost:8501`).
