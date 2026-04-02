import streamlit as st
import anthropic
import requests
from datetime import datetime
import pandas as pd

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Address Tracks AI", page_icon="🗺️", layout="wide")

# ─── Styling ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 0; max-width: 1100px; }
    .section-card {
        background: white;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 16px 18px;
        height: 100%;
        min-height: 180px;
    }
    .section-title {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #6c757d;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid #f0f0f0;
    }
    .card-item {
        font-size: 13px;
        padding: 6px 0;
        border-bottom: 1px solid #f8f9fa;
        color: #212529;
        line-height: 1.5;
    }
    .card-item:last-child { border-bottom: none; }
    .card-meta { font-size: 11px; color: #adb5bd; margin-top: 2px; }
    .header-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #e9ecef;
    }
    .status-dot {
        width: 8px; height: 8px;
        border-radius: 50%;
        background: #28a745;
        display: inline-block;
        margin-right: 6px;
    }
</style>
""", unsafe_allow_html=True)

# ─── Clients & secrets ────────────────────────────────────────────────────────
client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
GOOGLE_DOC_URL = st.secrets["GOOGLE_DOC_URL"]

# ─── Shared store (persists across all sessions) ──────────────────────────────
@st.cache_resource
def get_shared_store():
    return {
        "launches": [],
        "meetings": [],
        "accomplishments": [],
        "usage_logs": [],       # [{email, timestamp, question}]
        "is_populated": False,
    }

shared = get_shared_store()

# ─── Per-user session state ───────────────────────────────────────────────────
for k, v in {
    "messages": [],
    "is_admin": False,
    "show_login": False,
    "admin_tab": "usage",
    "user_email": "",
    "email_submitted": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─── Fetch Google Doc content ─────────────────────────────────────────────────
@st.cache_data(ttl=300)  # refresh every 5 minutes
def fetch_google_doc():
    try:
        response = requests.get(GOOGLE_DOC_URL, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return f"[Could not fetch document: {e}]"


# ─── Log usage ────────────────────────────────────────────────────────────────
def log_usage(email, question):
    shared["usage_logs"].append({
        "email": email,
        "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "question": question,
    })


# ─── Render 3 section cards ───────────────────────────────────────────────────
def render_cards():
    col1, col2, col3 = st.columns(3)

    with col1:
        items_html = "".join([
            f"<div class='card-item'>🚀 <strong>{l['name']}</strong><div class='card-meta'>{l['date']}{'  ·  ' + l['owner'] if l['owner'] else ''}</div></div>"
            for l in shared["launches"]
        ]) if shared["launches"] else "<div style='color:#adb5bd;font-size:13px'>No launches added yet</div>"
        st.markdown(f"<div class='section-card'><div class='section-title'>🚀 Upcoming Launches</div>{items_html}</div>", unsafe_allow_html=True)

    with col2:
        items_html = "".join([
            f"<div class='card-item'>📅 <strong>{m['topic']}</strong><div class='card-meta'>{m['date']}</div></div>"
            for m in shared["meetings"]
        ]) if shared["meetings"] else "<div style='color:#adb5bd;font-size:13px'>No meetings added yet</div>"
        st.markdown(f"<div class='section-card'><div class='section-title'>📅 Meeting Points</div>{items_html}</div>", unsafe_allow_html=True)

    with col3:
        items_html = "".join([
            f"<div class='card-item'>✅ {a}</div>"
            for a in shared["accomplishments"]
        ]) if shared["accomplishments"] else "<div style='color:#adb5bd;font-size:13px'>No accomplishments added yet</div>"
        st.markdown(f"<div class='section-card'><div class='section-title'>🏆 Accomplishments</div>{items_html}</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN LOGIN
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.show_login and not st.session_state.is_admin:
    st.markdown("### 🔐 Admin Login")
    pwd = st.text_input("Password", type="password")
    c1, c2 = st.columns([1, 5])
    with c1:
        if st.button("Login", type="primary"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.is_admin = True
                st.session_state.show_login = False
                st.rerun()
            else:
                st.error("Incorrect password")
    with c2:
        if st.button("Cancel"):
            st.session_state.show_login = False
            st.rerun()
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN PANEL
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.is_admin:
    # Header
    hc1, hc2 = st.columns([4, 1])
    with hc1:
        st.markdown("### ⚙️ Admin Panel — Address Tracks AI")
    with hc2:
        if st.button("Sign out", use_container_width=True):
            st.session_state.is_admin = False
            st.rerun()

    tab1, tab2 = st.tabs(["📊 Usage Tracking", "✏️ Update Content"])

    # ── Tab 1: Usage Tracking ─────────────────────────────────────────────────
    with tab1:
        st.markdown("#### Who is asking what")
        st.caption("Every question asked by leadership is logged below in real time.")
        st.markdown("")

        if shared["usage_logs"]:
            df = pd.DataFrame(shared["usage_logs"])
            df.columns = ["Email / Name", "Timestamp", "Question Asked"]
            df = df.iloc[::-1].reset_index(drop=True)  # newest first

            # Summary metrics
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                st.metric("Total Questions", len(shared["usage_logs"]))
            with mc2:
                unique_users = len(set(l["email"] for l in shared["usage_logs"]))
                st.metric("Unique Users", unique_users)
            with mc3:
                if shared["usage_logs"]:
                    last_ts = shared["usage_logs"][-1]["timestamp"]
                    st.metric("Last Activity", last_ts)

            st.markdown("")
            st.dataframe(df, use_container_width=True, hide_index=True)

            if st.button("🗑️ Clear logs"):
                shared["usage_logs"] = []
                st.rerun()
        else:
            st.info("No questions asked yet. Logs will appear here once leadership starts using the portal.")

    # ── Tab 2: Update Content ─────────────────────────────────────────────────
    with tab2:
        st.markdown("#### Update what leadership sees in the 3 cards")
        st.caption("Google Doc is automatically used as AI context. Update the cards below for the structured sections.")

        doc_status = fetch_google_doc()
        if doc_status.startswith("[Could not fetch"):
            st.error(f"⚠️ Google Doc fetch failed: {doc_status}")
        else:
            st.success(f"✅ Google Doc connected · {len(doc_status)} characters fetched · refreshes every 5 mins")

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**🚀 Upcoming Launches**")
            st.caption("Format: `Launch name | Date | Owner`")
            launches_raw = st.text_area("l", height=140, label_visibility="collapsed",
                placeholder="Address Validation v2 | Jun 15 2025 | Priya Mehta\nInternational Support | Aug 1 2025 | Sandra Kim")

            st.markdown("**📅 Meeting Points**")
            st.caption("Format: `Topic | Date`")
            meetings_raw = st.text_area("m", height=140, label_visibility="collapsed",
                placeholder="Track B Kickoff | May 12 2025\nQ3 Roadmap Review | May 20 2025")

        with col2:
            st.markdown("**🏆 Accomplishments**")
            st.caption("One per line")
            accomplishments_raw = st.text_area("a", height=300, label_visibility="collapsed",
                placeholder="Launched address autocomplete for 10 cities\nReduced validation errors by 32%\nCompleted Track A architecture")

        st.markdown("")
        _, btn_col = st.columns([3, 1])
        with btn_col:
            if st.button("💾 Save & Publish", type="primary", use_container_width=True):
                launches = []
                for line in launches_raw.strip().split("\n"):
                    if not line.strip(): continue
                    parts = [p.strip() for p in line.split("|")]
                    launches.append({"name": parts[0], "date": parts[1] if len(parts) > 1 else "", "owner": parts[2] if len(parts) > 2 else ""})

                meetings = []
                for line in meetings_raw.strip().split("\n"):
                    if not line.strip(): continue
                    parts = [p.strip() for p in line.split("|")]
                    meetings.append({"topic": parts[0], "date": parts[1] if len(parts) > 1 else ""})

                accomplishments = [a.strip() for a in accomplishments_raw.strip().split("\n") if a.strip()]

                shared["launches"] = launches
                shared["meetings"] = meetings
                shared["accomplishments"] = accomplishments
                shared["is_populated"] = True
                st.success("✅ Published! Leadership sees updated content instantly.")


# ═══════════════════════════════════════════════════════════════════════════════
# LEADERSHIP PORTAL
# ═══════════════════════════════════════════════════════════════════════════════
else:
    # ── Ask for name/email if not yet submitted ───────────────────────────────
    if not st.session_state.email_submitted:
        st.markdown("## 🗺️ Address Tracks AI")
        st.markdown("Welcome. Please enter your name or email to continue.")
        st.markdown("")
        email_input = st.text_input("Your name or email", placeholder="e.g. Rajesh Kumar or rajesh@flipkart.com")
        c1, c2 = st.columns([1, 5])
        with c1:
            if st.button("Continue →", type="primary"):
                if email_input.strip():
                    st.session_state.user_email = email_input.strip()
                    st.session_state.email_submitted = True
                    st.rerun()
                else:
                    st.error("Please enter your name or email")
        st.stop()

    # ── Header ────────────────────────────────────────────────────────────────
    hc1, hc2 = st.columns([5, 1])
    with hc1:
        st.markdown(f"## 🗺️ Address Tracks AI")
        st.caption(f"<span class='status-dot'></span>Live · Welcome, {st.session_state.user_email}", unsafe_allow_html=True)
    with hc2:
        if st.button("Admin", use_container_width=True):
            st.session_state.show_login = True
            st.rerun()

    st.markdown("")

    # ── 3 Section Cards ───────────────────────────────────────────────────────
    render_cards()

    st.markdown("")
    st.divider()

    # ── Chat area ─────────────────────────────────────────────────────────────
    st.markdown("#### Ask anything about address tracks")

    if not shared["is_populated"]:
        st.info("⏳ Context is being loaded by the admin. Check back shortly.")
        st.stop()

    # Fetch Google Doc as AI context
    doc_content = fetch_google_doc()

    SYSTEM_PROMPT = f"""You are a knowledgeable assistant for senior leadership at Flipkart. \
Answer questions clearly and concisely based strictly on the provided context from the document below. \
If something is not covered, say so honestly. Be direct and executive-friendly — no fluff.

Here is the full context document:
---
{doc_content}
---"""

    # Suggested questions (only when no messages yet)
    if not st.session_state.messages:
        suggestions = [
            "What's the status of each address track?",
            "Which tracks are at risk of delays?",
            "What are the key blockers right now?",
            "What's coming up in the next quarter?",
        ]
        c1, c2 = st.columns(2)
        for i, s in enumerate(suggestions):
            with (c1 if i % 2 == 0 else c2):
                if st.button(s, use_container_width=True, key=f"sug{i}"):
                    st.session_state.messages.append({"role": "user", "content": s})
                    log_usage(st.session_state.user_email, s)
                    st.rerun()
        st.markdown("")

    # Chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Generate AI response
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1000,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                )
                reply = response.content[0].text
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})

    # Chat input
    if prompt := st.chat_input("Ask about timelines, risks, owners, launches…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        log_usage(st.session_state.user_email, prompt)
        st.rerun()
