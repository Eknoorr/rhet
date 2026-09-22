import streamlit as st

# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="parrhet.ai",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# CSS / DESIGN
# ============================================================

st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600;700&family=Nunito:ital,wght@0,400;0,700;1,400;1,700&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background-color: #faf9f3;
}

[data-testid="stHeader"] {
    background-color: transparent;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

.block-container {
    padding-top: 0rem;
    padding-left: 0rem;
    padding-right: 0rem;
    max-width: 100%;
}

/* ANIMATED GREEN SWIRLS */

.swirl {
    position: fixed;
    border: 22px solid #839065;
    border-radius: 50%;
    opacity: 0.65;
    pointer-events: none;
    z-index: 0;
}

.swirl-one {
    width: 430px;
    height: 190px;
    top: -120px;
    left: -120px;
    transform: rotate(-20deg);
    animation: moveOne 8s ease-in-out infinite alternate;
}

.swirl-two {
    width: 380px;
    height: 190px;
    bottom: -100px;
    right: -100px;
    transform: rotate(25deg);
    animation: moveTwo 10s ease-in-out infinite alternate;
}

.swirl-three {
    width: 180px;
    height: 350px;
    top: 100px;
    right: -110px;
    transform: rotate(-30deg);
    animation: moveThree 7s ease-in-out infinite alternate;
}

.swirl-four {
    width: 330px;
    height: 220px;
    top: -90px;
    right: -90px;
    transform: rotate(18deg);
    animation: moveFour 9s ease-in-out infinite alternate;
}

.swirl-five {
    width: 200px;
    height: 400px;
    top: 120px;
    left: -120px;
    transform: rotate(15deg);
    animation: moveFive 11s ease-in-out infinite alternate;
}

.swirl-six {
    width: 260px;
    height: 160px;
    bottom: 130px;
    left: -80px;
    transform: rotate(-25deg);
    animation: moveSix 8.5s ease-in-out infinite alternate;
}

.swirl-seven {
    width: 300px;
    height: 130px;
    bottom: -60px;
    left: 50%;
    margin-left: -150px;
    transform: rotate(5deg);
    animation: moveSeven 9.5s ease-in-out infinite alternate;
}

@keyframes moveOne {
    from {
        transform: translate(0px, 0px) rotate(-20deg);
    }
    to {
        transform: translate(35px, 20px) rotate(-10deg);
    }
}

@keyframes moveTwo {
    from {
        transform: translate(0px, 0px) rotate(25deg);
    }
    to {
        transform: translate(-30px, -25px) rotate(35deg);
    }
}

@keyframes moveThree {
    from {
        transform: translate(0px, 0px) rotate(-30deg);
    }
    to {
        transform: translate(-20px, 30px) rotate(-20deg);
    }
}

@keyframes moveFour {
    from {
        transform: translate(0px, 0px) rotate(18deg);
    }
    to {
        transform: translate(-25px, 15px) rotate(28deg);
    }
}

@keyframes moveFive {
    from {
        transform: translate(0px, 0px) rotate(15deg);
    }
    to {
        transform: translate(20px, -25px) rotate(5deg);
    }
}

@keyframes moveSix {
    from {
        transform: translate(0px, 0px) rotate(-25deg);
    }
    to {
        transform: translate(15px, 20px) rotate(-15deg);
    }
}

@keyframes moveSeven {
    from {
        transform: translate(0px, 0px) rotate(5deg);
    }
    to {
        transform: translate(0px, -18px) rotate(12deg);
    }
}

/* HERO */

.hero {
    position: relative;
    min-height: 650px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    z-index: 1;
    overflow: hidden;
}

/* LOGO */

.logo {
    font-family: 'Fredoka', 'Baloo 2', sans-serif;
    font-size: 110px;
    font-weight: 700;
    letter-spacing: 5px;
    color: #050505;
    text-shadow: 0px 4px 0px #e2fab8;
}

/* TAGLINE */

.tagline {
    font-family: 'Nunito', sans-serif;
    font-size: 27px;
    font-style: italic;
    color: #111;
    margin-top: -10px;
}

/* LOGO WRAP */

.logo-wrap {
    position: relative;
    display: inline-block;
}

/* START BUTTON */

.start-button {
    margin-top: 20px;
    background: #e2fab8;
    color: #111;
    border: 4px solid #111;
    border-radius: 50px;
    padding: 14px 35px;
    font-family: 'Fredoka', sans-serif;
    font-size: 20px;
    font-weight: 700;
}

/* FLYING PARROT */

.parrot {
    position: absolute;
    right: 52px;
    top: -42px;
    z-index: 6;
}

.svg-parrot {
    display: block;
    width: 150px;
    height: auto;
    animation: hover 2.6s ease-in-out infinite;
}

@keyframes hover {
    0%, 100% {
        transform: translateY(0px);
    }
    50% {
        transform: translateY(-12px);
    }
}

.parrot .wing-top,
.parrot .wing-bottom {
    transform-box: view-box;
    animation: flap 0.45s ease-in-out infinite alternate;
}

.parrot .wing-top {
    transform-origin: 60px 40px;
}

.parrot .wing-bottom {
    transform-origin: 60px 70px;
    animation-delay: 0.22s;
}

@keyframes flap {
    from {
        transform: rotate(-28deg);
    }
    to {
        transform: rotate(28deg);
    }
}

/* CHAT SECTION */

.chat-section {
    position: relative;
    z-index: 2;
    background: rgba(255, 255, 255, 0.92);
    border-top: 3px solid #111;
    padding: 45px 10% 80px 10%;
    min-height: 350px;
}

.chat-title {
    font-family: 'Fredoka', sans-serif;
    font-size: 32px;
    font-weight: bold;
    text-align: center;
    margin-bottom: 20px;
}

/* MOBILE */

@media (max-width: 700px) {
    .logo {
        font-size: 65px;
    }

    .tagline {
        font-size: 18px;
    }

    .hero {
        min-height: 550px;
    }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# ANIMATED BACKGROUND
# ============================================================

st.markdown("""
<div class="swirl swirl-one"></div>
<div class="swirl swirl-two"></div>
<div class="swirl swirl-three"></div>
<div class="swirl swirl-four"></div>
<div class="swirl swirl-five"></div>
<div class="swirl swirl-six"></div>
<div class="swirl swirl-seven"></div>
""", unsafe_allow_html=True)

# ============================================================
# HERO SECTION
# ============================================================

st.markdown("""<div class="hero">
    <div class="logo-wrap">
        <div class="logo">
parrhet.ai
        </div>
        <div class="parrot">
            <svg class="svg-parrot" viewBox="0 0 130 110" xmlns="http://www.w3.org/2000/svg">
                <path d="M44 68 L6 26 L18 20 L48 58 Z" fill="#4a7c32" stroke="#111" stroke-width="4" stroke-linejoin="round"/>
                <path d="M46 74 L16 42 L26 38 L50 68 Z" fill="#6a994e" stroke="#111" stroke-width="4" stroke-linejoin="round"/>
                <g class="wing-bottom">
                    <path d="M62 66 Q50 96 84 92 Q80 76 70 66 Z" fill="#35593b" stroke="#111" stroke-width="4" stroke-linejoin="round"/>
                </g>
                <ellipse cx="72" cy="62" rx="30" ry="24" fill="#6a994e" stroke="#111" stroke-width="5"/>
                <ellipse cx="78" cy="68" rx="18" ry="14" fill="#a7c957" stroke="#111" stroke-width="4"/>
                <g class="wing-top">
                    <path d="M64 50 Q54 12 84 10 Q80 34 70 52 Z" fill="#4a7c32" stroke="#111" stroke-width="4" stroke-linejoin="round"/>
                </g>
                <circle cx="96" cy="40" r="18" fill="#6a994e" stroke="#111" stroke-width="5"/>
                <path d="M110 32 L128 41 L110 48 Z" fill="#f4a261" stroke="#111" stroke-width="4" stroke-linejoin="round"/>
                <circle cx="93" cy="37" r="3.5" fill="#111"/>
                <circle cx="94" cy="36" r="1.2" fill="#fff"/>
                <circle cx="38" cy="58" r="6" fill="#111"/>
                <circle cx="72" cy="88" r="5" fill="#111"/>
            </svg>
        </div>
    </div>
    <div class="tagline">
        Learn anytime, speak anywhere.
    </div>
    <div class="start-button-placeholder"></div>
</div>""", unsafe_allow_html=True)

# ============================================================
# START LEARNING BUTTON / NAVIGATION
# ============================================================

# This real Streamlit button sits over the styled placeholder in the hero.
# Clicking it opens the learning/chat page in pages/learn.py.
if st.button("✨ Start Learning", key="start_learning", use_container_width=False):
    st.switch_page("pages/learn.py")

st.markdown("""
<style>
/* Position the real Streamlit button where the old visual button was */
div[data-testid="stButton"] {
    display: flex;
    justify-content: center;
    position: relative;
    z-index: 10;
    margin-top: -105px;
    margin-bottom: 70px;
}

div[data-testid="stButton"] > button {
    background: #e2fab8;
    color: #111;
    border: 4px solid #111;
    border-radius: 50px;
    padding: 14px 35px;
    font-family: 'Fredoka', sans-serif;
    font-size: 20px;
    font-weight: 700;
    min-height: 58px;
    box-shadow: none;
    transition: transform 0.15s ease, background 0.15s ease;
}

div[data-testid="stButton"] > button:hover {
    background: #cdef91;
    color: #111;
    border-color: #111;
    transform: translateY(-2px);
}

div[data-testid="stButton"] > button:active {
    transform: translateY(1px);
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# CHAT SECTION
# ============================================================

st.markdown("""
<div class="chat-section">
    <div class="chat-title">
        💬 Talk to parrhet.ai
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# CHAT INPUT
# ============================================================

prompt = st.chat_input("Ask me something...")

if prompt:
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        st.write("I'm thinking... 🤔")
