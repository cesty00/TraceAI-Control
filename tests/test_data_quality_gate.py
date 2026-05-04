from pathlib import Path

from src.core.normalized_dataset import build_normalized_dataset
from src.core.source_inventory import build_inventory_report
from src.quality.data_quality_gate import run_data_quality_gate


def write_csv(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def write_minimal_sources(root: Path) -> None:
    write_csv(root / "trasabilitate_wms.csv", "Cod articol,Lot,Cantitate,UM\nDS0001,L001,10,kg\n")
    write_csv(root / "rapoarte productie.csv", "Cod produs,Lot,Cantitate,UM\nDS0001,L001,10,kg\n")
    write_csv(root / "stoc la moment original.csv", "Cod articol,Lot,Stoc,UM\nDS0001,L001,5,kg\n")
    write_csv(root / "nomenclator.csv", "Cod articol,Denumire\nDS0001,Produs test\n")


def test_data_quality_gate_reports_missing_source_file(tmp_path: Path) -> None:
    write_csv(tmp_path / "trasabilitate_wms.csv", "Cod articol,Lot,Cantitate\nDS0001,L001,10\n")

    inventory = build_inventory_report(tmp_path)
    dataset = build_normalized_dataset(tmp_path)
    report = run_data_quality_gate(tmp_path, dataset=dataset, inventory=inventory)

    assert report.status.value == "ERROR"
    assert any("Lipsește sursa obligatorie" in issue.message for issue in report.issues)


def test_data_quality_gate_reports_missing_required_column(tmp_path: Path) -> None:
    write_csv(tmp_path / "trasabilitate_wms.csv", "Cod articol,Cantitate\nDS0001,10\n")

    inventory = build_inventory_report(tmp_path)
    dataset = build_normalized_dataset(tmp_path)
    report = run_data_quality_gate(tmp_path, dataset=dataset, inventory=inventory)

    assert report.status.value == "ERROR"
    assert any(issue.source_key == "wms" and "lot" in issue.message.casefold() for issue in report.issues)


def test_data_quality_gate_reports_invalid_quantity(tmp_path: Path) -> None:
    write_csv(tmp_path / "trasabilitate_wms.csv", "Cod articol,Lot,Cantitate\nDS0001,L001,abc\n")

    inventory = build_inventory_report(tmp_path)
    dataset = build_normalized_dataset(tmp_path)
    report = run_data_quality_gate(tmp_path, dataset=dataset, inventory=inventory)

    assert any(issue.source_key == "wms" and "cantități" in issue.message for issue in report.issues)
    invalid_issue = next(issue for issue in report.issues if issue.source_key == "wms" and "cantități" in issue.message)
    assert invalid_issue.row_count == 1
    assert invalid_issue.sample_rows == [2]


def test_data_quality_gate_accepts_valid_minimal_dataset(tmp_path: Path) -> None:
    write_minimal_sources(tmp_path)

    inventory = build_inventory_report(tmp_path)
    dataset = build_normalized_dataset(tmp_path)
    report = run_data_quality_gate(tmp_path, dataset=dataset, inventory=inventory)

    assert report.compact_summary()["status"] in {"OK", "WARNING"}
    assert report.compact_summary()["source_count"] == 4
    assert report.compact_summary()["sources_found"] == 4
