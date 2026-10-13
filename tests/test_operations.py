import time

from core.operations import Operation, OperationEngine, OperationState


def test_operation_engine_serializes_and_reports_progress():
    engine = OperationEngine()
    def action(cancel, progress):
        progress(0.5, "halfway")
        return 123
    operation = engine.submit(Operation("demo", action))
    engine.wait(2)
    assert operation.state == OperationState.SUCCEEDED
    assert operation.result == 123
    assert operation.progress == 0.5
