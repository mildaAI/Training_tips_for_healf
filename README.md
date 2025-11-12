# Training_tips_for_healf

A small repository with a Streamlit app example that connects to a local Ollama instance and chats with the `gemma3:4b` model.

Files of interest
- `streamlit_app.py`: Streamlit web UI to chat with `gemma3:4b` via Ollama.
- `requirements.txt`: Python dependencies for the demo (Streamlit and Ollama client).
- `.env.example`: Example environment variables (OLLAMA_HOST).

Quick start

1. Install Python dependencies (prefer a virtualenv):

```
pip install -r requirements.txt
```

2. Ensure Ollama is running locally. By default this app expects Ollama's HTTP API at `http://localhost:11434`.

3. Run the Streamlit app:

```
streamlit run streamlit_app.py
```

4. Open the provided local URL in your browser. Enter messages and chat with `gemma3:4b`.

Troubleshooting
- If the `ollama` package isn't found, verify the package name or install via the provider's instructions. The app will show an error in the UI if the package is missing.
- If you get connection errors, check `OLLAMA_HOST` in the sidebar or set it in your environment and restart the app.

Notes
- This example uses the `ollama.Client` API as shown in `docs/ollama.md` and `docs/streamlit.md` in this repository.

# Training_tips_for_healf
trainings_tets
