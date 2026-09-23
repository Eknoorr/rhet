import streamlit as st
from services.orchestrator import MasterOrchestrator
from models.p3_schemas import LearnerTurnInput

st.set_page_config(page_title="AI Language Tutor", layout="wide")

st.title("AI Language Learning Assistant")
st.markdown("---")

orchestrator = MasterOrchestrator()

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🎙️ Learner Input")
    target_lang = st.selectbox("Select Target Language", ["es-ES", "zh-CN", "hi-IN", "fr-FR", "en-US"])
    target_sentence = st.text_input("Target Sentence Prompt", value="Buenos días por favor")
    
    if st.button("🎤 Speak & Submit Turn"):
        with st.spinner("Processing Voice & Assessment..."):
            turn_input = LearnerTurnInput(
                user_id="user_123",
                target_language=target_lang,
                target_sentence=target_sentence
            )
            response = orchestrator.process_turn(turn_input)
            st.session_state["last_response"] = response

with col2:
    st.subheader("🤖 AI Tutor Feedback & Response")
    if "last_response" in st.session_state:
        res = st.session_state["last_response"]
        if res.success:
            st.success(f"**Transcript:** {res.transcript}")
            if res.pronunciation_scores:
                st.metric("Pronunciation Score", f"{res.pronunciation_scores.get('pronunciation_score', 0)}/100")
            st.info(f"**Tutor Feedback:** {res.feedback}")
            st.markdown(f"**Tutor Reply:** *{res.next_prompt}*")
            st.caption(f"English Gloss: {res.native_gloss}")
            if res.tutor_audio_path:
                st.audio(res.tutor_audio_path)
        else:
            st.error(res.error)
