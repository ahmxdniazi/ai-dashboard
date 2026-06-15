import streamlit as st
import ollama
import time

# ── Page config ──────────────────────────────────────────────
st.set_page_config(page_title="AI Dashboard", page_icon="🤖", layout="centered")
st.title("🤖 Local AI Dashboard")
st.caption("Powered by Ollama — runs fully on your machine, no internet needed.")

# ── Fetch available models from Ollama ───────────────────────
@st.cache_data(ttl=30)   # re-fetch model list every 30 seconds
def get_models():
    try:
        models = ollama.list()
        return [m.model for m in models.models]
    except Exception:
        return []

models = get_models()

if not models:
    st.error("⚠️ No models found. Run `ollama pull llama3.2` in your terminal first.")
    st.stop()

# ── Sidebar controls ─────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")
    selected_model = st.selectbox("Choose a model", models)
    temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1,
                            help="Higher = more creative, Lower = more precise")
    st.divider()
    st.markdown("**How to add more models:**")
    st.code("ollama pull mistral", language="bash")

# ── Chat history (stored in session state) ───────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display past messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Input box ────────────────────────────────────────────────
prompt = st.chat_input("Ask anything...")

if prompt:
    # Show the user's message immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # ── Stream the model's response ──────────────────────────
    with st.chat_message("assistant"):
        placeholder = st.empty()        # we'll update this in-place
        stats_box   = st.empty()        # live tokens/sec counter

        full_response = ""
        token_count   = 0
        start_time    = time.time()

        stream = ollama.chat(
            model=selected_model,
            messages=st.session_state.messages,
            options={"temperature": temperature},
            stream=True,                # ← key flag: gives us chunks one by one
        )

        for chunk in stream:
            token = chunk["message"]["content"]
            full_response += token
            token_count   += 1

            elapsed = time.time() - start_time
            tps     = token_count / elapsed if elapsed > 0 else 0

            placeholder.markdown(full_response + "▌")   # ▌ = blinking cursor feel
            stats_box.caption(f"⚡ {tps:.1f} tokens/sec  •  {token_count} tokens")

        # Final render without the fake cursor
        placeholder.markdown(full_response)
        elapsed = time.time() - start_time
        stats_box.caption(
            f"✅ Done — {token_count} tokens in {elapsed:.1f}s "
            f"({token_count/elapsed:.1f} tok/s)"
        )

    st.session_state.messages.append({"role": "assistant", "content": full_response})