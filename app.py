import streamlit as st
import anthropic

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Address Tracks AI",
    page_icon="🗺️",
    layout="wide",
)

# ─── Styling ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 0; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #e9ecef; }
    .launch-item { background: white; border: 1px solid #e9ecef; border-radius: 8px; padding: 10px 12px; margin-bottom: 8px; }
    .meeting-item { background: white; border-left: 3px solid #4f8ef7; padding: 8px 12px; margin-bottom: 6px; border-radius: 0 6px 6px 0; }
    .accomplish-item { background: white; border-left: 3px solid #28a745; padding: 8px 12px; margin-bottom: 6px; border-radius: 0 6px 6px 0; }
    div[data-testid="stExpander"] { background: white; border: 1px solid #e9ecef !important; border-radius: 8px; margin-bottom: 6px; }
</style>
""", unsafe_allow_html=True)

# ─── Anthropic client ─────────────────────────────────────────────────────────
client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

# ─── Session state defaults ───────────────────────────────────────────────────
for k, v in {
    "view": "admin",
    "messages": [],
    "launches": [],
    "projects": {},
    "meetings": [],
    "accomplishments": [],
    "raw_context": "",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN VIEW
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.view == "admin":
    st.markdown("### ⚙️ Admin: Load Your Context")
    st.caption("Fill in each section. Leadership will see this structured in the left panel and can ask questions on the right.")
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🚀 Upcoming Launches**")
        st.caption("One per line. Format: `Launch name | Date | Owner`")
        launches_raw = st.text_area("launches", placeholder="Address Validation v2 | Jun 15 2025 | Priya Mehta\nInternational Address Support | Aug 1 2025 | Sandra Kim", height=140, label_visibility="collapsed")

        st.markdown("**📅 Upcoming Meeting Points**")
        st.caption("One per line. Format: `Topic | Date`")
        meetings_raw = st.text_area("meetings", placeholder="Track B Kickoff | May 12 2025\nQ3 Roadmap Review | May 20 2025", height=140, label_visibility="collapsed")

    with col2:
        st.markdown("**⚙️ Ongoing Actions (by Project)**")
        st.caption("Format: `Project Name >> Item 1 | Item 2 | Item 3` — one project per line")
        projects_raw = st.text_area("projects", placeholder="Track A - Core Infra >> Legal sign-off pending | Microservice migration 70% done | Load testing pending\nTrack B - International >> Kickoff deck prep | Accenture onboarding | EU format spec review", height=140, label_visibility="collapsed")

        st.markdown("**🏆 Accomplishments**")
        st.caption("One per line")
        accomplishments_raw = st.text_area("accomplishments", placeholder="Launched address autocomplete for 10 cities\nReduced address validation errors by 32%", height=140, label_visibility="collapsed")

    st.divider()
    st.markdown("**📋 Additional Context for AI (optional)**")
    st.caption("Background, risks, decisions, or anything else leadership might ask about")
    extra_context = st.text_area("extra", placeholder="Track A is blocked on legal sign-off expected by end of May. Track C vendor selection is between vendor X and Y...", height=100, label_visibility="collapsed")

    st.markdown("")
    _, col_btn = st.columns([3, 1])
    with col_btn:
        if st.button("Activate Portal →", type="primary", use_container_width=True):
            # Parse launches
            launches = []
            for line in launches_raw.strip().split("\n"):
                if not line.strip():
                    continue
                parts = [p.strip() for p in line.split("|")]
                launches.append({
                    "name": parts[0],
                    "date": parts[1] if len(parts) > 1 else "",
                    "owner": parts[2] if len(parts) > 2 else "",
                })

            # Parse projects
            projects = {}
            for line in projects_raw.strip().split("\n"):
                if not line.strip():
                    continue
                if ">>" in line:
                    proj, items_str = line.split(">>", 1)
                    projects[proj.strip()] = [i.strip() for i in items_str.split("|") if i.strip()]
                else:
                    projects[line.strip()] = []

            # Parse meetings
            meetings = []
            for line in meetings_raw.strip().split("\n"):
                if not line.strip():
                    continue
                parts = [p.strip() for p in line.split("|")]
                meetings.append({"topic": parts[0], "date": parts[1] if len(parts) > 1 else ""})

            # Parse accomplishments
            accomplishments = [a.strip() for a in accomplishments_raw.strip().split("\n") if a.strip()]

            # Build AI context
            raw_context = f"""UPCOMING LAUNCHES:\n{launches_raw}\n\nONGOING PROJECTS AND ACTIONS:\n{projects_raw}\n\nUPCOMING MEETING POINTS:\n{meetings_raw}\n\nACCOMPLISHMENTS:\n{accomplishments_raw}\n\nADDITIONAL CONTEXT:\n{extra_context}"""

            st.session_state.launches = launches
            st.session_state.projects = projects
            st.session_state.meetings = meetings
            st.session_state.accomplishments = accomplishments
            st.session_state.raw_context = raw_context
            st.session_state.messages = []
            st.session_state.view = "portal"
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PORTAL VIEW
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.view == "portal":

    # ── LEFT SIDEBAR ──────────────────────────────────────────────────────────
    with st.sidebar:
        top_col1, top_col2 = st.columns([4, 1])
        with top_col1:
            st.markdown("## 🗺️ Address Tracks")
        with top_col2:
            if st.button("⚙️", help="Edit context"):
                st.session_state.view = "admin"
                st.rerun()

        # Section 1 — Upcoming Launches
        st.markdown("---")
        st.markdown("**🚀 UPCOMING LAUNCHES**")
        if st.session_state.launches:
            for launch in st.session_state.launches:
                st.markdown(f"""<div class='launch-item'>
                    <strong style='font-size:13px'>{launch['name']}</strong><br>
                    <span style='font-size:11px;color:#6c757d'>{launch['date']}{'&nbsp;·&nbsp;' + launch['owner'] if launch['owner'] else ''}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.caption("No launches added")

        # Section 2 — Ongoing Actions
        st.markdown("---")
        st.markdown("**⚙️ ONGOING ACTIONS**")
        if st.session_state.projects:
            for project, items in st.session_state.projects.items():
                with st.expander(f"**{project}**"):
                    if items:
                        for item in items:
                            st.markdown(f"• {item}")
                    else:
                        st.caption("No items listed")
        else:
            st.caption("No projects added")

        # Section 3 — Upcoming Meeting Points
        st.markdown("---")
        st.markdown("**📅 UPCOMING MEETINGS**")
        if st.session_state.meetings:
            for m in st.session_state.meetings:
                st.markdown(f"""<div class='meeting-item'>
                    <strong style='font-size:13px'>{m['topic']}</strong><br>
                    <span style='font-size:11px;color:#6c757d'>{m['date']}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.caption("No meetings added")

        # Section 4 — Accomplishments
        st.markdown("---")
        st.markdown("**🏆 ACCOMPLISHMENTS**")
        if st.session_state.accomplishments:
            for item in st.session_state.accomplishments:
                st.markdown(f"""<div class='accomplish-item'>
                    <span style='font-size:13px'>{item}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.caption("No accomplishments added")

    # ── RIGHT — CHAT AREA ─────────────────────────────────────────────────────
    st.markdown("### 💬 Ask anything about address tracks")
    st.caption("Powered by Claude · Answers based on context loaded by admin")
    st.divider()

    SYSTEM_PROMPT = f"""You are a knowledgeable assistant for senior leadership at Flipkart. \
Answer questions clearly and concisely based strictly on the provided context. \
If something is not covered in the context, say so honestly rather than guessing. \
Be direct and executive-friendly — no fluff.

Here is the full context:
---
{st.session_state.raw_context}
---"""

    # Suggested questions (only when chat is empty)
    if not st.session_state.messages:
        st.markdown("**Suggested questions:**")
        suggestions = [
            "What's the status of each track?",
            "Which tracks are at risk of delays?",
            "What are our upcoming launches?",
            "What have we accomplished so far?",
        ]
        c1, c2 = st.columns(2)
        for i, s in enumerate(suggestions):
            with (c1 if i % 2 == 0 else c2):
                if st.button(s, use_container_width=True, key=f"sug{i}"):
                    st.session_state.messages.append({"role": "user", "content": s})
                    st.rerun()
        st.markdown("")

    # Render chat history
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
        st.rerun()
