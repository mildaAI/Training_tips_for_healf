import os
import streamlit as st
from typing import List, Dict, Tuple

# Extra deps for connectivity check
import requests
from dotenv import load_dotenv

load_dotenv()

# Try to import Ollama client. If not installed, instruct user in README/requirements.
try:
    from ollama import Client
except Exception:
    Client = None

# App configuration
st.set_page_config(page_title="Ollama Chat — gemma3:4b", layout="wide")

st.title("Chat with gemma3:4b (Ollama)")


def check_ollama_host(host: str, timeout: float = 3.0) -> Tuple[bool, str]:
    """Try a simple HTTP GET to the provided host. Returns (ok, message).

    We do a plain GET to the host root to detect connection/refused and surface
    helpful troubleshooting info. This is intentionally conservative (no
    assumptions about specific Ollama endpoints).
    """
    try:
        resp = requests.get(host, timeout=timeout)
        return True, f"Reachable: HTTP {resp.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Connection refused — is Ollama running? Try `ollama serve`"
    except requests.exceptions.InvalidURL:
        return False, "Invalid host URL. Make sure it starts with http:// or https://"
    except requests.exceptions.Timeout:
        return False, "Connection timed out — check network and host/port"
    except Exception as e:
        return False, f"Error: {e}"


def list_models(host: str, timeout: float = 3.0):
    """Return a list of available model ids from the Ollama HTTP API (/v1/models).

    Returns an empty list on error.
    """
    try:
        resp = requests.get(f"{host.rstrip('/')}/v1/models", timeout=timeout)
        data = resp.json()
        return [m.get('id') for m in data.get('data', []) if 'id' in m]
    except Exception:
        return []


with st.sidebar:
    st.header("Connection")
    ollama_host = st.text_input("Ollama host", value=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
    # Try to list models for the host the user entered and present them in a selectbox.
    # There's also a Refresh button below if you just installed/updated a model.
    refresh_models = st.button("Refresh models")
    available_models = list_models(ollama_host)
    # Prefer gemma3:1b for this app if present, otherwise choose first available
    if available_models:
        preferred_index = 0
        if 'gemma3:1b' in available_models:
            preferred_index = available_models.index('gemma3:1b')
        model = st.selectbox("Model", options=available_models, index=preferred_index)
    else:
        model = st.text_input("Model", value="gemma3:1b")
        if refresh_models:
            # If user clicked refresh but no models were found, show actionable hints
            st.info("No models found at the provided host. If you just installed a model, try restarting Ollama (e.g. `ollama serve`) or pulling the model with `ollama pull gemma3:1b`.")
    max_history = st.number_input("Max messages to keep (per call)", min_value=1, max_value=50, value=10)
    clear = st.button("Clear conversation")
    check = st.button("Check connection")

    if check:
        ok, msg = check_ollama_host(ollama_host)
        if ok:
            st.success(msg)
        else:
            st.error(msg)
            st.info("Typical fixes: run `ollama serve` in a terminal, verify host/port, or set OLLAMA_HOST in .env")


if "messages" not in st.session_state:
    # messages is a list of dicts: {'role': 'user'|'assistant'|'system', 'content': '...'}
    st.session_state.messages = []

if clear:
    st.session_state.messages = []

if Client is None:
    st.error("The `ollama` Python package is not installed.")
    with st.expander("How to install the Python client"):
        st.write(
            "Install the dependencies (recommended inside a virtualenv). If the package name differs for your environment, follow the provider's install instructions."
        )
        st.code("pip install -r requirements.txt")
        st.code("# or, if available:\n# pip install ollama")

# Conversation area
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("Conversation")

    for msg in st.session_state.messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            st.markdown(f"**System:** {content}")
        elif role == "user":
            st.markdown(f"**You:** {content}")
        else:
            st.markdown(f"**Assistant:** {content}")

    response_placeholder = st.empty()

with col2:
    st.subheader("Controls")
    system_prompt = st.text_area("System prompt (optional)", value="", height=80)

    st.markdown("---")
    st.write("### User inputs for weekly plan")
    user_age = st.number_input("Age (years)", min_value=10, max_value=120, value=30)
    known_problems = st.text_area("Known health problems (comma-separated)", value="", height=80)
    time_for_exercise = st.number_input("Time per session (minutes)", min_value=10, max_value=240, value=45)
    fitness_goal = st.selectbox("Fitness goal", options=["Lose weight", "Gain muscle mass"], index=0)

    send = st.button("Generate weekly plan")


def safe_client(host: str):
    """Create an Ollama client or return None."""
    if Client is None:
        return None
    try:
        return Client(host=host)
    except Exception:
        # Fall back to default constructor
        try:
            return Client()
        except Exception:
            return None


if send:
    # Build a tailored prompt for the weekly plan using the provided inputs
    plan_request = (
        f"Create a 7-day weekly exercise plan for a {user_age}-year-old. "
        f"Known health problems: {known_problems or 'None'}. "
        f"Available time per session: {time_for_exercise} minutes. "
        f"Fitness goal: {fitness_goal}. "
        "Provide a daily breakdown (day name, exercise type, sets/reps or duration, intensity), safety notes, and a short warm-up and cool-down. Be concise and use bullet points."
    )

    # Add optional system prompt if provided
    if system_prompt.strip():
        st.session_state.messages.append({"role": "system", "content": system_prompt.strip()})
    # Append the plan request as a user message
    st.session_state.messages.append({"role": "user", "content": plan_request})

    # Build messages slice to send
    messages_to_send = st.session_state.messages[-int(max_history):]

    # Quick connectivity check before creating the client
    ok, msg = check_ollama_host(ollama_host)
    if not ok:
        st.error(f"Ollama host check failed: {msg}")
    else:
        client = safe_client(ollama_host)
        if client is None:
            st.error("Could not create Ollama client. Check that the `ollama` package is installed and Ollama is reachable.")
        else:
            # Stream the assistant response
            try:
                stream = client.chat(model=model, messages=messages_to_send, stream=True)
            except Exception as e:
                err_text = str(e)
                # Detect common out-of-memory / resource errors and give tailored advice
                if 'requires more system memory' in err_text or 'out of memory' in err_text.lower() or 'memory' in err_text.lower():
                    st.error("The model failed to run due to insufficient system memory.")
                    with st.expander("Why this happened and how to fix it"):
                        st.write(
                            "The selected model requires more RAM than is currently available on this machine.\n"
                            "Common fixes:\n"
                        )
                        st.write("- Use a smaller model (pull or select a lighter model, e.g. `gemma3:latest` or another small variant).")
                        st.write("- If you need `gemma3:4b`, run Ollama on a machine with more RAM or with GPU support.")
                        st.write("- Add swap / increase system memory (Windows: create a pagefile; Linux: create a swapfile).")
                        st.write("- Use a quantized or lower-precision variant if available (check Ollama model options).")
                        st.code("# Example: pull a specific model (if available)\nollama pull gemma3:4b")
                        st.write("After preparing, restart the Ollama server and click 'Refresh models' in the app.")
                    st.write(f"(raw error: {err_text})")
                else:
                    st.error(f"Error calling Ollama: {err_text}")
                stream = None

            assistant_text = ""
            if stream is not None:
                # Use the placeholder to progressively write
                for chunk in stream:
                    # chunk may be a dict-like or object with .message
                    content_piece = ""
                    try:
                        # Prefer dict access
                        if isinstance(chunk, dict):
                            content_piece = chunk.get("message", {}).get("content", "")
                        else:
                            # object attribute access
                            content_piece = getattr(chunk, "message", None)
                            if content_piece is not None:
                                content_piece = getattr(content_piece, "content", "")
                    except Exception:
                        content_piece = ""

                    assistant_text += content_piece
                    response_placeholder.markdown(f"**Assistant:** {assistant_text}")

                # Append final assistant message to session state
                st.session_state.messages.append({"role": "assistant", "content": assistant_text})

    # Clear input box
    st.session_state.user_input = ""


st.markdown("---")
st.caption("Note: This app uses the local Ollama HTTP API. Use the 'Check connection' button in the sidebar to verify the host before sending messages.")

# Footer with quick troubleshooting
with st.expander("Troubleshooting"):
    st.write(
        "If you see connection errors: ensure Ollama is running (usually `ollama serve`), the host is correct (default http://localhost:11434), and the `ollama` Python package is installed."
    )
    st.write("Windows PowerShell example to start Ollama (if installed):")
    st.code("ollama serve")
