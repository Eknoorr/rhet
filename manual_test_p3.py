import json
import os
import sys
from services.orchestrator import MasterOrchestrator
from services.kb_service import KnowledgeBaseService
from services.guardrails import GuardrailService
from services.foundry_agent import FoundryAgentClient
from models.p3_schemas import LearnerTurnInput

def print_header(title: str):
    print("\n" + "=" * 65)
    print(f"🧪 {title}")
    print("=" * 65)

def test_guardrails_unit():
    print_header("TEST 1: GUARDRAILS VERIFICATION")
    safe_text = "Quiero practicar mi español para pedir comida."
    blocked_text = "I want to talk about extreme violence and weapons."
    
    is_safe_1, msg_1 = GuardrailService.validate_input(safe_text)
    print(f"Input 1: '{safe_text}'")
    print(f"Result : Safe={is_safe_1}, Message='{msg_1}'")
    
    is_safe_2, msg_2 = GuardrailService.validate_input(blocked_text)
    print(f"\nInput 2: '{blocked_text}'")
    print(f"Result : Safe={is_safe_2}, Message='{msg_2}'")

def test_kb_retrieval_unit():
    print_header("TEST 2: KNOWLEDGE BASE (KB) RETRIEVAL")
    kb = KnowledgeBaseService()
    query = input("Enter search query for KB (default 'restaurant ordering'): ").strip() or "restaurant ordering"
    
    print(f"\nSearching KB for: '{query}'...")
    results = kb.retrieve_context(query=query)
    print(f"Retrieved {len(results)} context item(s):")
    print(json.dumps(results, indent=2, ensure_ascii=False))

def test_foundry_agent_unit():
    print_header("TEST 3: FOUNDRY AGENT REASONING (TEXT INPUT)")
    agent = FoundryAgentClient()
    
    sample_signal = {
        "transcript": "Buenos días, quiero dos tacos de pollo.",
        "reference_text": "Buenos días, quiero dos tacos de pollo.",
        "pronunciation_scores": {"pronunciation_score": 92.0, "accuracy_score": 90.0, "fluency_score": 94.0},
        "detected_language": "es",
        "key_phrases": ["tacos", "pollo"],
        "entities": [{"text": "tacos", "category": "Product"}],
        "native_gloss": "Good morning, I want two chicken tacos."
    }
    sample_kb = [{"content": "Mexican restaurant dialogue vocabulary: tacos, salsa, cuenta."}]
    
    print("Simulated Structured Signal from P4:")
    print(json.dumps(sample_signal, indent=2, ensure_ascii=False))
    
    print("\nSending structured signal to Foundry Agent...")
    reply = agent.generate_tutor_turn(structured_signal=sample_signal, kb_context=sample_kb)
    print("\n--- Agent Response ---")
    print(json.dumps(reply, indent=2, ensure_ascii=False))

def test_e2e_text_turn(orchestrator: MasterOrchestrator):
    print_header("TEST 4: FULL ORCHESTRATOR TURN (TEXT INPUT)")
    text = input("Enter learner text (default 'Hola, quiero una mesa para dos personas.'): ").strip()
    if not text:
        text = "Hola, quiero una mesa para dos personas."
    
    lang = input("Enter target language (default 'es-ES'): ").strip() or "es-ES"
    
    turn_input = LearnerTurnInput(
        user_id="manual_test_user",
        target_language=lang,
        raw_text_input=text
    )
    
    print("\nExecuting Orchestrator turn (Guardrails -> KB -> Agent -> TTS)...")
    res = orchestrator.process_turn(turn_input)
    
    print("\n--- Master Orchestrator Result ---")
    print(f"Success         : {res.success}")
    print(f"Transcript      : {res.transcript}")
    print(f"Detected Lang   : {res.detected_language}")
    print(f"Native Gloss    : {res.native_gloss}")
    print(f"Tutor Feedback  : {res.feedback}")
    print(f"Tutor Reply     : {res.next_prompt}")
    print(f"Audio Path      : {res.tutor_audio_path}")
    if res.error:
        print(f"Error           : {res.error}")

def test_e2e_voice_turn(orchestrator: MasterOrchestrator):
    print_header("TEST 5: FULL ORCHESTRATOR TURN (LIVE VOICE + PRONUNCIATION)")
    target = input("Enter target sentence (default 'Buenos días, me gustaría un café por favor.'): ").strip()
    if not target:
        target = "Buenos días, me gustaría un café por favor."
    
    lang = input("Enter language (default 'es-ES'): ").strip() or "es-ES"
    
    print(f"\n👉 Target Sentence: \"{target}\"")
    print("🎙️ Please speak into your microphone now...")
    
    turn_input = LearnerTurnInput(
        user_id="manual_voice_user",
        target_language=lang,
        target_sentence=target
    )
    
    res = orchestrator.process_turn(turn_input)
    
    print("\n--- End-to-End Voice Turn Result ---")
    print(f"Success         : {res.success}")
    print(f"Recognized Text : {res.transcript}")
    print(f"Pronunciation   : {res.pronunciation_scores}")
    print(f"Tutor Feedback  : {res.feedback}")
    print(f"Tutor Reply     : {res.next_prompt}")
    print(f"Audio Generated : {res.tutor_audio_path}")
    if res.error:
        print(f"Error           : {res.error}")

def main():
    print("=" * 65)
    print("🚀 PERSON 3 INTEGRATION MANUAL TEST RUNNER")
    print("=" * 65)
    
    try:
        orchestrator = MasterOrchestrator()
    except Exception as e:
        print(f"⚠️ Orchestrator Init Warning: {e}")
        orchestrator = None

    while True:
        print("\nChoose an integration test:")
        print("  1. Test Guardrails (Safety Filter)")
        print("  2. Test Knowledge Base (KB) Retrieval")
        print("  3. Test Foundry Agent Reasoning (Text -> JSON Reply)")
        print("  4. Test Full Orchestrator Turn (Text Input)")
        print("  5. Test Full Orchestrator Turn (Live Voice Input via P4)")
        print("  6. Exit")
        
        choice = input("\nEnter choice (1-6): ").strip()
        if choice == "1":
            test_guardrails_unit()
        elif choice == "2":
            test_kb_retrieval_unit()
        elif choice == "3":
            test_foundry_agent_unit()
        elif choice == "4":
            if orchestrator:
                test_e2e_text_turn(orchestrator)
        elif choice == "5":
            if orchestrator:
                test_e2e_voice_turn(orchestrator)
        elif choice == "6":
            print("\nExiting integration test runner.")
            break
        else:
            print("Invalid choice, please select 1-6.")

if __name__ == "__main__":
    main()
