import importlib
import sys
import types
from dataclasses import dataclass, field


def test_audit_checklist_ui_payload_preserves_textual_data_quality_issues(monkeypatch) -> None:
    fake_audit_report_module = types.ModuleType("src.audit.audit_checklist_report")

    @dataclass
    class FakeExercise:
        code: str = "DS0001"
        lot: str = "L001"
        product_name: str = "Produs test"
        case_type: str = "FINISHED_PRODUCT"
        result: str = "PASS"

    @dataclass
    class FakeChecklistReport:
        exercise: FakeExercise = field(default_factory=FakeExercise)

    fake_audit_report_module.AuditChecklistReport = FakeChecklistReport
    fake_audit_report_module.build_audit_checklist_report = lambda _report: FakeChecklistReport()
    fake_audit_report_module.audit_checklist_report_to_dict = lambda _report: {
        "conformity": [],
        "exercise": {
            "code": "DS0001",
            "lot": "L001",
            "product_name": "Produs test",
            "case_type": "FINISHED_PRODUCT",
            "result": "PASS",
        },
        "balance": {},
        "downstream": [],
        "upstream": [],
        "production_consumption": [],
        "lot_flows": [],
        "document_register": [],
        "conclusion_status": "PASS",
        "conclusion_text": "ok",
        "observations": [],
    }

    fake_traceability_module = types.ModuleType("src.audit.audit_traceability_report")
    fake_traceability_module.build_audit_traceability_report = lambda _case: object()

    fake_run_case_module = types.ModuleType("src.rules.run_traceability_case")
    fake_run_case_module.run_traceability_case = lambda *_args, **_kwargs: object()

    monkeypatch.setitem(sys.modules, "src.audit.audit_checklist_report", fake_audit_report_module)
    monkeypatch.setitem(sys.modules, "src.audit.audit_traceability_report", fake_traceability_module)
    monkeypatch.setitem(sys.modules, "src.rules.run_traceability_case", fake_run_case_module)
    sys.modules.pop("src.ui.audit_checklist_json", None)

    module = importlib.import_module("src.ui.audit_checklist_json")
    payload = module.audit_checklist_ui_payload_from_report(
        FakeChecklistReport(),
        data_quality={
            "status": "WARNING",
            "source_count": 4,
            "sources_found": 4,
            "error_count": 0,
            "warning_count": 1,
            "issue_count": 1,
            "issues": [
                {
                    "severity": "WARNING",
                    "source_name": "nomenclator.xlsx",
                    "sheet_name": "Sheet2",
                    "column_name": "cod articol/produs",
                    "message": "Lipsește coloana obligatorie pentru cod articol/produs.",
                    "extra": "ignored",
                }
            ],
        },
    )

    issues = payload["report"]["data_quality"]["issues"]
    assert issues == [
        {
            "severity": "WARNING",
            "source_name": "nomenclator.xlsx",
            "sheet_name": "Sheet2",
            "column_name": "cod articol/produs",
            "message": "Lipsește coloana obligatorie pentru cod articol/produs.",
        }
    ]
