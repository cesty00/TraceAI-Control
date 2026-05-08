import importlib
import sys
import types
from types import SimpleNamespace

from src.quality.models import DataQualityIssue, DataQualityReport, DataQualitySeverity, DataQualityStatus


def test_traceability_case_sections_include_textual_data_quality_issues(monkeypatch) -> None:
    fake_order_mapping = types.ModuleType("src.rules.order_traceability_mapping")
    fake_order_mapping.build_order_traceability_rows = lambda _result: []
    fake_prd_mapping = types.ModuleType("src.rules.prd_table_mapping")
    fake_prd_mapping.build_source_specific_rows = lambda _result: {
        "production": [],
        "finished_goods_deliveries": [],
        "raw_materials": [],
        "packaging": [],
        "auxiliaries_gas": [],
        "wms_receipts": [],
        "prd_consumptions": [],
        "stock": [],
    }
    fake_pipeline = types.ModuleType("src.rules.run_rules_pipeline")
    fake_pipeline.RulesPipelineResult = object

    monkeypatch.setitem(sys.modules, "src.rules.order_traceability_mapping", fake_order_mapping)
    monkeypatch.setitem(sys.modules, "src.rules.prd_table_mapping", fake_prd_mapping)
    monkeypatch.setitem(sys.modules, "src.rules.run_rules_pipeline", fake_pipeline)
    sys.modules.pop("src.rules.traceability_case", None)

    module = importlib.import_module("src.rules.traceability_case")
    monkeypatch.setattr(
        module,
        "run_data_quality_gate",
        lambda *_args, **_kwargs: DataQualityReport(
            status=DataQualityStatus.WARNING,
            source_count=4,
            sources_found=4,
            issues=[
                DataQualityIssue(
                    severity=DataQualitySeverity.WARNING,
                    source_key="nomenclator",
                    source_name="nomenclator.xlsx",
                    sheet_name="Sheet2",
                    column_name="cod articol/produs",
                    message="Lipsește coloana obligatorie pentru cod articol/produs.",
                )
            ],
        ),
    )

    result = SimpleNamespace(
        case_type_detection=SimpleNamespace(case_type="FINISHED_PRODUCT", evidence=[], observations=[]),
        core=SimpleNamespace(
            normalized_dataset=SimpleNamespace(source_directory="/tmp/sources", problems=[]),
            inventory=SimpleNamespace(problems=[]),
            validation=SimpleNamespace(status="OK"),
            selection=SimpleNamespace(records=[]),
        ),
    )

    traceability_case = module.build_traceability_case(result, "DS0001", "L001")

    assert traceability_case.sections["data_quality"]["issues"] == [
        {
            "severity": "WARNING",
            "source_name": "nomenclator.xlsx",
            "sheet_name": "Sheet2",
            "column_name": "cod articol/produs",
            "message": "Lipsește coloana obligatorie pentru cod articol/produs.",
        }
    ]
