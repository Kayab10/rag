# streamlit_app.py - Frontend for the RAG Chatbot.
#
# Talks to the FastAPI backend via HTTP.
# Make sure the backend is running before starting this:
#   uvicorn app.main:app --reload
#
# Run with:
#   streamlit run frontend/streamlit_app.py

import streamlit as st
import requests

# ── Config ────────────────────────────────────────────────────────────────────
API_BASE = "http://localhost:8000"


# ── Page setup ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RAG Chatbot",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 RAG Chatbot")
st.caption("Ask questions about your uploaded documents — powered by Google Gemini")


# ── Helper ────────────────────────────────────────────────────────────────────
def render_sources(sources: list[dict]):
    """Render source documents in a collapsible expander."""
    if not sources:
        return
    with st.expander("📚 Sources", expanded=False):
        for src in sources:
            st.markdown(
                f"- **{src['file_name']}** | "
                f"Page {src['page_number']} | "
                f"Score `{src['score']:.4f}`"
            )


# ── Sidebar — Document Management ─────────────────────────────────────────────
with st.sidebar:
    st.header("📁 Documents")

    # ── Upload ────────────────────────────────────────────────────────────────
    st.subheader("Upload a Document")
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["pdf", "txt", "md"],
        help="Supported formats: PDF, TXT, Markdown",
    )

    if uploaded_file is not None:
        if st.button("📤 Ingest Document", use_container_width=True):
            with st.spinner(f"Ingesting {uploaded_file.name}..."):
                try:
                    response = requests.post(
                        f"{API_BASE}/documents/upload",
                        files={"file": (uploaded_file.name, uploaded_file.getvalue())},
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.success(
                            f"✓ **{data['file_name']}** ingested\n\n"
                            f"- Pages loaded: {data['pages_loaded']}\n"
                            f"- Chunks stored: {data['chunks_stored']}\n"
                            f"- Total chunks in DB: {data['total_chunks']}"
                        )
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to API. Is the backend running?")

    st.divider()

    # ── Uploaded files list ───────────────────────────────────────────────────
    st.subheader("Uploaded Files")

    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

    try:
        response = requests.get(f"{API_BASE}/documents")
        if response.status_code == 200:
            data = response.json()
            if data["total"] == 0:
                st.info("No documents uploaded yet.")
            else:
                for f in data["files"]:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(f"📄 {f['file_name']}")
                        st.caption(f"{f['size_kb']} KB")
                    with col2:
                        if st.button("🗑", key=f"del_{f['file_name']}", help="Delete file"):
                            del_response = requests.delete(
                                f"{API_BASE}/documents/{f['file_name']}"
                            )
                            if del_response.status_code == 200:
                                st.success(f"Deleted {f['file_name']}")
                                st.rerun()
                            else:
                                st.error("Delete failed.")
    except requests.exceptions.ConnectionError:
        st.warning("Cannot reach API.")

    st.divider()

    # ── Health check ──────────────────────────────────────────────────────────
    st.subheader("System Status")
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            info = response.json()
            st.success("✓ API online")
            st.metric("Chunks in DB", info["total_chunks"])
        else:
            st.error("API returned an error.")
    except requests.exceptions.ConnectionError:
        st.error("✗ API offline")


# ── Main — Chat Interface ──────────────────────────────────────────────────────

# Initialise chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render existing chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and message.get("sources"):
            render_sources(message["sources"])

# Chat input
if prompt := st.chat_input("Ask a question about your documents..."):

    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call API and show response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    f"{API_BASE}/chat",
                    json={"question": prompt},
                )

                if response.status_code == 200:
                    data    = response.json()
                    answer  = data["answer"]
                    sources = data["sources"]

                    st.markdown(answer)
                    render_sources(sources)

                    st.session_state.messages.append({
                        "role":    "assistant",
                        "content": answer,
                        "sources": sources,
                    })

                elif response.status_code == 404:
                    msg = "⚠️ No documents found. Please upload a document first."
                    st.warning(msg)
                    st.session_state.messages.append({"role": "assistant", "content": msg})

                else:
                    detail = response.json().get("detail", "Unknown error")
                    msg = f"❌ Error: {detail}"
                    st.error(msg)
                    st.session_state.messages.append({"role": "assistant", "content": msg})

            except requests.exceptions.ConnectionError:
                msg = "❌ Cannot connect to API. Make sure the backend is running."
                st.error(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})
