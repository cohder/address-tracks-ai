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

    /* ── Tighter gap between the 3 top card columns (~60% less than default) ── */
    div[data-testid="stHorizontalBlock"] { gap: 0.35rem !important; }
    div[data-testid="column"] { padding-left: 0.25rem !important; padding-right: 0.25rem !important; }

    /* ── Top-of-screen loading overlay ── */
    .top-loader {
        position: fixed;
        top: 0; left: 0; right: 0;
        z-index: 99999;
        background: #1a3a6b;
        color: white;
        padding: 9px 20px;
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 13px;
        font-weight: 500;
        box-shadow: 0 3px 12px rgba(0,0,0,0.35);
    }
    .top-loader-ring {
        width: 15px; height: 15px;
        border: 2px solid rgba(255,255,255,0.3);
        border-top-color: white;
        border-radius: 50%;
        animation: spin 0.7s linear infinite;
        flex-shrink: 0;
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    /* ── Card title (one step larger than before) ── */
    .card-title {
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        color: #495057;
        margin-bottom: 2px;
        padding-bottom: 3px;
        border-bottom: 1px solid #e9ecef;
    }

    /* ── Compact card item buttons: smaller text + minimal vertical waste ── */
    .compact-btn { margin: 0 !important; padding: 0 !important; line-height: 1 !important; }
    .compact-btn > div[data-testid="stButton"] { margin: 0 !important; padding: 0 !important; }
    .compact-btn > div[data-testid="stButton"] > button {
        background: transparent !important;
        border: none !important;
        border-bottom: 1px solid #f3f4f5 !important;
        border-radius: 0 !important;
        padding: 1px 2px !important;
        margin: 0 !important;
        text-align: left !important;
        font-size: 9px !important;
        color: #343a40 !important;
        box-shadow: none !important;
        height: auto !important;
        min-height: unset !important;
        line-height: 1.15 !important;
        width: 100% !important;
    }
    .compact-btn > div[data-testid="stButton"] > button:hover {
        background: #f0f4ff !important;
        color: #4f8ef7 !important;
    }

    /* ── Metric pills ── */
    .metric-pill { display: inline-block; font-size: 9px; font-weight: 600; padding: 1px 6px; border-radius: 20px; margin: 1px 1px 0 0; }
    .pill-green { background: #d4edda; color: #155724; }
    .pill-blue  { background: #d1ecf1; color: #0c5460; }

    /* ── Back to top ── */
    #back-to-top { position: fixed; bottom: 80px; left: 50%; transform: translateX(-50%); background: #1a1a2e; color: white; border: none; border-radius: 24px; padding: 8px 18px; font-size: 13px; font-weight: 500; cursor: pointer; box-shadow: 0 4px 14px rgba(0,0,0,0.2); display: none; align-items: center; z-index: 9998; }
    #back-to-top:hover { background: #2d2d4e; }

    /* ── FAB ── */
    .fab-container { position: fixed; bottom: 28px; right: 28px; z-index: 9999; display: flex; flex-direction: column; align-items: flex-end; gap: 8px; }
    .fab-options { display: none; flex-direction: column; gap: 6px; align-items: flex-end; }
    .fab-container:hover .fab-options { display: flex; }
    .fab-btn { background: white; border: 1px solid #dee2e6; border-radius: 20px; padding: 7px 14px; font-size: 12px; font-weight: 500; color: #343a40; cursor: pointer; text-decoration: none; box-shadow: 0 2px 8px rgba(0,0,0,0.1); white-space: nowrap; display: block; }
    .fab-btn:hover { background: #f8f9fa; color: #343a40; text-decoration: none; }
    .fab-main { width: 48px; height: 48px; background: #4f8ef7; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 22px; cursor: pointer; box-shadow: 0 4px 12px rgba(79,142,247,0.4); border: none; color: white; line-height: 1; }

    .chat-divider { border: none; border-top: 1px solid #f0f0f0; margin: 0.75rem 0 0.5rem; }

    /* ── Card containers: less internal padding so rows sit tighter ── */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        padding-top: 0.35rem !important;
        padding-bottom: 0.35rem !important;
    }
</style>

<button id="back-to-top" onclick="scrollToTop()">↑ Back to top</button>
<script>
function getScrollEl() { return document.querySelector('[data-testid="stAppViewContainer"]') || document.documentElement; }
function scrollToTop() { var el=getScrollEl(); if(el&&el.scrollTo) el.scrollTo({top:0,behavior:'smooth'}); else window.scrollTo({top:0,behavior:'smooth'}); }
function checkScroll() { var el=getScrollEl(); var btn=document.getElementById('back-to-top'); if(!btn)return; var s=el===window?window.scrollY:el.scrollTop; btn.style.display=s>300?'flex':'none'; }
window.addEventListener('scroll',checkScroll,true);
document.addEventListener('scroll',checkScroll,true);
setInterval(checkScroll,800);
</script>
""", unsafe_allow_html=True)

# ─── Secrets ──────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = st.secrets["ANTHROPIC_API_KEY"]
ADMIN_PASSWORD    = st.secrets["ADMIN_PASSWORD"]
GOOGLE_DOC_URL    = st.secrets["GOOGLE_DOC_URL"]
ADMIN_EMAIL       = st.secrets.get("ADMIN_EMAIL", "admin@flipkart.com")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def _viewer_identity():
    """Streamlit Cloud can expose logged-in user; locally this is usually unset."""
    try:
        u = getattr(st, "user", None)
        if u is None:
            return None
        email = getattr(u, "email", None)
        if email:
            return str(email).strip() or None
    except Exception:
        pass
    return None


@st.cache_resource
def get_shared_store():
    return {"usage_logs": []}

shared = get_shared_store()

for k, v in {
    "messages": [],
    "is_admin": False,
    "show_login": False,
    "popup_state": None,
    "popup_type": None,
    "popup_item": None,
    "popup_detail": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ═══════════════════════════════════════════════════════════════════════════════
# DATA
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def fetch_google_doc(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.text
    except Exception:
        return None


@st.cache_data(ttl=300)
def extract_cards_from_doc(doc_content, api_key):
    c = anthropic.Anthropic(api_key=api_key)
    prompt = f"""Read this document and extract structured data. Return ONLY valid JSON, no markdown fences.

Extract:
1. upcoming_launches: max 6 objects: "name"(≤40 chars), "date"(short), "owner", "summary", "metrics_impact"(list from [Misroutes,RTO,Reachability,Drift,Text Quality,Delivery Promise Breach])
2. meeting_points: max 6 objects: "topic"(≤40 chars), "date", "summary", "launches_covered", "metrics_focus"(same list)
3. accomplishments: max 6 objects: "title"(≤35 chars), "impact"(≤20 chars e.g. "-20bps Misroutes"), "time"(e.g. "Jan'26"), "details", "metrics_impact"

Use "" for missing strings, [] for missing lists. Only include what is clearly in the document.

Document:
---
{doc_content}
---

Return exactly:
{{"upcoming_launches":[{{"name":"","date":"","owner":"","summary":"","metrics_impact":[]}}],"meeting_points":[{{"topic":"","date":"","summary":"","launches_covered":[],"metrics_focus":[]}}],"accomplishments":[{{"title":"","impact":"","time":"","details":"","metrics_impact":[]}}]}}"""
    try:
        response = c.messages.create(model="claude-sonnet-4-6", max_tokens=2000,
            messages=[{"role": "user", "content": prompt}])
        raw = response.content[0].text.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"): raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        return {"upcoming_launches": [], "meeting_points": [], "accomplishments": [], "error": str(e)}


def get_item_detail(item_type, item, doc_content):
    c = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompts = {
        "launch":         f"Detailed leadership briefing on launch: \"{item.get('name')}\". Cover: what it is, why it matters, status, timeline, owner, risks, impact on Misroutes/RTO/Reachability/Drift/Text Quality/Delivery Promise Breach. Numbers. Clear headers. Under 300 words.",
        "meeting":        f"Detailed briefing for meeting: \"{item.get('topic')}\". Cover: agenda, launches discussed, decisions expected, metric improvements on Misroutes/RTO/Reachability/Drift/Text Quality/Delivery Promise Breach. Numbers. Clear headers. Under 300 words.",
        "accomplishment": f"Detailed briefing on accomplishment: \"{item.get('title')}\". Cover: what was done, when, who, problem solved, measurable impact on Misroutes/RTO/Reachability/Drift/Text Quality/Delivery Promise Breach. Numbers. Clear headers. Under 300 words.",
    }
    try:
        response = c.messages.create(model="claude-sonnet-4-6", max_tokens=600,
            system="Concise executive assistant. Clear headers, bullet points, specific numbers.",
            messages=[{"role": "user", "content": prompts[item_type] + f"\n\nDocument:\n---\n{doc_content}\n---"}])
        return response.content[0].text
    except Exception as e:
        return f"Could not load details: {str(e)}"


def metric_pills(metrics):
    if not metrics: return ""
    colors = ["pill-green", "pill-blue"] * 6
    return "".join(f"<span class='metric-pill {colors[i]}'>{m}</span>" for i, m in enumerate(metrics))

def log_usage(name, question):
    shared["usage_logs"].append({"email": name or "unknown",
        "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p"), "question": question})

def render_fab():
    viewer = _viewer_identity() or "unknown"
    bug_url     = f"https://mail.google.com/mail/?view=cm&to={ADMIN_EMAIL}&su=Bug+Report+%7C+Address_Chhotu&body=Hi%2C%0A%0ABug%3A%0A%0A[Describe]%0A%0AFrom%3A+{viewer}"
    contact_url = f"https://mail.google.com/mail/?view=cm&to={ADMIN_EMAIL}&su=Query+%7C+Address_Chhotu&body=Hi%2C%0A%0AQuery%3A%0A%0A[Message]%0A%0AFrom%3A+{viewer}"
    st.markdown(f"""<div class="fab-container"><div class="fab-options">
        <a href="{bug_url}" target="_blank" class="fab-btn">🐛 Report a Bug / Feedback</a>
        <a href="{contact_url}" target="_blank" class="fab-btn">📬 Contact Admin</a>
    </div><div class="fab-main" title="Help">💬</div></div>""", unsafe_allow_html=True)


# ─── Popup ────────────────────────────────────────────────────────────────────
@st.dialog("Details", width="large")
def show_popup():
    item      = st.session_state.popup_item or {}
    item_type = st.session_state.popup_type
    detail    = st.session_state.popup_detail or ""
    if item_type == "launch":
        st.markdown(f"## 🚀 {item.get('name','')}")
        meta = []
        if item.get("date"):  meta.append(f"📅 {item['date']}")
        if item.get("owner"): meta.append(f"👤 {item['owner']}")
        if meta: st.caption("  ·  ".join(meta))
    elif item_type == "meeting":
        st.markdown(f"## 📅 {item.get('topic','')}")
        if item.get("date"): st.caption(f"📅 {item['date']}")
        if item.get("launches_covered"): st.caption(f"Launches: {', '.join(item['launches_covered'])}")
    elif item_type == "accomplishment":
        st.markdown(f"## ✅ {item.get('title','')}")
        meta = []
        if item.get("time"):   meta.append(f"📅 {item['time']}")
        if item.get("impact"): meta.append(f"📈 {item['impact']}")
        if meta: st.caption("  ·  ".join(meta))
    metrics = item.get("metrics_impact") or item.get("metrics_focus") or []
    if metrics: st.markdown(metric_pills(metrics), unsafe_allow_html=True)
    st.divider()
    st.markdown(detail)
    if st.button("Close", key="popup_close"):
        st.session_state.popup_state = None
        st.rerun()


# ─── Card button ──────────────────────────────────────────────────────────────
def card_button(label, key, item, item_type):
    st.markdown("<div class='compact-btn'>", unsafe_allow_html=True)
    if st.button(label, key=key, use_container_width=True):
        st.session_state.popup_state = "loading"
        st.session_state.popup_type  = item_type
        st.session_state.popup_item  = item
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ─── Cards ────────────────────────────────────────────────────────────────────
def render_cards(cards, doc_content):
    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container(border=True):
            st.markdown("<div class='card-title'>🚀 Upcoming Launches</div>", unsafe_allow_html=True)
            launches = cards.get("upcoming_launches", [])
            if not launches:
                st.caption("Nothing found in doc yet")
            else:
                for i, l in enumerate(launches[:4]):
                    name = (l.get("name","") or "")[:40]
                    date = l.get("date","") or ""
                    card_button(f"🚀 {name}" + (f"  ·  {date}" if date else ""), f"launch_{i}", l, "launch")
                if len(launches) > 4:
                    with st.expander(f"+ {len(launches)-4} more"):
                        for i, l in enumerate(launches[4:]):
                            name = (l.get("name","") or "")[:40]
                            date = l.get("date","") or ""
                            card_button(f"🚀 {name}" + (f"  ·  {date}" if date else ""), f"launch_e_{i}", l, "launch")

    with col2:
        with st.container(border=True):
            st.markdown("<div class='card-title'>📅 Meeting Points</div>", unsafe_allow_html=True)
            meetings = cards.get("meeting_points", [])
            if not meetings:
                st.caption("Nothing found in doc yet")
            else:
                for i, m in enumerate(meetings[:4]):
                    card_button(f"📅 {(m.get('topic','') or '')[:40]}", f"meeting_{i}", m, "meeting")
                if len(meetings) > 4:
                    with st.expander(f"+ {len(meetings)-4} more"):
                        for i, m in enumerate(meetings[4:]):
                            card_button(f"📅 {(m.get('topic','') or '')[:40]}", f"meeting_e_{i}", m, "meeting")

    with col3:
        with st.container(border=True):
            st.markdown("<div class='card-title'>🏆 Accomplishments</div>", unsafe_allow_html=True)
            accomplishments = cards.get("accomplishments", [])
            if not accomplishments:
                st.caption("Nothing found in doc yet")
            else:
                for i, a in enumerate(accomplishments[:4]):
                    title  = (a.get("title","") or "")[:35]
                    impact = (a.get("impact","") or "")[:20]
                    card_button(f"✅ {title}" + (f"  ·  {impact}" if impact else ""), f"accomp_{i}", a, "accomplishment")
                if len(accomplishments) > 4:
                    with st.expander(f"+ {len(accomplishments)-4} more"):
                        for i, a in enumerate(accomplishments[4:]):
                            title  = (a.get("title","") or "")[:35]
                            impact = (a.get("impact","") or "")[:20]
                            card_button(f"✅ {title}" + (f"  ·  {impact}" if impact else ""), f"accomp_e_{i}", a, "accomplishment")


# ─── Loading — fixed top overlay ──────────────────────────────────────────────
def handle_loading(doc_content):
    if st.session_state.popup_state != "loading":
        return
    item = st.session_state.popup_item or {}
    name = item.get("name") or item.get("topic") or item.get("title") or "item"
    # Fixed banner at top of screen — visible regardless of scroll
    st.markdown(f"""<div class="top-loader">
        <div class="top-loader-ring"></div>
        <span>Fetching details for <strong>{name}</strong>…</span>
    </div>""", unsafe_allow_html=True)
    # Cancel button — centred below the banner
    _, cc, _ = st.columns([2, 1, 2])
    with cc:
        if st.button("✕  Cancel", key="cancel_load", use_container_width=True):
            st.session_state.popup_state = None
            st.rerun()
    with st.spinner("Loading…"):
        detail = get_item_detail(st.session_state.popup_type, item, doc_content)
    st.session_state.popup_detail = detail
    st.session_state.popup_state  = "ready"
    st.rerun()


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
                st.session_state.is_admin   = True
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
    doc_content = fetch_google_doc(GOOGLE_DOC_URL)
    if doc_content:
        st.success(f"✅ Google Doc connected · {len(doc_content):,} chars · refreshes every 5 mins")
        with st.expander("👀 Preview extraction"):
            cards = extract_cards_from_doc(doc_content, ANTHROPIC_API_KEY)
            if "error" in cards:
                st.error(f"Error: {cards['error']}")
            else:
                for l in cards.get("upcoming_launches", []):
                    st.markdown(f"- **Launch:** {l['name']} · {l.get('date','')} · {', '.join(l.get('metrics_impact',[]))}")
                for m in cards.get("meeting_points", []):
                    st.markdown(f"- **Meeting:** {m['topic']} · {m.get('date','')} · {', '.join(m.get('metrics_focus',[]))}")
                for a in cards.get("accomplishments", []):
                    st.markdown(f"- **Accomplishment:** {a['title']} · {a.get('impact','')} · {a.get('time','')}")
        if st.button("🔄 Force refresh"):
            fetch_google_doc.clear()
            extract_cards_from_doc.clear()
            st.success("Cache cleared.")
            st.rerun()
    else:
        st.error("⚠️ Could not fetch Google Doc.")
    st.divider()
    st.markdown("#### 📊 Usage Tracking")
    if shared["usage_logs"]:
        mc1, mc2, mc3 = st.columns(3)
        with mc1: st.metric("Total Questions", len(shared["usage_logs"]))
        with mc2: st.metric("Unique Users", len(set(l["email"] for l in shared["usage_logs"])))
        with mc3: st.metric("Last Activity", shared["usage_logs"][-1]["timestamp"])
        df = pd.DataFrame(shared["usage_logs"][::-1])
        df.columns = ["Name / Email", "Timestamp", "Question"]
        st.dataframe(df, use_container_width=True, hide_index=True)
        if st.button("🗑️ Clear logs"):
            shared["usage_logs"] = []
            st.rerun()
    else:
        st.info("No questions asked yet.")

else:
    doc_content = fetch_google_doc(GOOGLE_DOC_URL)
    if not doc_content:
        st.error("⚠️ Could not load content. Please try again shortly.")
        st.stop()

    # Loading overlay — called FIRST so it renders at top of page
    handle_loading(doc_content)

    # Popup
    if st.session_state.popup_state == "ready":
        show_popup()

    with st.spinner("Syncing latest updates…"):
        cards = extract_cards_from_doc(doc_content, ANTHROPIC_API_KEY)

    viewer_email = _viewer_identity()
    hello_line = (
        f"Hello, <strong>{viewer_email}</strong>"
        if viewer_email
        else "Hello"
    )

    # ── Header ────────────────────────────────────────────────────────────────
    h1, h2 = st.columns([5, 1])
    with h1:
        st.markdown("## 🤵 Address_Chhotu")
        st.markdown(
            f"<p style='font-size:13px;color:#495057;margin:2px 0 0'>{hello_line} · Synced from source doc</p>",
            unsafe_allow_html=True,
        )
    with h2:
        st.markdown("<div style='padding-top:12px'>", unsafe_allow_html=True)
        if st.button("Admin", use_container_width=True):
            st.session_state.show_login = True
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

    # ── 3 Cards ───────────────────────────────────────────────────────────────
    render_cards(cards, doc_content)

    # ── Chat ──────────────────────────────────────────────────────────────────
    st.markdown("<hr class='chat-divider'>", unsafe_allow_html=True)
    st.markdown("#### 💬 Ask anything about address tracks")
    st.caption("Chat bar stays pinned at the bottom · Scroll down to read responses")

    SYSTEM_PROMPT = f"""You are a sharp, executive-focused assistant for Flipkart leadership.
- Answer ONLY from the context document
- Be direct, no filler phrases
- Use **bold** for key terms/numbers, bullets for 3+ items, short paragraphs
- Highlight metric improvements (Misroutes, RTO, Reachability, Drift, Text Quality, Delivery Promise Breach) with numbers
- If not in document, say so in one line
- Under 200 words

Context:
---
{doc_content}
---"""

    _log_name = viewer_email or "anonymous"

    if not st.session_state.messages:
        suggestions = [
            "What's the status of each address track?",
            "Which tracks are at risk of delays?",
            "How will our launches improve misroutes and RTO?",
            "What's coming up next quarter?",
        ]
        c1, c2 = st.columns(2)
        for i, s in enumerate(suggestions):
            with (c1 if i % 2 == 0 else c2):
                if st.button(s, use_container_width=True, key=f"sug{i}"):
                    st.session_state.messages.append({"role": "user", "content": s})
                    log_usage(_log_name, s)
                    st.rerun()
        st.markdown("")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

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
                        model="claude-sonnet-4-6", max_tokens=800,
                        system=SYSTEM_PROMPT, messages=cleaned)
                    reply = response.content[0].text
                except Exception as e:
                    reply = f"Error: {str(e)}"
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})

    if prompt := st.chat_input("Ask about timelines, risks, owners, launches…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        log_usage(_log_name, prompt)
        st.rerun()

    render_fab()
