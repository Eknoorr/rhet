import os
import json
import uuid
from datetime import datetime

import streamlit as st
from streamlit_local_storage import LocalStorage

from services.foundry_agent import FoundryAgentClient
from services.orchestrator import MasterOrchestrator
from models.p3_schemas import LearnerTurnInput
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
# ==========================
# ==================================

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = MasterOrchestrator()

if "next_target" not in st.session_state:
    st.session_state.next_target = ""

# ============================================================
# LOCAL STORAGE
# ============================================================

local_storage = LocalStorage()

HISTORY_KEY = "rhet_chat_history"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "history_loaded" not in st.session_state:
    saved_history = local_storage.getItem(HISTORY_KEY)

    if saved_history:
        try:
            if isinstance(saved_history, str):
                st.session_state.chat_history = json.loads(
                    saved_history
                )
            elif isinstance(saved_history, list):
                st.session_state.chat_history = saved_history
        except (json.JSONDecodeError, TypeError):
            st.session_state.chat_history = []

    st.session_state.history_loaded = True

if "foundry_agent" not in st.session_state:
    st.session_state.foundry_agent = None

def get_foundry_agent():
    if st.session_state.foundry_agent is None:
        st.session_state.foundry_agent = FoundryAgentClient()

    return st.session_state.foundry_agent

def save_history_to_local_storage():
    """
    Save the current conversation list to browser localStorage.
    """
    try:
        local_storage.setItem(
            HISTORY_KEY,
            json.dumps(
                st.session_state.chat_history,
                ensure_ascii=False
            )
        )
    except Exception as e:
        st.warning(
            f"Could not save conversation history: {e}"
        )


def get_history_title(messages):
    """
    Use the first meaningful user message as the conversation title.
    """
    for message in messages:
        if message.get("role") == "user":
            content = message.get("content", "")

            if isinstance(content, str):
                title = content.strip()

                if title:
                    return (
                        title[:42] + "..."
                        if len(title) > 42
                        else title
                    )

    return "New conversation"


def get_language_flag(language):
    """
    Convert target language into a small sidebar flag.
    """
    flags = {
        "Spanish": "🇪🇸",
        "English": "🇬🇧",
        "French": "🇫🇷",
        "German": "🇩🇪",
        "Japanese": "🇯🇵",
        "Hindi": "🇮🇳",
    }

    return flags.get(language, "🌐")


def save_current_conversation():
    """
    Save the current chat as a history entry.
    """

    messages = st.session_state.messages

    # Don't save empty conversations.
    if not messages:
        return

    conversation_id = st.session_state.get(
        "conversation_id"
    )

    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        st.session_state.conversation_id = conversation_id

    history_entry = {
        "id": conversation_id,
        "title": get_history_title(messages),
        "flag": get_language_flag(
            st.session_state.get(
                "target_language",
                "Spanish"
            )
        ),
        "created_at": datetime.now().isoformat(),
        "messages": messages,
        "native_language": st.session_state.get(
            "native_language",
            "English"
        ),
        "target_language": st.session_state.get(
            "target_language",
            "Spanish"
        ),
        "level": st.session_state.get(
            "proficiency_level",
            "A1"
        ),
    }

    history = st.session_state.chat_history

    # Replace existing version of this conversation.
    history = [
        item
        for item in history
        if item.get("id") != conversation_id
    ]

    # Put newest conversation first.
    history.insert(0, history_entry)

    # Keep localStorage small.
    history = history[:20]

    st.session_state.chat_history = history

    save_history_to_local_storage()

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
    background: rgba(15, 23, 42, 0.96) !important;
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
/* =========================================================
   HISTORY BUTTONS
   ========================================================= */

.history-button [data-testid="stButton"] > button {
    width: 100%;
    text-align: left !important;
    padding: 10px 12px !important;
    border-radius: 11px !important;
    margin-bottom: 6px !important;
    background: rgba(255, 255, 255, 0.02) !important;
    border: 1px solid rgba(255, 255, 255, 0.04) !important;
    color: #e2e8f0 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 600 !important;
}

.history-button [data-testid="stButton"] > button:hover {
    background: rgba(34, 197, 94, 0.07) !important;
    border-color: rgba(74, 222, 128, 0.25) !important;
}

/* =========================================================
   CHAT TEXT VISIBILITY FIX
   ========================================================= */

/* Main text inside every chat message */
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] div,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] span,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li {
    color: #f1f5f9 !important;
}

/* Headings */
[data-testid="stChatMessage"] h1,
[data-testid="stChatMessage"] h2,
[data-testid="stChatMessage"] h3,
[data-testid="stChatMessage"] h4,
[data-testid="stChatMessage"] h5,
[data-testid="stChatMessage"] h6 {
    color: #ffffff !important;
}

/* Strong / bold labels */
[data-testid="stChatMessage"] strong,
[data-testid="stChatMessage"] b {
    color: #ffffff !important;
}

/* User message text */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
[data-testid="stMarkdownContainer"] {
    color: #f8fafc !important;
}

/* Rhet main response */
[data-testid="stChatMessage"] .rhet-response {
    color: #f8fafc !important;
    font-size: 15px;
    line-height: 1.7;
}

/* Translation */
[data-testid="stChatMessage"] .translation-text {
    color: #cbd5e1 !important;
    line-height: 1.6;
}

/* Tutor feedback */
[data-testid="stChatMessage"] [data-testid="stAlert"] {
    background: rgba(30, 41, 59, 0.85) !important;
    border: 1px solid rgba(96, 165, 250, 0.18) !important;
}

[data-testid="stChatMessage"] [data-testid="stAlert"] p,
[data-testid="stChatMessage"] [data-testid="stAlert"] div {
    color: #dbeafe !important;
}

/* Captions such as "You said" */
[data-testid="stChatMessage"] [data-testid="stCaptionContainer"],
[data-testid="stChatMessage"] [data-testid="stCaptionContainer"] p {
    color: #94a3b8 !important;
}

/* Metrics */
[data-testid="stChatMessage"] [data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
}

[data-testid="stChatMessage"] [data-testid="stMetricValue"] {
    color: #f8fafc !important;
}

/* Inline target sentence */
[data-testid="stChatMessage"] code {
    color: #166534 !important;
    background: #f0fdf4 !important;
    border: 1px solid rgba(74, 222, 128, 0.25) !important;
    border-radius: 6px !important;
    padding: 3px 7px !important;
}

/* Audio player spacing */
[data-testid="stChatMessage"] audio {
    width: 100% !important;
}

/* =========================================================
   CHAT INPUT BUTTONS
   ========================================================= */

/* Mic + Send buttons inside the chat bar */
[data-testid="stChatInput"] button {
    background: #1f2937 !important;
    color: #4ade80 !important;
    border: 1px solid rgba(74, 222, 128, 0.18) !important;
    border-radius: 12px !important;
    width: 38px !important;
    height: 38px !important;
    transition: all 0.2s ease !important;
}

/* Hover */
[data-testid="stChatInput"] button:hover {
    background: #22c55e !important;
    color: #06120a !important;
    border-color: #4ade80 !important;
    box-shadow: 0 0 16px rgba(34, 197, 94, 0.25) !important;
    transform: translateY(-1px);
}

/* Pressed */
[data-testid="stChatInput"] button:active {
    background: #16a34a !important;
    color: #ffffff !important;
    transform: scale(0.95);
}

/* Disabled send button */
[data-testid="stChatInput"] button:disabled {
    background: rgba(31, 41, 55, 0.65) !important;
    color: #475569 !important;
    border-color: rgba(255, 255, 255, 0.05) !important;
    box-shadow: none !important;
    transform: none !important;
    opacity: 1 !important;
}

/* SVG icons */
[data-testid="stChatInput"] button svg {
    color: currentColor !important;
    stroke: currentColor !important;
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
    if st.button(
        "＋  New conversation",
        use_container_width=True
    ):

        save_current_conversation()

        st.session_state.messages = []
        st.session_state.orchestrator = MasterOrchestrator()
        st.session_state.next_target = ""
        st.session_state.conversation_id = str(uuid.uuid4())

        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">LEARNER</div>', unsafe_allow_html=True)

    native_language = st.selectbox(
        "Native language",
        ["English", "Hindi", "French", "Spanish", "German"],
        index=0,
        key="native_language"
    )

    target_language = st.selectbox(
        "Learning",
        ["Spanish", "English", "French", "German", "Japanese", "Hindi"],
        index=0,
        key="target_language"
    )

    proficiency_level = st.selectbox(
        "Level",
        ["A1", "A2", "B1", "B2", "C1", "C2"],
        index=0,
        key="proficiency_level"
    )

    # ============================================================
    # RECENT CONVERSATIONS
    # ============================================================

    st.markdown(
        '<div class="section-title">RECENT CONVERSATIONS</div>',
        unsafe_allow_html=True
    )

    if not st.session_state.chat_history:

        st.markdown(
            """
            <div class="recent-card">
                <div class="recent-details">
                    <div class="recent-title">
                        No conversations yet
                    </div>
                    <div class="recent-meta">
                        Start chatting to build your history
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        for item in st.session_state.chat_history[:8]:

            conversation_id = item.get(
                "id",
                str(uuid.uuid4())
            )

            title = item.get(
                "title",
                "Conversation"
            )

            flag = item.get(
                "flag",
                "🌐"
            )

            # ONE button per history item.
            clicked = st.button(
                f"{flag}  {title}",
                key=f"history_{conversation_id}",
                use_container_width=True
            )

            if clicked:

                # Restore saved messages.
                st.session_state.messages = item.get(
                    "messages",
                    []
                )

                # Restore learner settings.
                st.session_state.native_language = item.get(
                    "native_language",
                    "English"
                )

                st.session_state.target_language = item.get(
                    "target_language",
                    "Spanish"
                )

                st.session_state.proficiency_level = item.get(
                    "level",
                    "A1"
                )

                # Reset the next pronunciation target.
                st.session_state.next_target = ""

                # Give this loaded conversation its own UI ID.
                st.session_state.conversation_id = conversation_id

                # Start a fresh backend conversation for now.
                st.session_state.orchestrator = MasterOrchestrator()

                st.rerun()

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

        if message["role"] == "user":
            st.write(message["content"])
            continue

        result = message["content"]

        reply = result.get(
            "conversational_reply",
            ""
        )

        if reply:
            st.markdown(
                f'<div class="rhet-response"><strong>🦜 Rhet</strong><br>{reply}</div>',
                unsafe_allow_html=True
            )

        transcript = result.get(
            "transcript",
            ""
        )

        if transcript:
            st.caption(
                f"🎙️ You said: {transcript}"
            )

        scores = result.get(
            "pronunciation_scores"
        )

        if scores:
            st.markdown(
                "**🗣️ Pronunciation**"
            )

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Pronunciation",
                    f"{scores.get('pronunciation_score', 0):.1f}/100"
                )

            with col2:
                st.metric(
                    "Accuracy",
                    f"{scores.get('accuracy_score', 0):.1f}/100"
                )

            st.caption(
                f"Fluency: "
                f"{scores.get('fluency_score', 0):.1f} • "
                f"Completeness: "
                f"{scores.get('completeness_score', 0):.1f}"
            )

        # Pronunciation guide
        pronunciation = result.get(
            "pronunciation",
            ""
        )

        if pronunciation:
            st.markdown(
                f"**🔊 Pronunciation**\n\n{pronunciation}"
            )

        # Native-language translation
        translation = result.get(
            "translation",
            ""
        )

        if translation:
            st.markdown(
                f"**🌐 Translation**\n\n{translation}"
            )

        feedback = result.get(
            "pedagogical_feedback",
            ""
        )

        if feedback:
            st.info(
                f"💡 {feedback}"
            )

        next_target = result.get(
            "suggested_next_target",
            ""
        )

        if next_target:
            st.markdown(
                f"**🎯 Try saying:** `{next_target}`"
            )

        audio_path = result.get(
            "tutor_audio_path"
        )

        if (
            audio_path
            and os.path.exists(audio_path)
        ):
            st.audio(
                audio_path,
                format="audio/wav"
            )

# ============================================================
# CENTERED MINIMALISTIC CHAT INPUT
# ============================================================

submission = st.chat_input(
    "Speak or message in any language...",
    key="chat_input",
    accept_audio=True,
    audio_sample_rate=16000,
)

# ============================================================
# HANDLE TEXT + VOICE SUBMISSION
# ============================================================

if submission is not None:

    # --------------------------------------------------------
    # GET TEXT + AUDIO FROM THE SAME CHAT INPUT
    # --------------------------------------------------------

    text_input = (
        submission.text.strip()
        if submission.text
        else ""
    )

    audio_input = submission.audio

    # --------------------------------------------------------
    # DO NOT ACCEPT TEXT + AUDIO IN THE SAME TURN
    # --------------------------------------------------------

    if text_input and audio_input is not None:

        st.warning(
            "Please use either text or voice for one turn."
        )
        st.stop()

    # ========================================================
    # TEXT MODE
    # ========================================================

    elif text_input:

        # Store learner message
        st.session_state.messages.append({
            "role": "user",
            "content": text_input
        })

        try:
            agent = get_foundry_agent()

            learner_signal = {
                "transcript": text_input,
                "detected_language": native_language,
                "target_language": target_language,
                "native_language": native_language,
                "proficiency_level": proficiency_level,
                "pronunciation_scores": None,
                "language_analysis": {},
            }

            # Send text to Rhet
            result = agent.generate_tutor_turn(
                learner_signal
            )

            # Save Rhet's suggested sentence
            # for the NEXT pronunciation turn.
            st.session_state.next_target = (
                result.get(
                    "suggested_next_target",
                    ""
                ) or ""
            )

            save_current_conversation()

        except Exception as e:

            result = {
                "conversational_reply":
                    "Sorry, I couldn't process that message.",
                "translation": "",
                "pedagogical_feedback": "",
                "explanation": "",
                "suggested_next_target": "",
                "error": str(e),
            }

        # Store structured Rhet response
        st.session_state.messages.append({
            "role": "assistant",
            "content": result
        })

    # ========================================================
    # VOICE MODE
    # ========================================================

    elif audio_input is not None:

        import tempfile

        temp_fd, temp_path = tempfile.mkstemp(
            suffix=".wav"
        )
        os.close(temp_fd)

        try:

            # ------------------------------------------------
            # SAVE THE BROWSER RECORDING
            # ------------------------------------------------

            with open(temp_path, "wb") as f:
                f.write(audio_input.getvalue())

            # ------------------------------------------------
            # UI LANGUAGE → AZURE SPEECH LOCALE
            # ------------------------------------------------

            speech_language_codes = {
                "Spanish": "es-ES",
                "English": "en-US",
                "French": "fr-FR",
                "German": "de-DE",
                "Japanese": "ja-JP",
                "Hindi": "hi-IN",
            }

            speech_language = (
                speech_language_codes.get(
                    target_language,
                    "en-US"
                )
            )

            # ------------------------------------------------
            # PREVIOUS RHET SUGGESTION = REFERENCE SENTENCE
            # ------------------------------------------------

            reference_text = (
                st.session_state.next_target.strip()
                if st.session_state.next_target
                else None
            )

            # ------------------------------------------------
            # BUILD THE EXISTING BACKEND INPUT
            # ------------------------------------------------

            turn_input = LearnerTurnInput(
                user_id="user_123",
                target_language=speech_language,
                target_sentence=reference_text,
                audio_path=temp_path,
                target_gloss_language="en",
            )

            # ------------------------------------------------
            # SEND THE SAME WAV TO YOUR EXISTING PIPELINE
            # ------------------------------------------------

            with st.spinner("Listening to you..."):

                response = (
                    st.session_state
                    .orchestrator
                    .process_turn(turn_input)
                )

            # ------------------------------------------------
            # READ BACKEND RESPONSE
            # ------------------------------------------------

            transcript = getattr(
                response,
                "transcript",
                ""
            )

            pronunciation_scores = getattr(
                response,
                "pronunciation_scores",
                None
            )

            feedback = getattr(
                response,
                "feedback",
                ""
            )

            native_gloss = getattr(
                response,
                "native_gloss",
                ""
            )

            next_prompt = getattr(
                response,
                "next_prompt",
                ""
            )

            tutor_audio_path = getattr(
                response,
                "tutor_audio_path",
                None
            )

            # ------------------------------------------------
            # STORE LEARNER'S SPOKEN MESSAGE
            # ------------------------------------------------

            if transcript:

                st.session_state.messages.append({
                    "role": "user",
                    "content": f"🎙️ {transcript}"
                })

            # ------------------------------------------------
            # STORE STRUCTURED RHET RESPONSE
            # ------------------------------------------------

            assistant_result = {
                "transcript": transcript,

                "pronunciation_scores":
                    pronunciation_scores,

                "pedagogical_feedback":
                    feedback,

                "translation":
                    native_gloss,

                "conversational_reply":
                    next_prompt,

                "suggested_next_target":
                    next_prompt,

                "tutor_audio_path":
                    tutor_audio_path,
            }

            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_result
            })

            # ------------------------------------------------
            # NEW TARGET FOR NEXT VOICE TURN
            # ------------------------------------------------

            st.session_state.next_target = (
                next_prompt or ""
            )

            save_current_conversation()

        except Exception as e:

            st.error(
                f"Voice processing failed: {e}"
            )

        finally:

            if os.path.exists(temp_path):
                os.remove(temp_path)

    # --------------------------------------------------------
    # RE-RENDER CHAT ONCE
    # --------------------------------------------------------

    st.rerun()
