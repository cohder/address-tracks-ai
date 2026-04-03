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

    .section-card {
        background: white;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 10px 12px;
        height: 220px;
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }
    .section-title {
        font-size: 9px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        color: #6c757d;
        margin-bottom: 6px;
        padding-bottom: 5px;
        border-bottom: 1px solid #f0f0f0;
        flex-shrink: 0;
    }
    .card-scroll {
        overflow-y: auto;
        flex: 1;
        padding-right: 2px;
    }
    .card-scroll::-webkit-scrollbar { width: 3px; }
    .card-scroll::-webkit-scrollbar-track { background: transparent; }
    .card-scroll::-webkit-scrollbar-thumb { background: #dee2e6; border-radius: 3px; }
    .card-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 4px 0;
        border-bottom: 1px solid #f8f9fa;
        gap: 6px;
        min-height: 26px;
    }
    .card-row:last-child { border-bottom: none; }
    .card-name { font-size: 11px; color: #212529; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; }
    .card-date { font-size: 10px; color: #adb5bd; white-space: nowrap; flex-shrink: 0; }
    .accomp-row-wrap { padding: 4px 0; border-bottom: 1px solid #f8f9fa; }
    .accomp-row-wrap:last-child { border-bottom: none; }
    .accomp-top { display: flex; justify-content: space-between; align-items: center; gap: 6px; }
    .accomp-name { font-size: 11px; color: #212529; font-weight: 500; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .accomp-impact-inline { font-size: 10px; color: #28a745; font-weight: 600; white-space: nowrap; flex-shrink: 0; }
    .metric-pill { display: inline-block; font-size: 9px; font-weight: 600; padding: 1px 6px; border-radius: 20px; margin: 1px 1px 0 0; }
    .pill-green { background: #d4edda; color: #155724; }
    .pill-blue { background: #d1ecf1; color: #0c5460; }

    /* Back to top — fixed to viewport bottom-center */
    #back-to-top {
        position: fixed;
        bottom: 80px;
        left: 50%;
        transform: translateX(-50%);
        background: #1a1a2e;
        color: white;
        border: none;
        border-radius: 24px;
        padding: 8px 18px;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        box-shadow: 0 4px 14px rgba(0,0,0,0.2);
        display: none;
        align-items: center;
        gap: 6px;
        z-index: 9998;
    }
    #back-to-top:hover { background: #2d2d4e; }

    .fab-container { position: fixed; bottom: 28px; right: 28px; z-index: 9999; display: flex; flex-direction: column; align-items: flex-end; gap: 8px; }
    .fab-options { display: none; flex-direction: column; gap: 6px; align-items: flex-end; }
    .fab-container:hover .fab-options { display: flex; }
    .fab-btn { background: white; border: 1px solid #dee2e6; border-radius: 20px; padding: 7px 14px; font-size: 12px; font-weight: 500; color: #343a40; cursor: pointer; text-decoration: none; box-shadow: 0 2px 8px rgba(0,0,0,0.1); white-space: nowrap; display: block; }
    .fab-btn:hover { background: #f8f9fa; color: #343a40; text-decoration: none; }
    .fab-main { width: 48px; height: 48px; background: #4f8ef7; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 22px; cursor: pointer; box-shadow: 0 4px 12px rgba(79,142,247,0.4); border: none; color: white; line-height: 1; }
    .chat-divider { border: none; border-top: 1px solid #f0f0f0; margin: 1rem 0 0.5rem; }

    div[data-testid="stButton"] > button {
        background: transparent !important;
        border: none !important;
        padding: 2px 0 !important;
        text-align: left !important;
        font-size: 11px !important;
        color: #212529 !important;
        box-shadow: none !important;
        height: auto !important;
        min-height: unset !important;
        line-height: 1.3 !important;
    }
    div[data-testid="stButton"] > button:hover { background: #f8f9fa !important; color: #4f8ef7 !important; }
</style>

<button id="back-to-top" onclick="scrollToTop()">↑ Back to top</button>

<script>
// Streamlit renders inside a scroll container — target it specifically
function getScrollEl() {
    return document.querySelector('[data-testid="stAppViewContainer"]')
        || document.querySelector('.main .block-container')
        || document.documentElement
        || window;
}

function scrollToTop() {
    var el = getScrollEl();
    if (el && el.scrollTo) {
        el.scrollTo({top: 0, behavior: 'smooth'});
    } else {
        window.scrollTo({top: 0, behavior: 'smooth'});
    }
}

function checkScroll() {
    var el = getScrollEl();
    var btn = document.getElementById('back-to-top');
    if (!btn) return;
    var scrolled = el === window ? window.scrollY : el.scrollTop;
    btn.style.display = scrolled > 300 ? 'flex' : 'none';
}

// Attach to both window and the Streamlit container
window.addEventListener('scroll', checkScroll, true);
document.addEventListener('scroll', checkScroll, true);

// Also poll every second in case scroll events don't fire
setInterval(checkScroll, 1000);
</script>
""", unsafe_allow_html=True)

# ─── Secrets ──────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = st.secrets["ANTHROPIC_API_KEY"]
ADMIN_PASSWORD    = st.secrets["ADMIN_PASSWORD"]
GOOGLE_DOC_URL    = st.secrets["GOOGLE_DOC_URL"]
ADMIN_EMAIL       = st.secrets.get("ADMIN_EMAIL", "admin@flipkart.com")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

@st.cache_resource
def get_shared_store():
    return {"usage_logs": []}

shared = get_shared_store()

for k, v in {"messages": [], "is_admin": False, "show_login": False}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── Get logged-in user email from Streamlit Cloud auth ──────────────────────
# When Streamlit Cloud sharing is restricted to specific emails,
# st.experimental_user.email is automatically populated — no login prompt needed
def get_user_email():
    try:
        email = st.experimental_user.email
        if email:
            return email
    except Exception:
        pass
    # Fallback for local dev — use a placeholder
    return "user@flipkart.com"

USER_EMAIL = get_user_email()


# ═══════════════════════════════════════════════════════════════════════════════
# DATA FETCHING
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def fetch_google_doc(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.text
    except Exception as e:
        return None


@st.cache_data(ttl=300)
def extract_cards_from_doc(doc_content, api_key):
    c = anthropic.Anthropic(api_key=api_key)
    prompt = f"""Read this document and extract structured data. Return ONLY valid JSON, no explanation, no markdown fences.

Extract:
1. upcoming_launches: list of max 6 objects with "name" (max 40 chars), "date" (short e.g. "17 Apr"), "owner", "summary", "metrics_impact" (list from [Misroutes, RTO, Reachability, Drift, Text Quality, Delivery Promise Breach])
2. meeting_points: list of max 6 objects with "topic" (max 40 chars), "date", "summary", "launches_covered", "metrics_focus" (list from same)
3. accomplishments: list of max 6 objects with "title" (max 35 chars), "impact" (max 20 chars e.g. "-20bps Misroutes"), "time" (e.g. "Jan'26"), "details", "metrics_impact"

Only include what is clearly in the document. Use "" for missing strings, [] for missing lists.

Document:
---
{doc_content}
---

Return exactly:
{{"upcoming_launches":[{{"name":"","date":"","owner":"","summary":"","metrics_impact":[]}}],"meeting_points":[{{"topic":"","date":"","summary":"","launches_covered":[],"metrics_focus":[]}}],"accomplishments":[{{"title":"","impact":"","time":"","details":"","metrics_impact":[]}}]}}"""

    try:
        response = c.messages.create(
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
    c = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompts = {
        "launch":         f"Detailed leadership briefing on launch: \"{item.get('name')}\". Cover: what it is, why it matters, status, timeline, owner, risks, impact on Misroutes/RTO/Reachability/Drift/Text Quality/Delivery Promise Breach. Use numbers. Clear headers. Under 300 words.",
        "meeting":        f"Detailed briefing for meeting: \"{item.get('topic')}\". Cover: agenda, launches discussed, decisions expected, metric improvements on Misroutes/RTO/Reachability/Drift/Text Quality/Delivery Promise Breach. Use numbers. Clear headers. Under 300 words.",
        "accomplishment": f"Detailed briefing on accomplishment: \"{item.get('title')}\". Cover: what was done, when, who, problem solved, measurable impact on Misroutes/RTO/Reachability/Drift/Text Quality/Delivery Promise Breach. Use numbers. Clear headers. Under 300 words.",
    }
    try:
        response = c.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            system="Concise executive assistant. Use clear headers and bullet points. Be specific with numbers.",
            messages=[{"role": "user", "content": prompts[item_type] + f"\n\nDocument:\n---\n{doc_content}\n---"}],
        )
        return response.content[0].text
    except Exception as e:
        return f"Could not load details: {str(e)}"


def metric_pills(metrics):
    if not metrics: return ""
    colors = ["pill-green", "pill-blue"] * 6
    return "".join(f"<span class='metric-pill {colors[i]}'>{m}</span>" for i, m in enumerate(metrics))

def log_usage(email, question):
    shared["usage_logs"].append({"email": email, "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p"), "question": question})

def render_fab():
    bug_url     = f"https://mail.google.com/mail/?view=cm&to={ADMIN_EMAIL}&su=Bug+Report+%7C+Address_Chhotu&body=Hi%2C%0A%0ABug%3A%0A%0A[Describe]%0A%0AName%3A+{USER_EMAIL}"
    contact_url = f"https://mail.google.com/mail/?view=cm&to={ADMIN_EMAIL}&su=Query+%7C+Address_Chhotu&body=Hi%2C%0A%0AQuery%3A%0A%0A[Message]%0A%0AName%3A+{USER_EMAIL}"
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
        items_html = "".join([
            f"<div class='card-row'><span class='card-name'>🚀 {(l.get('name','') or '')[:40]}</span><span class='card-date'>{l.get('date','')}</span></div>"
            for l in launches
        ]) if launches else "<div style='font-size:11px;color:#adb5bd;padding:6px 0'>Nothing found yet</div>"
        st.markdown(f"<div class='section-card'><div class='section-title'>🚀 Upcoming Launches</div><div class='card-scroll'>{items_html}</div></div>", unsafe_allow_html=True)
        for i, l in enumerate(launches):
            if st.button(l.get("name",""), key=f"launch_{i}", use_container_width=True, help="Click for details"):
                launch_popup(l, doc_content)

    with col2:
        meetings = cards.get("meeting_points", [])
        items_html = "".join([
            f"<div class='card-row'><span class='card-name'>📅 {(m.get('topic','') or '')[:40]}</span></div>"
            for m in meetings
        ]) if meetings else "<div style='font-size:11px;color:#adb5bd;padding:6px 0'>Nothing found yet</div>"
        st.markdown(f"<div class='section-card'><div class='section-title'>📅 Meeting Points</div><div class='card-scroll'>{items_html}</div></div>", unsafe_allow_html=True)
        for i, m in enumerate(meetings):
            if st.button(m.get("topic",""), key=f"meeting_{i}", use_container_width=True, help="Click for details"):
                meeting_popup(m, doc_content)

    with col3:
        accomplishments = cards.get("accomplishments", [])
        items_html = ""
        for a in accomplishments:
            title  = (a.get("title","") or "")[:35]
            impact = (a.get("impact","") or "")[:20]
            impact_html = f"<span class='accomp-impact-inline'>{impact}</span>" if impact else ""
            items_html += f"<div class='accomp-row-wrap'><div class='accomp-top'><span class='accomp-name'>✅ {title}</span>{impact_html}</div></div>"
        if not items_html:
            items_html = "<div style='font-size:11px;color:#adb5bd;padding:6px 0'>Nothing found yet</div>"
        st.markdown(f"<div class='section-card'><div class='section-title'>🏆 Accomplishments</div><div class='card-scroll'>{items_html}</div></div>", unsafe_allow_html=True)
        for i, a in enumerate(accomplishments):
            if st.button(a.get("title",""), key=f"accomp_{i}", use_container_width=True, help="Click for details"):
                accomplishment_popup(a, doc_content)


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
    doc_content = fetch_google_doc(GOOGLE_DOC_URL)
    if doc_content:
        st.success(f"✅ Google Doc connected · {len(doc_content):,} characters · refreshes every 5 mins")
        with st.expander("👀 Preview Claude extraction"):
            cards = extract_cards_from_doc(doc_content, ANTHROPIC_API_KEY)
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
            st.success("Cache cleared — reloading.")
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
    # ── No email prompt — use Streamlit Cloud auth directly ───────────────────
    doc_content = fetch_google_doc(GOOGLE_DOC_URL)
    if not doc_content:
        st.error("⚠️ Could not load content. Please try again shortly.")
        st.stop()

    with st.spinner("Syncing latest updates…"):
        cards = extract_cards_from_doc(doc_content, ANTHROPIC_API_KEY)

    # ── Header ────────────────────────────────────────────────────────────────
    h1, h2 = st.columns([5, 1])
    with h1:
        st.markdown("## 🤵 Address_Chhotu")
        st.caption(f"Welcome, {USER_EMAIL} · Synced from source doc")
    with h2:
        st.markdown("<div style='padding-top:12px'>", unsafe_allow_html=True)
        if st.button("Admin", use_container_width=True):
            st.session_state.show_login = True
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("")
    render_cards(cards, doc_content)

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
                    log_usage(USER_EMAIL, s)
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
                        model="claude-sonnet-4-6",
                        max_tokens=800,
                        system=SYSTEM_PROMPT,
                        messages=cleaned,
                    )
                    reply = response.content[0].text
                except Exception as e:
                    reply = f"Error: {str(e)}"
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})

    if prompt := st.chat_input("Ask about timelines, risks, owners, launches…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        log_usage(USER_EMAIL, prompt)
        st.rerun()

    render_fab()
