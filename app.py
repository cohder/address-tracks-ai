import streamlit as st
import anthropic

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Address Tracks AI",
    page_icon="🗺️",
    layout="centered",
)

# ─── Styling ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 2rem; max-width: 760px; }
    .stTextArea textarea { font-family: monospace; font-size: 13px; }
    .stChatMessage { border-radius: 12px; }
    div[data-testid="stChatInput"] { border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# ─── Anthropic client ─────────────────────────────────────────────────────────
client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

# ─── Session state defaults ───────────────────────────────────────────────────
if "context" not in st.session_state:
    st.session_state.context = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "view" not in st.session_state:
    st.session_state.view = "admin"

# ─── Header ───────────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("### 🗺️ Address Tracks AI")
with col2:
    if st.session_state.view == "chat":
        if st.button("⚙️ Edit context", use_container_width=True):
            st.session_state.view = "admin"
            st.rerun()

st.divider()

# ─── Admin view ───────────────────────────────────────────────────────────────
if st.session_state.view == "admin":
    st.markdown("#### Admin: load your context")
    st.caption("Paste everything leadership should be able to ask about — roadmap, status, owners, risks, timelines.")

    context = st.text_area(
        label="Context",
        value=st.session_state.context,
        placeholder="""Example:

## Address Track Overview
- Track A (Core Infrastructure): Q2 2025 — migrating legacy address validation to new microservice
- Track B (International Expansion): Q3 2025 — supporting EU address formats
- Track C (Real-time Verification): Q4 2025 — live address lookup with postal API integration

## Current Status
- Track A is 70% complete; blockers: legal sign-off on data residency
- Track B kickoff scheduled for May 12
- Track C in discovery phase

## Key Owners
- Track A: Priya Mehta (eng lead), James O'Brien (PM)
- Track B: Sandra Kim (PM)
- Track C: TBD — headcount request pending
""",
        height=380,
        label_visibility="collapsed",
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        if context.strip():
            st.caption(f"✅ {len(context.strip())} characters loaded")
        else:
            st.caption("No context yet")
    with col2:
        if st.button("Activate portal →", type="primary", use_container_width=True, disabled=not context.strip()):
            st.session_state.context = context
            st.session_state.messages = []
            st.session_state.view = "chat"
            st.rerun()

# ─── Chat view ────────────────────────────────────────────────────────────────
elif st.session_state.view == "chat":
    st.caption("Ask anything about your address tracks")

    SYSTEM_PROMPT = f"""You are a knowledgeable assistant for senior leadership at Flipkart. \
Answer questions clearly and concisely based strictly on the provided context. \
If something is not covered in the context, say so honestly rather than guessing. \
Be direct and executive-friendly — no fluff.

Here is the full context:
---
{st.session_state.context}
---"""

    # Suggested questions (shown only when chat is empty)
    if not st.session_state.messages:
        st.markdown("**Suggested questions:**")
        suggestions = [
            "What's the current status of each address track?",
            "Which tracks are at risk of delays?",
            "Who owns each track?",
            "What's coming in Q4?",
        ]
        cols = st.columns(2)
        for i, suggestion in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(suggestion, use_container_width=True, key=f"sug_{i}"):
                    st.session_state.messages.append({"role": "user", "content": suggestion})
                    st.rerun()
        st.markdown("")

    # Render chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Generate AI response if last message is from user
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1000,
                    system=SYSTEM_PROMPT,
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                )
                reply = response.content[0].text
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})

    # Chat input
    if prompt := st.chat_input("Ask about timelines, owners, risks, what's coming…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
