import streamlit as st

# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="parrhet.ai",
    page_icon="🦜",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# FONTS & STYLESHEET (CLEAN, HUMAN, PREMIUM THEME)
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
        radial-gradient(at 100% 0%, rgba(56, 189, 248, 0.04) 0px, transparent 45%),
        radial-gradient(at 50% 100%, rgba(16, 185, 129, 0.04) 0px, transparent 50%);
    color: #f1f5f9;
    font-family: 'Plus Jakarta Sans', sans-serif;
    overflow-x: hidden;
}

[data-testid="stHeader"] {
    background-color: transparent;
}

#MainMenu, footer {
    visibility: hidden;
}

.block-container {
    padding-top: 0rem;
    padding-left: 0rem;
    padding-right: 0rem;
    padding-bottom: 5rem;
    max-width: 100%;
}

/* =========================================================
   AMBIENT BACKGROUND ACCENTS (MUTED & SOFT)
   ========================================================= */

.ambient-orb {
    position: fixed;
    border-radius: 50%;
    pointer-events: none;
    z-index: 0;
    filter: blur(100px);
}

.orb-one {
    width: 440px;
    height: 440px;
    background: radial-gradient(circle, rgba(34, 197, 94, 0.15) 0%, transparent 70%);
    top: -200px;
    left: -150px;
    animation: floatOrbOne 16s ease-in-out infinite alternate;
}

.orb-two {
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(56, 189, 248, 0.12) 0%, transparent 70%);
    top: 30%;
    right: -150px;
    animation: floatOrbTwo 18s ease-in-out infinite alternate;
}

@keyframes floatOrbOne {
    0% { transform: translate(0, 0); }
    100% { transform: translate(40px, 60px); }
}

@keyframes floatOrbTwo {
    0% { transform: translate(0, 0); }
    100% { transform: translate(-50px, 40px); }
}

/* =========================================================
   TOP NAVIGATION BAR
   ========================================================= */

.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 24px 60px;
    position: relative;
    z-index: 10;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    background: rgba(8, 11, 17, 0.6);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.nav-brand {
    display: flex;
    align-items: center;
    gap: 12px;
}

.nav-brand-avatar {
    width: 38px;
    height: 38px;
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(56, 189, 248, 0.1));
    border: 1px solid rgba(74, 222, 128, 0.3);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
}

.nav-brand-text {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.5px;
    color: #f8fafc;
}

.nav-brand-text .mint {
    color: #4ade80;
}

.nav-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 50px;
    padding: 7px 18px;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 13px;
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
   HERO SECTION & SPACED MASCOT STAGE
   ========================================================= */

.hero {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 40px 20px 10px 20px;
    z-index: 2;
}

/* MASCOT CONTAINER (CLEAN SPACING, NO OVERLAPPING BLOBS) */

.mascot-stage {
    position: relative;
    width: 440px;
    height: 270px;
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 15px auto 25px auto;
}

/* SUBTLE AURA (Strictly behind and gentle) */
.mascot-glow-disc {
    position: absolute;
    width: 170px;
    height: 170px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(34, 197, 94, 0.18) 0%, transparent 70%);
    filter: blur(35px);
    z-index: 1;
    pointer-events: none;
}

/* PARROT MASCOT (Clean sharp layer) */
.parrot-entity {
    position: relative;
    z-index: 10;
    animation: floatMascot 4.8s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite alternate;
}

@keyframes floatMascot {
    0% { transform: translateY(0px) rotate(0deg); }
    50% { transform: translateY(-10px) rotate(1.5deg); }
    100% { transform: translateY(3px) rotate(-1deg); }
}

.svg-parrot {
    display: block;
    width: 170px;
    height: auto;
    filter: drop-shadow(0 10px 20px rgba(0, 0, 0, 0.45));
}

.wing-top, .wing-bottom {
    transform-box: view-box;
    animation: flapFluid 0.5s ease-in-out infinite alternate;
}

.wing-top { transform-origin: 60px 40px; }
.wing-bottom { transform-origin: 60px 70px; animation-delay: 0.25s; }

@keyframes flapFluid {
    from { transform: rotate(-22deg); }
    to { transform: rotate(22deg); }
}

/* ORBITING SPEECH BUBBLES (SPACED OUT FROM THE PARROT) */

.orbit-chip {
    position: absolute;
    background: rgba(14, 20, 32, 0.85);
    border: 1px solid rgba(74, 222, 128, 0.25);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border-radius: 30px;
    padding: 8px 18px;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 13px;
    font-weight: 600;
    color: #f1f5f9;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
    white-space: nowrap;
    z-index: 8;
    pointer-events: none;
}

.chip-left {
    left: -80px;
    top: 50px;
    animation: orbitFloatLeft 6s ease-in-out infinite alternate;
}

.chip-right {
    right: -85px;
    top: 115px;
    animation: orbitFloatRight 7s ease-in-out infinite alternate;
}

.chip-top {
    right: -20px;
    top: -15px;
    animation: orbitFloatTop 6.5s ease-in-out infinite alternate;
}

@keyframes orbitFloatLeft {
    0% { transform: translateY(0px) rotate(-1.5deg); }
    100% { transform: translateY(-10px) rotate(1deg); }
}

@keyframes orbitFloatRight {
    0% { transform: translateY(0px) rotate(1.5deg); }
    100% { transform: translateY(12px) rotate(-1deg); }
}

@keyframes orbitFloatTop {
    0% { transform: translateY(0px); }
    100% { transform: translateY(-8px); }
}

/* AUDIO SOUNDWAVE BARS */

.soundwave-bar-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    height: 22px;
    margin-top: 6px;
    margin-bottom: 14px;
}

.eq-bar {
    width: 3.5px;
    background: linear-gradient(180deg, #4ade80 0%, #22c55e 100%);
    border-radius: 4px;
    animation: soundPulse 1.2s ease-in-out infinite alternate;
}

.eq-bar:nth-child(1) { height: 8px; animation-delay: 0.1s; }
.eq-bar:nth-child(2) { height: 16px; animation-delay: 0.3s; }
.eq-bar:nth-child(3) { height: 22px; animation-delay: 0.0s; }
.eq-bar:nth-child(4) { height: 14px; animation-delay: 0.4s; }
.eq-bar:nth-child(5) { height: 8px; animation-delay: 0.2s; }

@keyframes soundPulse {
    0% { transform: scaleY(0.4); opacity: 0.5; }
    100% { transform: scaleY(1.0); opacity: 0.95; }
}

/* HERO HEADLINE & COPY (NATURAL, IMPACTFUL, REFINED) */

.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 64px;
    font-weight: 700;
    line-height: 1.1;
    letter-spacing: -2px;
    color: #ffffff;
    margin-bottom: 14px;
    max-width: 820px;
}

.hero-title .gradient-text {
    background: linear-gradient(135deg, #ffffff 10%, #86efac 60%, #4ade80 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 19px;
    font-weight: 400;
    color: #94a3b8;
    max-width: 600px;
    line-height: 1.6;
    margin-bottom: 26px;
}

/* FEATURE PILLS */

.hero-feature-row {
    display: flex;
    gap: 12px;
    justify-content: center;
    flex-wrap: wrap;
    margin-bottom: 34px;
}

.feature-tag {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 40px;
    padding: 8px 22px;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 13.5px;
    font-weight: 600;
    color: #cbd5e1;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.feature-tag:hover {
    border-color: rgba(74, 222, 128, 0.35);
    background: rgba(34, 197, 94, 0.06);
    color: #ffffff;
    transform: translateY(-1px);
}

/* =========================================================
   START LEARNING CTA BUTTON (CLEAN & CENTERED)
   ========================================================= */

div[data-testid="stButton"] {
    display: flex;
    justify-content: center;
    position: relative;
    z-index: 10;
    margin: 6px auto 55px auto;
}

div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #22c55e 0%, #10b981 100%);
    color: #05080d;
    border: none;
    border-radius: 50px;
    padding: 18px 56px;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 21px;
    font-weight: 700;
    letter-spacing: -0.3px;
    min-height: 64px;
    box-shadow: 0 4px 25px rgba(34, 197, 94, 0.35);
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    cursor: pointer;
}

div[data-testid="stButton"] > button:hover {
    background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
    color: #030508;
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 8px 35px rgba(74, 222, 128, 0.5);
}

div[data-testid="stButton"] > button:active {
    transform: translateY(1px) scale(0.99);
}

/* =========================================================
   FEATURE SHOWCASE GRID (REPLACES STUCK SEARCH BAR)
   ========================================================= */

.showcase-grid {
    max-width: 900px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 18px;
    padding: 0 20px 40px 20px;
    position: relative;
    z-index: 2;
}

.showcase-card {
    background: rgba(13, 18, 28, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 20px;
    padding: 24px 22px;
    backdrop-filter: blur(16px);
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.showcase-card:hover {
    border-color: rgba(74, 222, 128, 0.25);
    background: rgba(18, 25, 38, 0.7);
    transform: translateY(-3px);
}

.showcase-icon {
    font-size: 28px;
    margin-bottom: 14px;
    display: inline-block;
}

.showcase-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 17px;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 8px;
}

.showcase-desc {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 13.5px;
    font-weight: 400;
    color: #94a3b8;
    line-height: 1.5;
}

/* =========================================================
   MOBILE RESPONSIVENESS
   ========================================================= */

@media (max-width: 768px) {
    .navbar {
        padding: 16px 20px;
    }

    .hero-title {
        font-size: 38px;
        letter-spacing: -1px;
    }

    .hero-subtitle {
        font-size: 16px;
    }

    .mascot-stage {
        width: 300px;
        height: 220px;
    }

    .svg-parrot {
        width: 130px;
    }

    .chip-left {
        left: -35px;
        top: 20px;
        font-size: 11px;
    }

    .chip-right {
        right: -35px;
        top: 80px;
        font-size: 11px;
    }

    .chip-top {
        right: -10px;
        top: -15px;
        font-size: 11px;
    }

    div[data-testid="stButton"] > button {
        font-size: 18px;
        padding: 16px 36px;
    }

    .showcase-grid {
        grid-template-columns: 1fr;
    }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# AMBIENT BACKGROUND ACCENTS
# ============================================================

st.markdown("""<div class="ambient-orb orb-one"></div>
<div class="ambient-orb orb-two"></div>""", unsafe_allow_html=True)

# ============================================================
# TOP NAVIGATION BAR
# ============================================================

st.markdown("""<header class="navbar">
<div class="nav-brand">
<div class="nav-brand-avatar">🦜</div>
<div class="nav-brand-text">parrhet<span class="mint">.ai</span></div>
</div>
<div class="nav-badge">
<span class="pulse-dot"></span> Interactive Language Studio
</div>
</header>""", unsafe_allow_html=True)

# ============================================================
# HERO SECTION (SPACED MASCOT & CLEAN COPY)
# ============================================================

st.markdown("""<div class="hero">
<div class="mascot-stage">
<div class="mascot-glow-disc"></div>
<div class="orbit-chip chip-left">¡Hola! ¿Cómo estás? 🇪🇸</div>
<div class="orbit-chip chip-right">Bonjour! Prêt à parler? 🇫🇷</div>
<div class="orbit-chip chip-top">こんにちは! 🇯🇵</div>
<div class="parrot-entity">
<svg class="svg-parrot" viewBox="0 0 130 110" xmlns="http://www.w3.org/2000/svg">
<path d="M44 68 L6 26 L18 20 L48 58 Z" fill="#22c55e" stroke="#04070a" stroke-width="3" stroke-linejoin="round"/>
<path d="M46 74 L16 42 L26 38 L50 68 Z" fill="#4ade80" stroke="#04070a" stroke-width="3" stroke-linejoin="round"/>
<g class="wing-bottom">
<path d="M62 66 Q50 96 84 92 Q80 76 70 66 Z" fill="#15803d" stroke="#04070a" stroke-width="3" stroke-linejoin="round"/>
</g>
<ellipse cx="72" cy="62" rx="30" ry="24" fill="#22c55e" stroke="#04070a" stroke-width="4"/>
<ellipse cx="78" cy="68" rx="18" ry="14" fill="#86efac" stroke="#04070a" stroke-width="3"/>
<g class="wing-top">
<path d="M64 50 Q54 12 84 10 Q80 34 70 52 Z" fill="#16a34a" stroke="#04070a" stroke-width="3" stroke-linejoin="round"/>
</g>
<circle cx="96" cy="40" r="18" fill="#4ade80" stroke="#04070a" stroke-width="4"/>
<path d="M110 32 L128 41 L110 48 Z" fill="#f59e0b" stroke="#04070a" stroke-width="3" stroke-linejoin="round"/>
<circle cx="93" cy="37" r="3.5" fill="#04070a"/>
<circle cx="94" cy="36" r="1.2" fill="#ffffff"/>
<circle cx="38" cy="58" r="5" fill="#04070a"/>
<circle cx="72" cy="88" r="4.5" fill="#04070a"/>
</svg>
</div>
</div>
<div class="soundwave-bar-wrap">
<span class="eq-bar"></span>
<span class="eq-bar"></span>
<span class="eq-bar"></span>
<span class="eq-bar"></span>
<span class="eq-bar"></span>
</div>
<h1 class="hero-title">
Master Languages,<br><span class="gradient-text">Anytime Anywhere.</span>
</h1>
<p class="hero-subtitle">
Practice speaking with your personal conversational tutor. Get instant pronunciation feedback and build real-world fluency at your own pace.
</p>
<div class="hero-feature-row">
<div class="feature-tag">🎙️ Real-time Speaking Practice</div>
<div class="feature-tag">🌍 50+ Global Languages</div>
<div class="feature-tag">🎯 Instant Pronunciation Coaching</div>
</div>
</div>""", unsafe_allow_html=True)

# ============================================================
# START LEARNING CTA BUTTON
# ============================================================

if st.button("✨ Start Learning Now", key="start_learning", use_container_width=False):
    st.switch_page("pages/learn.py")

# ============================================================
# SHOWCASE PATHWAY CARDS (CLEAN & SUBSTANTIAL)
# ============================================================

st.markdown("""<div class="showcase-grid">
<div class="showcase-card">
<span class="showcase-icon">🗣️</span>
<div class="showcase-title">Conversational Immersion</div>
<div class="showcase-desc">Engage in realistic dialogues from ordering espresso in Rome to navigating Tokyo subways.</div>
</div>
<div class="showcase-card">
<span class="showcase-icon">🎯</span>
<div class="showcase-title">Accent & Pronunciation</div>
<div class="showcase-desc">Listen, repeat, and polish your accent with immediate phonetic guidance and tone coaching.</div>
</div>
<div class="showcase-card">
<span class="showcase-icon">⚡</span>
<div class="showcase-title">Natural Fluency</div>
<div class="showcase-desc">Learn idioms, colloquial phrasing, and cultural context effortlessly in 5-minute sessions.</div>
</div>
</div>""", unsafe_allow_html=True)
