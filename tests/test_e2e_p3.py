import pytest
from services.orchestrator import MasterOrchestrator
from models.p3_schemas import LearnerTurnInput

def test_master_orchestrator_turn():
    orchestrator = MasterOrchestrator()
    turn_input = LearnerTurnInput(
        user_id="test_user",
        target_language="es-ES",
        raw_text_input="Hola, quiero practicar español."
    )
    res = orchestrator.process_turn(turn_input)
    assert res.success is True
    assert res.next_prompt != ""
