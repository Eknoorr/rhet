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
        "Spanish — Greetings & Introductions",
        "French — Basic Phrases",
        "English — Grammar Practice",
        "Japanese — Hiragana Basics"
    ]


# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@400;500;600;700&family=Nunito:wght@400;500;600;700&display=swap');


/* =========================================================
   GENERAL
   ========================================================= */

html, body,
[data-testid="stAppViewContainer"] {
    background-color: #faf9f3;
}

[data-testid="stHeader"] {
    background: transparent;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

.block-container {
    padding-top: 0rem;
    padding-bottom: 7rem;
    max-width: 100%;
}


/* =========================================================
   SIDEBAR
   ========================================================= */

[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e8e8e3;
}

[data-testid="stSidebar"] > div:first-child {
    padding: 28px 20px;
}


/* LOGO */

.sidebar-logo {
    font-family: 'Fredoka', sans-serif;
    font-size: 27px;
    font-weight: 700;
    color: #111111;
    margin-bottom: 28px;
}

.sidebar-logo .green {
    color: #6a994e;
}


/* HOME BUTTON */

.home-label {
    font-family: 'Nunito', sans-serif;
    font-size: 14px;
    font-weight: 600;
    color: #555555;
    margin-bottom: 8px;
}


/* BUTTONS */

[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    border-radius: 10px;
    border: 1px solid #ddddda;
    background: #ffffff;
    color: #222222;
    font-family: 'Nunito', sans-serif;
    font-size: 14px;
    font-weight: 600;
    min-height: 42px;
}

[data-testid="stSidebar"] .stButton > button:hover {
    border-color: #6a994e;
    color: #4a7c32;
}


/* NEW CHAT */

.new-chat button {
    background: #20211f !important;
    color: white !important;
    border: 1px solid #20211f !important;
}


/* RECENTS TITLE */

.section-title {
    font-family: 'Nunito', sans-serif;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1.3px;
    color: #8a8a83;
    margin-top: 34px;
    margin-bottom: 12px;
}


/* RECENT ITEMS */

.recent-item {
    font-family: 'Nunito', sans-serif;
    font-size: 14px;
    color: #444444;
    padding: 11px 10px;
    border-radius: 8px;
    margin-bottom: 4px;
}

.recent-item:hover {
    background: #f4f5ef;
}


/* ACCOUNT */

.account-section {
    margin-top: 45px;
}


/* =========================================================
   MAIN HEADER
   ========================================================= */

.main-header {
    height: 72px;
    border-bottom: 1px solid #e7e7e1;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 42px;
    background: rgba(250, 249, 243, 0.92);
}

.main-header-title {
    font-family: 'Fredoka', sans-serif;
    font-size: 21px;
    font-weight: 600;
    color: #151515;
}

.main-header-subtitle {
    font-family: 'Nunito', sans-serif;
    font-size: 13px;
    color: #888888;
}


/* =========================================================
   CHAT AREA
   ========================================================= */

.chat-container {
    max-width: 820px;
    margin: 0 auto;
    padding: 45px 25px 120px 25px;
}


/* EMPTY CHAT */

.empty-chat {
    text-align: center;
    padding-top: 170px;
}

.empty-chat-title {
    font-family: 'Fredoka', sans-serif;
    font-size: 32px;
    font-weight: 600;
    color: #171717;
}

.empty-chat-text {
    font-family: 'Nunito', sans-serif;
    font-size: 16px;
    color: #858585;
    margin-top: 8px;
}


/* CHAT MESSAGES */

[data-testid="stChatMessage"] {
    font-family: 'Nunito', sans-serif;
}


/* =========================================================
   MAIN CHAT INPUT
   ========================================================= */

/* This controls the ACTUAL conversation bar */

[data-testid="stChatInput"] {
    width: 100%;
    max-width: 720px;
    margin-left: auto;
    margin-right: auto;
}

[data-testid="stChatInput"] > div {
    border-radius: 18px !important;
    border: 1.5px solid #bdbdb6 !important;
    background: #ffffff !important;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.06);
}

[data-testid="stChatInput"] textarea {
    font-family: 'Nunito', sans-serif !important;
    font-size: 15px !important;
}


/* =========================================================
   MOBILE
   ========================================================= */

@media (max-width: 700px) {

    .main-header {
        padding: 0 18px;
    }

    .chat-container {
        padding-left: 15px;
        padding-right: 15px;
    }

    [data-testid="stChatInput"] {
        max-width: 95%;
    }

}

</style>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    # LOGO
    st.markdown(
        """
        <div class="sidebar-logo">
            🦜 parrhet<span class="green">.ai</span>
        </div>
        """,
        unsafe_allow_html=True
    )


    # HOME
    if st.button("←  Home", use_container_width=True):
        st.switch_page("app.py")


    st.write("")


    # NEW CONVERSATION
    if st.button("＋  New conversation", use_container_width=True):

        st.session_state.messages = []

        st.rerun()


    # ========================================================
    # RECENTS
    # ========================================================

    st.markdown(
        '<div class="section-title">RECENTS</div>',
        unsafe_allow_html=True
    )

    for lesson in st.session_state.recent_lessons:

        st.markdown(
            f"""
            <div class="recent-item">
                {lesson}
            </div>
            """,
            unsafe_allow_html=True
        )


    # ========================================================
    # ACCOUNT
    # ========================================================

    st.markdown(
        '<div class="account-section"></div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-title">ACCOUNT</div>',
        unsafe_allow_html=True
    )

    st.button("⚙  Settings", use_container_width=True)
    st.button("👤  Profile", use_container_width=True)


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown(
    """
    <div class="main-header">

        <div>
            <div class="main-header-title">
                parrhet.ai
            </div>

            <div class="main-header-subtitle">
                Language learning assistant
            </div>
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# CHAT AREA
# ============================================================

st.markdown('<div class="chat-container">', unsafe_allow_html=True)


# ============================================================
# EMPTY CHAT
# ============================================================

if len(st.session_state.messages) == 0:

    st.markdown(
        """
        <div class="empty-chat">

            <div class="empty-chat-title">
                Start a conversation
            </div>

            <div class="empty-chat-text">
                Practice speaking, learn vocabulary, translate,
                or ask Parrhet anything.
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# DISPLAY MESSAGES
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.write(message["content"])


st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# CHAT INPUT
# ============================================================

prompt = st.chat_input(
    "Message parrhet.ai  🎙"
)


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


    # TEMPORARY RESPONSE
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