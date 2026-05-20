import streamlit as st
import requests

# Read API_BASE from Streamlit secrets if available (production),
# otherwise fall back to localhost (local dev)
try:
    API_BASE = st.secrets["API_BASE"]
except Exception:
    API_BASE = "http://localhost:8000"

st.set_page_config(page_title="RAG Chatbot", page_icon="🤖", layout="wide")


def api_headers():
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def render_sources(sources: list[dict]):
    if not sources:
        return
    with st.expander("📚 Sources", expanded=False):
        for src in sources:
            st.markdown(
                f"- **{src['file_name']}** | Page {src['page_number']} | Score `{src['score']:.4f}`"
            )


def login_page():
    st.title("🤖 RAG Chatbot")
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            try:
                res = requests.post(
                    f"{API_BASE}/auth/login",
                    json={"username": username, "password": password},
                )
                if res.status_code == 200:
                    st.session_state.token    = res.json()["access_token"]
                    st.session_state.username = username
                    st.session_state.messages = []
                    _load_history()
                    st.rerun()
                else:
                    st.error(res.json().get("detail", "Login failed."))
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to API. Is the backend running?")

    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Choose a username")
            new_password = st.text_input("Choose a password", type="password")
            submitted = st.form_submit_button("Register", use_container_width=True)

        if submitted:
            try:
                res = requests.post(
                    f"{API_BASE}/auth/register",
                    json={"username": new_username, "password": new_password},
                )
                if res.status_code == 201:
                    st.session_state.token    = res.json()["access_token"]
                    st.session_state.username = new_username
                    st.session_state.messages = []
                    st.rerun()
                else:
                    st.error(res.json().get("detail", "Registration failed."))
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to API. Is the backend running?")


def _load_history():
    try:
        res = requests.get(f"{API_BASE}/chat/history", headers=api_headers())
        if res.status_code == 200:
            for msg in res.json().get("history", []):
                st.session_state.messages.append({
                    "role":    msg["role"],
                    "content": msg["message"],
                })
    except Exception:
        pass


def main_app():
    with st.sidebar:
        st.markdown(f"👤 **{st.session_state.get('username', '')}**")
        if st.button("Logout", use_container_width=True):
            for key in ["token", "username", "messages"]:
                st.session_state.pop(key, None)
            st.rerun()

        st.divider()
        st.header("📁 Documents")

        st.subheader("Upload")
        uploaded_file = st.file_uploader("Choose a file", type=["pdf", "txt", "md"])
        if uploaded_file and st.button("📤 Ingest", use_container_width=True):
            with st.spinner(f"Ingesting {uploaded_file.name}..."):
                try:
                    res = requests.post(
                        f"{API_BASE}/documents/upload",
                        files={"file": (uploaded_file.name, uploaded_file.getvalue())},
                        headers=api_headers(),
                    )
                    if res.status_code == 200:
                        d = res.json()
                        if d.get("skipped"):
                            st.warning(d.get("reason", "Already ingested."))
                        else:
                            st.success(
                                f"✓ **{d['file_name']}**\n\n"
                                f"- Pages: {d['pages_loaded']}\n"
                                f"- Chunks: {d['chunks_stored']}\n"
                                f"- Total in DB: {d['total_chunks']}"
                            )
                    else:
                        st.error(res.json().get("detail", "Upload failed."))
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to API.")

        st.divider()
        st.subheader("Your Files")
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        try:
            res = requests.get(f"{API_BASE}/documents", headers=api_headers())
            if res.status_code == 200:
                data = res.json()
                if data["total"] == 0:
                    st.info("No documents uploaded yet.")
                else:
                    for f in data["files"]:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.text(f"📄 {f['file_name']}")
                        with col2:
                            if st.button("🗑", key=f"del_{f['file_name']}"):
                                requests.delete(
                                    f"{API_BASE}/documents/{f['file_name']}",
                                    headers=api_headers(),
                                )
                                st.rerun()
        except requests.exceptions.ConnectionError:
            st.warning("Cannot reach API.")

        st.divider()
        st.subheader("Status")
        try:
            res = requests.get(f"{API_BASE}/health")
            if res.status_code == 200:
                st.success("✓ API online")
        except Exception:
            st.error("✗ API offline")

    st.title("🤖 RAG Chatbot")
    st.caption("Ask questions about your documents — powered by Google Gemini")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and message.get("sources"):
                render_sources(message["sources"])

    if prompt := st.chat_input("Ask a question about your documents..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    res = requests.post(
                        f"{API_BASE}/chat",
                        json={"question": prompt},
                        headers=api_headers(),
                    )
                    if res.status_code == 200:
                        data    = res.json()
                        answer  = data["answer"]
                        sources = data["sources"]
                        st.markdown(answer)
                        render_sources(sources)
                        st.session_state.messages.append({
                            "role":    "assistant",
                            "content": answer,
                            "sources": sources,
                        })
                    elif res.status_code == 401:
                        st.warning("Session expired. Please log in again.")
                        st.session_state.pop("token", None)
                        st.rerun()
                    elif res.status_code == 404:
                        msg = "⚠️ No documents found. Please upload a document first."
                        st.warning(msg)
                        st.session_state.messages.append({"role": "assistant", "content": msg})
                    else:
                        msg = f"❌ {res.json().get('detail', 'Unknown error')}"
                        st.error(msg)
                        st.session_state.messages.append({"role": "assistant", "content": msg})
                except requests.exceptions.ConnectionError:
                    msg = "❌ Cannot connect to API."
                    st.error(msg)
                    st.session_state.messages.append({"role": "assistant", "content": msg})


if "token" not in st.session_state:
    login_page()
else:
    main_app()
