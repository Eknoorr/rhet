import streamlit as st

# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="parrhet.ai",
    page_icon="🦜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "recent_lessons" not in st.session_state:
    st.session_state.recent_lessons = [
        {"flag": "🇪🇸", "title": "Spanish — Daily Conversation", "time": "Today"},
        {"flag": "🇫🇷", "title": "French — Ordering at a Bistro", "time": "Yesterday"},
        {"flag": "🇯🇵", "title": "Japanese — Travel Essentials", "time": "2d ago"},
        {"flag": "🇩🇪", "title": "German — Workplace Greetings", "time": "4d ago"},
        {"flag": "🇮🇹", "title": "Italian — Food & Dining", "time": "1w ago"},
        {"flag": "🇬🇧", "title": "English — Pronunciation Practice", "time": "1w ago"},
        {"flag": "🇧🇷", "title": "Portuguese — Rio Travel Basics", "time": "2w ago"},
    ]

# ============================================================
# FONTS & STYLESHEET (MINIMALISTIC, REFINED, CLEAN)
# ============================================================

st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* =========================================================
   GLOBAL RESET & DARK OBSIDIAN CANVAS
   ========================================================= */

html, body, [data-testid="stAppViewContainer"] {
    background-color: #080b11;
    background-image: 
        radial-gradient(at 0% 0%, rgba(34, 197, 94, 0.05) 0px, transparent 45%),
        radial-gradient(at 100% 100%, rgba(56, 189, 248, 0.04) 0px, transparent 45%);
    color: #f1f5f9;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

[data-testid="stHeader"] {
    background: transparent;
}

#MainMenu, footer {
    visibility: hidden;
}

.block-container {
    padding-top: 0rem;
    padding-bottom: 7rem;
    max-width: 100%;
}

/* =========================================================
   SIDEBAR (REFINED GLASS WITH RICH RECENTS)
   ========================================================= */

[data-testid="stSidebar"] {
    background-color: #0b0f17 !important;
    border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
}

[data-testid="stSidebar"] > div:first-child {
    padding: 28px 18px;
}

/* SIDEBAR LOGO */

.sidebar-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 24px;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 22px;
    letter-spacing: -0.5px;
}

.sidebar-logo .mint {
    color: #4ade80;
}

/* NEW CONVERSATION BUTTON */

div.new-conv-btn [data-testid="stButton"] > button {
    background: linear-gradient(135deg, #22c55e 0%, #10b981 100%) !important;
    color: #04070a !important;
    border: none !important;
    border-radius: 12px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 14.5px !important;
    font-weight: 700 !important;
    min-height: 44px !important;
    box-shadow: 0 4px 18px rgba(34, 197, 94, 0.3) !important;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

div.new-conv-btn [data-testid="stButton"] > button:hover {
    background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 24px rgba(74, 222, 128, 0.45) !important;
}

/* SECTION TITLES */

.section-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.5px;
    color: #64748b;
    margin-top: 26px;
    margin-bottom: 12px;
    text-transform: uppercase;
}

/* RICH RECENTS LIST */

.recent-card {
    display: flex;
    align-items: center;
    gap: 11px;
    padding: 10px 12px;
    border-radius: 11px;
    margin-bottom: 6px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.04);
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    cursor: pointer;
}

.recent-card:hover {
    background: rgba(34, 197, 94, 0.07);
    border-color: rgba(74, 222, 128, 0.25);
    transform: translateX(3px);
}

.recent-flag {
    font-size: 18px;
    flex-shrink: 0;
}

.recent-details {
    overflow: hidden;
}

.recent-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 13px;
    font-weight: 600;
    color: #e2e8f0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.25;
}

.recent-meta {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 11px;
    font-weight: 500;
    color: #64748b;
    margin-top: 2px;
}

/* ACCOUNT BUTTONS */

.account-section {
    margin-top: 26px;
}

[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    border-radius: 11px;
    border: 1px solid rgba(255, 255, 255, 0.06);
    background: rgba(255, 255, 255, 0.02);
    color: #cbd5e1;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 13.5px;
    font-weight: 600;
    min-height: 40px;
    transition: all 0.2s ease;
}

[data-testid="stSidebar"] .stButton > button:hover {
    border-color: rgba(74, 222, 128, 0.3);
    background: rgba(34, 197, 94, 0.08);
    color: #ffffff;
}

/* =========================================================
   MAIN HEADER (TOP STATUS BAR)
   ========================================================= */

.main-header {
    height: 72px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 44px;
    background: rgba(8, 11, 17, 0.75);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
}

.main-header-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 21px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.3px;
}

.main-header-subtitle {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 13px;
    font-weight: 400;
    color: #94a3b8;
}

.header-status-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 50px;
    padding: 6px 16px;
    font-size: 12.5px;
    font-weight: 600;
    color: #cbd5e1;
}

.pulse-dot {
    width: 7px;
    height: 7px;
    background-color: #22c55e;
    border-radius: 50%;
    box-shadow: 0 0 8px #22c55e;
}

/* =========================================================
   CHAT CONTAINER
   ========================================================= */

.chat-container {
    max-width: 820px;
    margin: 0 auto;
    padding: 35px 20px 140px 20px;
}

/* EMPTY STATE */

.empty-chat {
    text-align: center;
    padding-top: 75px;
    padding-bottom: 40px;
}

.empty-chat-avatar {
    width: 74px;
    height: 74px;
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(56, 189, 248, 0.1));
    border: 1px solid rgba(74, 222, 128, 0.35);
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 38px;
    margin-bottom: 18px;
}

.empty-chat-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 32px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.5px;
}

.empty-chat-text {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 15px;
    font-weight: 400;
    color: #94a3b8;
    margin-top: 8px;
    max-width: 500px;
    margin-left: auto;
    margin-right: auto;
    line-height: 1.6;
}

.empty-chat-chips {
    display: flex;
    gap: 10px;
    justify-content: center;
    flex-wrap: wrap;
    margin-top: 26px;
}

.empty-chip {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 30px;
    padding: 7px 18px;
    font-size: 12.5px;
    font-weight: 600;
    color: #cbd5e1;
    transition: all 0.2s ease;
}

.empty-chip:hover {
    border-color: rgba(74, 222, 128, 0.35);
    background: rgba(34, 197, 94, 0.06);
    color: #ffffff;
}

/* =========================================================
   STREAMLIT CHAT MESSAGES (CLEAN & SUBTLE)
   ========================================================= */

[data-testid="stChatMessage"] {
    max-width: 820px;
    margin-left: auto;
    margin-right: auto;
    font-family: 'Plus Jakarta Sans', sans-serif;
    background: rgba(13, 17, 26, 0.65) !important;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.06) !important;
    border-radius: 18px !important;
    padding: 16px 22px !important;
    margin-bottom: 14px !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4) !important;
    color: #f1f5f9 !important;
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: rgba(18, 28, 22, 0.7) !important;
    border: 1px solid rgba(74, 222, 128, 0.25) !important;
}

/* =========================================================
   MINIMALISTIC CENTERED CHAT INPUT & MICROPHONE DOCK
   ========================================================= */

/* Float microphone pill directly above centered chat input */
.voice-dock-wrap {
    display: flex;
    justify-content: center;
    margin-top: 20px;
    margin-bottom: 12px;
}

.minimal-mic-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(15, 20, 30, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(12px);
    border-radius: 30px;
    padding: 7px 18px;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 12.5px;
    font-weight: 600;
    color: #cbd5e1;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.35);
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.minimal-mic-pill:hover {
    border-color: rgba(74, 222, 128, 0.4);
    background: rgba(34, 197, 94, 0.08);
    color: #ffffff;
}

.mic-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: #22c55e;
}

/* CENTERED MINIMALISTIC CHAT INPUT */

[data-testid="stChatInput"] {
    width: 100% !important;
    max-width: 680px !important;
    margin: 0 auto !important;
    bottom: 24px !important;
    padding: 0 !important;
}

[data-testid="stChatInput"] > div {
    border-radius: 30px !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    background: rgba(13, 17, 26, 0.94) !important;
    backdrop-filter: blur(24px) !important;
    -webkit-backdrop-filter: blur(24px) !important;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.7), 0 0 20px rgba(34, 197, 94, 0.08) !important;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    padding: 4px 8px !important;
}

[data-testid="stChatInput"] > div:focus-within {
    border-color: rgba(74, 222, 128, 0.6) !important;
    box-shadow: 0 20px 48px rgba(0, 0, 0, 0.8), 0 0 30px rgba(74, 222, 128, 0.2) !important;
    transform: translateY(-2px);
}

[data-testid="stChatInput"] textarea {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 14.5px !important;
    font-weight: 500 !important;
    color: #f8fafc !important;
    padding-left: 12px !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: #64748b !important;
}

/* =========================================================
   MOBILE RESPONSIVENESS
   ========================================================= */

@media (max-width: 700px) {
    .main-header {
        padding: 0 20px;
    }

    .chat-container {
        padding-left: 16px;
        padding-right: 16px;
    }

    .empty-chat-title {
        font-size: 26px;
    }

    [data-testid="stChatInput"] {
        max-width: 92% !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR (NO HOME BUTTON, FILLED WITH RECENTS)
# ============================================================

with st.sidebar:
    # LOGO
    st.markdown("""<div class="sidebar-logo"><span>🦜</span> parrhet<span class="mint">.ai</span></div>""", unsafe_allow_html=True)

    # NEW CONVERSATION BUTTON
    st.markdown('<div class="new-conv-btn">', unsafe_allow_html=True)
    if st.button("＋  New conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # RECENTS SECTION (EXPANDED TO FILL SPACE)
    st.markdown('<div class="section-title">RECENT LESSONS</div>', unsafe_allow_html=True)

    for lesson in st.session_state.recent_lessons:
        st.markdown(f"""<div class="recent-card">
<span class="recent-flag">{lesson['flag']}</span>
<div class="recent-details">
<div class="recent-title">{lesson['title']}</div>
<div class="recent-meta">{lesson['time']}</div>
</div>
</div>""", unsafe_allow_html=True)

    # ACCOUNT SECTION
    st.markdown('<div class="account-section"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">ACCOUNT</div>', unsafe_allow_html=True)

    st.button("⚙  Settings", use_container_width=True)
    st.button("👤  Profile", use_container_width=True)

# ============================================================
# MAIN HEADER
# ============================================================

st.markdown("""<div class="main-header">
<div>
<div class="main-header-title">parrhet.ai Studio</div>
<div class="main-header-subtitle">Interactive Conversational Practice</div>
</div>
<div class="header-status-badge"><span class="pulse-dot"></span> Ready to Speak</div>
</div>""", unsafe_allow_html=True)

# ============================================================
# CHAT CONTAINER
# ============================================================

st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# ============================================================
# EMPTY CHAT STATE
# ============================================================

if len(st.session_state.messages) == 0:
    st.markdown("""<div class="empty-chat">
<div class="empty-chat-avatar">🦜</div>
<div class="empty-chat-title">Start a Conversation</div>
<div class="empty-chat-text">Practice real-time speaking, learn conversational vocabulary, polish your accent, or ask Parrhet anything in 50+ languages.</div>
<div class="empty-chat-chips">
<span class="empty-chip">🇪🇸 Practice Spanish conversational basics</span>
<span class="empty-chip">🇫🇷 Help me order food in Paris</span>
<span class="empty-chip">🇯🇵 Practice Hiragana & Katakana</span>
<span class="empty-chip">💡 Explain past tense grammar</span>
</div>
</div>""", unsafe_allow_html=True)

# ============================================================
# DISPLAY MESSAGES
# ============================================================

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# MINIMALISTIC MICROPHONE DOCK (Voice Practice Trigger)
st.markdown("""<div class="voice-dock-wrap">
<div class="minimal-mic-pill">
<span>🎙️</span>
<span>Voice Practice Ready</span>
<span class="mic-dot"></span>
</div>
</div>""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# CENTERED MINIMALISTIC CHAT INPUT
# ============================================================

prompt = st.chat_input("Speak or message in any language... 🎙️")

# ============================================================
# HANDLE MESSAGE
# ============================================================

if prompt:
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.write(prompt)

    # BACKEND RESPONSE HOOK
    # Azure AI will be connected here later.
    response = (
        "I'm ready to help! 🦜\n\n"
        "Your Azure AI response will be connected here."
    )

    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })

    with st.chat_message("assistant"):
        st.write(response)