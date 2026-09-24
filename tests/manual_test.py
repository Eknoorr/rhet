import json
import os
import sys
from services.speech_service import SpeechService
from services.language_analysis_service import LanguageAnalysisService


def print_header(title: str):
    print("\n" + "=" * 60)
    print(f"🧪 {title}")
    print("=" * 60)


def test_speech_to_text(speech: SpeechService):
    print_header("TEST 1: SPEECH-TO-TEXT (STT)")
    lang = input("Enter language code (default 'en-US', or 'es-ES'): ").strip() or "en-US"
    print(f"\n🎙️ Speak into your microphone now (Language: {lang})...")
    
    try:
        res = speech.speech_to_text(language=lang)
        print("\n--- STT Result ---")
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return res.get("text")
    except Exception as e:
        print(f"❌ Error during STT: {e}")
        return None


def test_pronunciation_assessment(speech: SpeechService):
    print_header("TEST 2: PRONUNCIATION ASSESSMENT")
    ref_text = input("Enter reference sentence (e.g., 'Buenos días por favor'): ").strip()
    if not ref_text:
        ref_text = "Buenos días por favor"
    
    lang = input("Enter language code (default 'es-ES'): ").strip() or "es-ES"
    print(f"\n🎙️ Please read aloud: \"{ref_text}\"")
    
    try:
        res = speech.assess_pronunciation(reference_text=ref_text, language=lang)
        print("\n--- Pronunciation Assessment Result ---")
        print(json.dumps(res, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ Error during Pronunciation Assessment: {e}")


def test_text_to_speech(speech: SpeechService):
    print_header("TEST 3: TEXT-TO-SPEECH (TTS)")
    text = input("Enter text to synthesize (e.g. 'Hola, bienvenido a la clase'): ").strip()
    if not text:
        text = "Hola, bienvenido a la clase."
    
    voice = input("Enter voice (default 'es-ES-ElviraNeural' / 'en-US-JennyNeural'): ").strip() or "es-ES-ElviraNeural"
    save_file = input("Save to audio file? (y/n, default 'n'): ").strip().lower()
    
    out_path = "tts_output_test.wav" if save_file == "y" else None
    
    try:
        print("\n🔊 Synthesizing audio...")
        res = speech.text_to_speech(text=text, voice_name=voice, output_audio_path=out_path)
        print("\n--- TTS Result ---")
        print(json.dumps(res, indent=2, ensure_ascii=False))
        if out_path and os.path.exists(out_path):
            print(f"✅ Audio saved locally to '{out_path}'")
    except Exception as e:
        print(f"❌ Error during TTS: {e}")


def test_nlp_and_gloss(nlp: LanguageAnalysisService, preset_text: str | None = None):
    print_header("TEST 4: LANGUAGE ANALYSIS & TRANSLATOR GLOSS")
    if preset_text:
        use_preset = input(f"Use previous recognized text ('{preset_text}')? (y/n, default 'y'): ").strip().lower()
        if use_preset != "n":
            text = preset_text
        else:
            text = input("Enter text to analyze: ").strip()
    else:
        text = input("Enter text to analyze (e.g., 'Quiero viajar a Barcelona y comer paella.'): ").strip()
        if not text:
            text = "Quiero viajar a Barcelona y comer paella."
    
    target_lang = input("Enter target gloss language (default 'en'): ").strip() or "en"
    
    try:
        print(f"\n🧠 Analyzing text: \"{text}\"...")
        res = nlp.analyze_and_translate(text=text, target_gloss_language=target_lang)
        print("\n--- Structured NLP Signal for Person 3 & 5 ---")
        print(json.dumps(res, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ Error during NLP & Glossing: {e}")


def test_full_pipeline(speech: SpeechService, nlp: LanguageAnalysisService):
    print_header("TEST 5: FULL END-TO-END PIPELINE (MIC -> NLP -> GLOSS -> TTS)")
    ref = "Me gustaría reservar una mesa para dos personas."
    print(f"1. Pronunciation Target: \"{ref}\"")
    print("🎙️ Please speak the sentence into your microphone now...")
    
    pron_res = speech.assess_pronunciation(reference_text=ref, language="es-ES")
    print("\n[Step 1 - Speech Assessment]:")
    print(json.dumps(pron_res, indent=2, ensure_ascii=False))
    
    spoken_text = pron_res.get("recognized_text") or ref
    print(f"\n[Step 2 - NLP & Glossing on '{spoken_text}']:")
    nlp_res = nlp.analyze_and_translate(text=spoken_text, target_gloss_language="en")
    print(json.dumps(nlp_res, indent=2, ensure_ascii=False))
    
    print("\n[Step 3 - TTS AI Response Audio Playback]:")
    reply = "¡Perfecto! Su mesa para dos está confirmada."
    print(f"AI Spoken Reply: \"{reply}\"")
    tts_res = speech.text_to_speech(text=reply, voice_name="es-ES-ElviraNeural")
    print(json.dumps(tts_res, indent=2, ensure_ascii=False))


def main():
    print("=" * 60)
    print("🚀 MANUAL VERIFICATION TEST SUITE (PERSON 4)")
    print("=" * 60)
    
    try:
        speech = SpeechService()
        nlp = LanguageAnalysisService()
    except Exception as e:
        print(f"\n⚠️ Initialization Error: {e}")
        print("Ensure your .env file has valid keys or check Azure configurations.")
        sys.exit(1)
        
    last_text = None
    while True:
        print("\nChoose a test to run:")
        print("  1. Test Speech-to-Text (STT)")
        print("  2. Test Pronunciation Assessment")
        print("  3. Test Text-to-Speech (TTS)")
        print("  4. Test Language Analysis & Glossing")
        print("  5. Run Complete End-to-End Test (1 -> 2 -> 3)")
        print("  6. Exit")
        
        choice = input("\nEnter choice (1-6): ").strip()
        if choice == "1":
            last_text = test_speech_to_text(speech)
        elif choice == "2":
            test_pronunciation_assessment(speech)
        elif choice == "3":
            test_text_to_speech(speech)
        elif choice == "4":
            test_nlp_and_gloss(nlp, preset_text=last_text)
        elif choice == "5":
            test_full_pipeline(speech, nlp)
        elif choice == "6":
            print("\nExiting manual test runner. All done!")
            break
        else:
            print("Invalid choice, please select 1-6.")


if __name__ == "__main__":
    main()
