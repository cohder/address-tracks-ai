import streamlit as st
import anthropic
import requests
import json
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Address_Chhotu", page_icon="🤵", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    header[data-testid="stHeader"] { display: none; }
    div[data-testid="stDecoration"] { display: none; }
    .block-container { padding-top: 0.75rem !important; padding-bottom: 6rem; max-width: 1100px; }
    .section-card { background: white; border: 1px solid #e9ecef; border-radius: 12px; padding: 14px 16px; min-height: 220px; }
    .section-title { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.09em; color: #6c757d; margin-bottom: 10px; padding-bottom: 7px; border-bottom: 1px solid #f0f0f0; }
    .accomp-row { display: flex; justify-content: space-between; align-items: flex-start; padding: 6px 0; border-bottom: 1px solid #f8f9fa; gap: 8px; }
    .accomp-row:last-child { border-bottom: none; }
    .accomp-activity { font-size: 13px; color: #212529; font-weight: 500; flex: 1; }
    .accomp-impact { font-size: 12px; color: #28a745; font-weight: 600; white-space: nowrap; text-align: right; }
    .accomp-time { font-size: 10px; color: #adb5bd; margin-top: 1px; text-align: right; }
    .metric-pill { display: inline-block; font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 20px; margin: 2px 2px 0 0; }
    .pill-green { background: #d4edda; color: #155724; }
    .pill-blue { background: #d1ecf1; color: #0c5460; }
    #back-to-top { position: fixed; bottom: 80px; left: 50%; transform: translateX(-50%); background: #1a1a2e; color: white; border: none; border-radius: 24px; padding: 8px 18px; font-size: 13px; font-weight: 500; cursor: pointer; box-shadow: 0 4px 14px rgba(0,0,0,0.2); display: none; align-items: center; gap: 6px; z-index: 9998; }
    #back-to-top:hover { background: #2d2d4e; }
    .fab-container { position: fixed; bottom: 28px; right: 28px; z-index: 9999; display: flex; flex-direction: column; align-items: flex-end; gap: 8px; }
    .fab-options { display: none; flex-direction: column; gap: 6px; align-items: flex-end; }
    .fab-container:hover .fab-options { display: flex; }
    .fab-btn { background: white; border: 1px solid #dee2e6; border-radius: 20px; padding: 7px 14px; font-size: 12px; font-weight: 500; color: #343a40; cursor: pointer; text-decoration: none; box-shadow: 0 2px 8px rgba(0,0,0,0.1); white-space: nowrap; display: block; }
    .fab-btn:hover { background: #f8f9fa; color: #343a40; text-decoration: none; }
    .fab-main { width: 48px; height: 48px; background: #4f8ef7; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 22px; cursor: pointer; box-shadow: 0 4px 12px rgba(79,142,247,0.4); border: none; color: white; line-height: 1; }
    .chat-divider { border: none; border-top: 1px solid #f0f0f0; margin: 1rem 0 0.5rem; }
</style>
<button id="back-to-top" onclick="window.scrollTo({top:0,behavior:'smooth'})">↑ Back to top</button>
<script>
    window.addEventListener('scroll', function() {
        var btn = document.getElementById('back-to-top');
        if (!btn) return;
        btn.style.display = window.scrollY > 320 ? 'flex' : 'none';
    });
</script>
""", unsafe_allow_html=True)

# ─── Secrets ──────────────────────────────────────────────────────────────────
client         = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
GOOGLE_DOC_URL = st.secrets["GOOGLE_DOC_URL"]
ADMIN_EMAIL    = st.secrets.get("ADMIN_EMAIL", "admin@flipkart.com")

@st.cache_resource
def get_shared_store():
    return {"usage_logs": []}

shared = get_shared_store()

for k, v in {"messages": [], "is_admin": False, "show_login": False, "user_email": "", "email_submitted": False}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── Data fetching ────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_google_doc():
    try:
        r = requests.get(GOOGLE_DOC_URL, timeout=10)
        r.raise_for_status()
        return r.text
    except:
        return None

@st.cache_data(ttl=300)
def extract_cards_from_doc(doc_content):
    prompt = f"""Read this document and extract structured data. Return ONLY valid JSON, no explanation, no markdown fences.

Extract:
1. upcoming_launches: list of max 6 objects with "name", "date", "owner", "summary", "metrics_impact" (list from [Misroutes, RTO, Reachability, Drift, Text Quality, Delivery Promise Breach])
2. meeting_points: list of max 6 objects with "topic", "date", "summary", "launches_covered", "metrics_focus" (list from same)
3. accomplishments: list of max 6 objects with "title", "impact" (e.g. "-12% Misroutes"), "time" (e.g. "Jan'26"), "details", "metrics_impact"

Only include what is clearly in the document. Use "" for missing strings, [] for missing lists.

Document:
---
{doc_content}
---

Return exactly:
{{"upcoming_launches":[{{"name":"","date":"","owner":"","summary":"","metrics_impact":[]}}],"meeting_points":[{{"topic":"","date":"","summary":"","launches_covered":[],"metrics_focus":[]}}],"accomplishments":[{{"title":"","impact":"","time":"","details":"","metrics_impact":[]}}]}}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        return {"upcoming_launches": [], "meeting_points": [], "accomplishments": [], "error": str(e)}

def get_item_detail(item_type, item, doc_content):
    prompts = {
        "launch": f"Detailed leadership briefing on launch: \"{item.get('name')}\". Cover: what it is, why it matters, status, timeline, owner, risks, impact on Misroutes/RTO/Reachability/Drift/Text Quality/Delivery Promise Breach. Use numbers. Clear headers. Under 300 words.",
        "meeting": f"Detailed briefing for meeting: \"{item.get('topic')}\". Cover: agenda, launches discussed, decisions expected, metric improvements on Misroutes/RTO/Reachability/Drift/Text Quality/Delivery Promise Breach. Use numbers. Clear headers. Under 300 words.",
        "accomplishment": f"Detailed briefing on accomplishment: \"{item.get('title')}\". Cover: what was done, when, who, problem solved, measurable impact on Misroutes/RTO/Reachability/Drift/Text Quality/Delivery Promise Breach. Use numbers. Clear headers. Under 300 words.",
    }
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            system="Concise executive assistant. Use clear headers and bullet points. Be specific with numbers.",
            messages=[{"role": "user", "content": prompts[item_type] + f"\n\nDocument:\n---\n{doc_content}\n---"}],
        )
        return response.content[0].text
    except:
        return "Could not load details. Please try again."

def metric_pills(metrics):
    if not metrics:
        return ""
    colors = ["pill-green", "pill-blue"] * 6
    return "".join(f"<span class='metric-pill {colors[i]}'>{m}</span>" for i, m in enumerate(metrics))

def log_usage(email, question):
    shared["usage_logs"].append({"email": email, "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p"), "question": question})

def render_fab():
    user = st.session_state.get("user_email", "")
    bug_url     = f"https://mail.google.com/mail/?view=cm&to={ADMIN_EMAIL}&su=Bug+Report+%7C+Address_Chhotu&body=Hi%2C%0A%0ABug%3A%0A%0A[Describe]%0A%0AName%3A+{user}"
    contact_url = f"https://mail.google.com/mail/?view=cm&to={ADMIN_EMAIL}&su=Query+%7C+Address_Chhotu&body=Hi%2C%0A%0AQuery%3A%0A%0A[Message]%0A%0AName%3A+{user}"
    st.markdown(f"""<div class="fab-container"><div class="fab-options"><a href="{bug_url}" target="_blank" class="fab-btn">🐛 Report a Bug / Feedback</a><a href="{contact_url}" target="_blank" class="fab-btn">📬 Contact Admin</a></div><div class="fab-main" title="Contact & Help">💬</div></div>""", unsafe_allow_html=True)

# ─── Popups ───────────────────────────────────────────────────────────────────
@st.dialog("Launch Details", width="large")
def launch_popup(item, doc_content):
    st.markdown(f"## 🚀 {item.get('name','')}")
    meta = []
    if item.get("date"):  meta.append(f"📅 {item['date']}")
    if item.get("owner"): meta.append(f"👤 {item['owner']}")
    if meta: st.caption("  ·  ".join(meta))
    if item.get("metrics_impact"): st.markdown(metric_pills(item["metrics_impact"]), unsafe_allow_html=True)
    st.divider()
    with st.spinner("Loading details…"):
        st.markdown(get_item_detail("launch", item, doc_content))

@st.dialog("Meeting Details", width="large")
def meeting_popup(item, doc_content):
    st.markdown(f"## 📅 {item.get('topic','')}")
    if item.get("date"): st.caption(f"📅 {item['date']}")
    if item.get("metrics_focus"):
        st.markdown("**Metrics focus:**")
        st.markdown(metric_pills(item["metrics_focus"]), unsafe_allow_html=True)
    if item.get("launches_covered"): st.caption(f"Launches covered: {', '.join(item['launches_covered'])}")
    st.divider()
    with st.spinner("Loading details…"):
        st.markdown(get_item_detail("meeting", item, doc_content))

@st.dialog("Accomplishment Details", width="large")
def accomplishment_popup(item, doc_content):
    st.markdown(f"## ✅ {item.get('title','')}")
    meta = []
    if item.get("time"):   meta.append(f"📅 {item['time']}")
    if item.get("impact"): meta.append(f"📈 {item['impact']}")
    if meta: st.caption("  ·  ".join(meta))
    if item.get("metrics_impact"): st.markdown(metric_pills(item["metrics_impact"]), unsafe_allow_html=True)
    st.divider()
    with st.spinner("Loading details…"):
        st.markdown(get_item_detail("accomplishment", item, doc_content))

# ─── Cards ────────────────────────────────────────────────────────────────────
def render_cards(cards, doc_content):
    col1, col2, col3 = st.columns(3)

    with col1:
        launches = cards.get("upcoming_launches", [])
        st.markdown("<div class='section-card'><div class='section-title'>🚀 Upcoming Launches</div>", unsafe_allow_html=True)
        if launches:
            for i, l in enumerate(launches):
                if st.button(f"🚀 **{l.get('name','')}**  \n{l.get('date','')}{'  ·  ' + l['owner'] if l.get('owner') else ''}", key=f"launch_{i}", use_container_width=True, help="Click for details"):
                    launch_popup(l, doc_content)
                if l.get("metrics_impact"): st.markdown(metric_pills(l["metrics_impact"]), unsafe_allow_html=True)
                st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        else:
            st.caption("Nothing found in doc yet")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        meetings = cards.get("meeting_points", [])
        st.markdown("<div class='section-card'><div class='section-title'>📅 Meeting Points</div>", unsafe_allow_html=True)
        if meetings:
            for i, m in enumerate(meetings):
                if st.button(f"📅 **{m.get('topic','')}**  \n{m.get('date','')}", key=f"meeting_{i}", use_container_width=True, help="Click for metrics & agenda"):
                    meeting_popup(m, doc_content)
                if m.get("metrics_focus"): st.markdown(metric_pills(m["metrics_focus"]), unsafe_allow_html=True)
                st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        else:
            st.caption("Nothing found in doc yet")
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        accomplishments = cards.get("accomplishments", [])
        st.markdown("<div class='section-card'><div class='section-title'>🏆 Accomplishments</div>", unsafe_allow_html=True)
        if accomplishments:
            for i, a in enumerate(accomplishments):
                impact_html = f"<div class='accomp-impact'>{a.get('impact','')}</div><div class='accomp-time'>{a.get('time','')}</div>" if (a.get("impact") or a.get("time")) else ""
                st.markdown(f"<div class='accomp-row'><div class='accomp-activity'>✅ {a.get('title','')}</div><div>{impact_html}</div></div>", unsafe_allow_html=True)
                if st.button("View details →", key=f"accomp_{i}", help="Click for full details"):
                    accomplishment_popup(a, doc_content)
                if a.get("metrics_impact"): st.markdown(metric_pills(a["metrics_impact"]), unsafe_allow_html=True)
                st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)
        else:
            st.caption("Nothing found in doc yet")
        st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTING
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

elif st.session_state.is_admin:
    hc1, hc2 = st.columns([4, 1])
    with hc1:
        st.markdown("### 🤵 Address_Chhotu — Admin Panel")
    with hc2:
        if st.button("Sign out", use_container_width=True):
            st.session_state.is_admin = False
            st.rerun()

    st.divider()
    doc_content = fetch_google_doc()
    if doc_content:
        st.success(f"✅ Google Doc connected · {len(doc_content):,} characters · refreshes every 5 mins")
        with st.expander("👀 Preview Claude extraction"):
            cards = extract_cards_from_doc(doc_content)
            if "error" in cards:
                st.error(f"Extraction error: {cards['error']}")
            else:
                st.markdown("**Launches:**")
                for l in cards.get("upcoming_launches", []):
                    st.markdown(f"- {l['name']} · {l.get('date','')} · {l.get('owner','')} · {', '.join(l.get('metrics_impact',[]))}")
                st.markdown("**Meetings:**")
                for m in cards.get("meeting_points", []):
                    st.markdown(f"- {m['topic']} · {m.get('date','')} · {', '.join(m.get('metrics_focus',[]))}")
                st.markdown("**Accomplishments:**")
                for a in cards.get("accomplishments", []):
                    st.markdown(f"- {a['title']} · {a.get('impact','')} · {a.get('time','')} · {', '.join(a.get('metrics_impact',[]))}")
        if st.button("🔄 Force refresh now"):
            fetch_google_doc.clear()
            extract_cards_from_doc.clear()
            st.success("Cache cleared.")
            st.rerun()
    else:
        st.error("⚠️ Could not fetch Google Doc. Check GOOGLE_DOC_URL in Streamlit Secrets.")

    st.divider()
    st.markdown("#### 📊 Usage Tracking")
    if shared["usage_logs"]:
        mc1, mc2, mc3 = st.columns(3)
        with mc1: st.metric("Total Questions", len(shared["usage_logs"]))
        with mc2: st.metric("Unique Users", len(set(l["email"] for l in shared["usage_logs"])))
        with mc3: st.metric("Last Activity", shared["usage_logs"][-1]["timestamp"])
        df = pd.DataFrame(shared["usage_logs"][::-1])
        df.columns = ["Email / Name", "Timestamp", "Question Asked"]
        st.dataframe(df, use_container_width=True, hide_index=True)
        if st.button("🗑️ Clear logs"):
            shared["usage_logs"] = []
            st.rerun()
    else:
        st.info("No questions asked yet.")

else:
    # ── Email gate ────────────────────────────────────────────────────────────
    if not st.session_state.email_submitted:
        st.markdown("## 🤵 Address_Chhotu")
        st.markdown("Welcome. Please enter your name or email to continue.")
        st.markdown("")
        email_input = st.text_input("Your name or email", placeholder="e.g. Rajesh Kumar or rajesh@flipkart.com")
        c1, _ = st.columns([1, 5])
        with c1:
            if st.button("Continue →", type="primary"):
                if email_input.strip():
                    st.session_state.user_email = email_input.strip()
                    st.session_state.email_submitted = True
                    st.rerun()
                else:
                    st.error("Please enter your name or email")
        st.stop()

    # ── Fetch doc ─────────────────────────────────────────────────────────────
    doc_content = fetch_google_doc()
    if not doc_content:
        st.error("⚠️ Could not load content. Please try again shortly.")
        st.stop()

    with st.spinner("Syncing latest updates…"):
        cards = extract_cards_from_doc(doc_content)

    # ── Header ────────────────────────────────────────────────────────────────
    h1, h2 = st.columns([5, 1])
    with h1:
        st.markdown("## 🤵 Address_Chhotu")
        st.caption(f"Welcome, {st.session_state.user_email} · Synced from source doc")
    with h2:
        st.markdown("<div style='padding-top:12px'>", unsafe_allow_html=True)
        if st.button("Admin", use_container_width=True):
            st.session_state.show_login = True
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("")

    # ── 3 Cards ───────────────────────────────────────────────────────────────
    render_cards(cards, doc_content)

    # ── Chat ──────────────────────────────────────────────────────────────────
    st.markdown("<hr class='chat-divider'>", unsafe_allow_html=True)
    st.markdown("#### 💬 Ask anything about address tracks")
    st.caption("Scroll down to read responses · Chat bar stays pinned at the bottom")

    SYSTEM_PROMPT = f"""You are a sharp, executive-focused assistant for Flipkart leadership.
Rules:
- Answer ONLY from the context document provided
- Be direct — no filler phrases
- Format every response for quick scanning:
  * Use **bold** for key terms and numbers
  * Bullet points for lists of 3 or more items
  * Short paragraphs — 2-3 lines max
  * Call out metric improvements (Misroutes, RTO, Reachability, Drift, Text Quality, Delivery Promise Breach) with numbers where available
- If not in the document, say so in one line
- Keep responses under 200 words

Context document:
---
{doc_content}
---"""

    # Suggested questions
    if not st.session_state.messages:
        suggestions = [
            "What's the status of each address track?",
            "Which tracks are at risk of delays?",
            "How will our launches improve misroutes and RTO?",
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

    # Render messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Generate AI response
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                cleaned = []
                for msg in st.session_state.messages:
                    if cleaned and cleaned[-1]["role"] == msg["role"]:
                        cleaned[-1] = {"role": msg["role"], "content": msg["content"]}
                    else:
                        cleaned.append({"role": msg["role"], "content": msg["content"]})
                if cleaned and cleaned[0]["role"] != "user":
                    cleaned = cleaned[1:]
                try:
                    response = client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=800,
                        system=SYSTEM_PROMPT,
                        messages=cleaned,
                    )
                    reply = response.content[0].text
                except Exception as e:
                    reply = "Sorry, something went wrong. Please try asking again."
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})

    # Sticky chat input
    if prompt := st.chat_input("Ask about timelines, risks, owners, launches…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        log_usage(st.session_state.user_email, prompt)
        st.rerun()

    # Floating contact button
    render_fab()
