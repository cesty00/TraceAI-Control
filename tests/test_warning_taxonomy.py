from src.core.preflight_report import PreflightReport, PreflightSubjectStatus, STATUS_WARNING
from src.core.warning_taxonomy import (
    DiagnosticZipPolicy,
    EscalationPolicy,
    OperatorAction,
    WarningTaxonomySeverity,
    classify_cumulative_warnings,
    classify_repeated_warning,
    data_quality_error_non_blocking,
    diagnostic_zip_missing_material_warning,
    missing_single_primary_source,
    missing_stock_for_code_lot,
)
from src.ui.visual import (
    DOCX_GATE_ALLOW,
    DOCX_GATE_BLOCK,
    DOCX_GATE_CONFIRM,
    PREFLIGHT_NEXT_STEP_BLOCKER_MESSAGE,
    PREFLIGHT_NEXT_STEP_OK_MESSAGE,
    PREFLIGHT_NEXT_STEP_WARNING_MESSAGE,
    PREFLIGHT_WARNING_CONFIRMATION_MESSAGE,
    build_preflight_gate_snapshot,
    build_preflight_operator_next_step,
    evaluate_docx_generation_gate,
)


def test_missing_stock_maps_to_warning_review() -> None:
    classification = missing_stock_for_code_lot()

    assert classification.severity == WarningTaxonomySeverity.WARNING_REVIEW
    assert classification.operator_action == OperatorAction.REVIEW_AND_CONTINUE
    assert classification.diagnostic_zip_policy == DiagnosticZipPolicy.RECOMMENDED
    assert classification.escalation_policy == EscalationPolicy.NO
    assert classification.can_transition_to_blocker is False


def test_single_primary_source_missing_maps_to_warning_escalate() -> None:
    classification = missing_single_primary_source()

    assert classification.severity == WarningTaxonomySeverity.WARNING_ESCALATE
    assert classification.operator_action == OperatorAction.CONTROLLED_CONTINUE
    assert classification.escalation_policy == EscalationPolicy.RECOMMENDED
    assert classification.can_transition_to_blocker is True


def test_data_quality_error_non_blocking_maps_to_warning_escalate() -> None:
    classification = data_quality_error_non_blocking()

    assert classification.severity == WarningTaxonomySeverity.WARNING_ESCALATE
    assert classification.operator_action == OperatorAction.CONTROLLED_CONTINUE
    assert classification.diagnostic_zip_policy == DiagnosticZipPolicy.RECOMMENDED
    assert classification.escalation_policy == EscalationPolicy.RECOMMENDED


def test_repeated_warning_raises_severity_by_one_level() -> None:
    original = missing_stock_for_code_lot()

    repeated = classify_repeated_warning(original, occurrence_count=2)

    assert original.severity == WarningTaxonomySeverity.WARNING_REVIEW
    assert repeated.severity == WarningTaxonomySeverity.WARNING_ESCALATE
    assert repeated.operator_action == OperatorAction.CONTROLLED_CONTINUE


def test_cumulative_review_warnings_raise_to_warning_escalate() -> None:
    cumulative = classify_cumulative_warnings(
        [missing_stock_for_code_lot(), missing_stock_for_code_lot()]
    )

    assert cumulative.severity == WarningTaxonomySeverity.WARNING_ESCALATE
    assert cumulative.escalation_policy == EscalationPolicy.RECOMMENDED


def test_source_degradation_data_quality_error_and_missing_diagnostic_zip_raise_critical() -> None:
    cumulative = classify_cumulative_warnings(
        [
            missing_single_primary_source(),
            data_quality_error_non_blocking(),
            diagnostic_zip_missing_material_warning(),
        ]
    )

    assert cumulative.severity == WarningTaxonomySeverity.WARNING_CRITICAL
    assert cumulative.operator_action == OperatorAction.STOP_FOR_HUMAN_REVIEW
    assert cumulative.diagnostic_zip_policy == DiagnosticZipPolicy.REQUIRED
    assert cumulative.escalation_policy == EscalationPolicy.REQUIRED
    assert cumulative.can_transition_to_blocker is True


def test_ds099903883_105_26_remains_warning_compatible_not_blocker() -> None:
    report = make_report(status=STATUS_WARNING, warnings=["Data Quality ERROR"], blockers=[])
    classification = data_quality_error_non_blocking()

    assert report.status == STATUS_WARNING
    assert report.blockers == []
    assert classification.severity == WarningTaxonomySeverity.WARNING_ESCALATE


def test_01b_docx_gate_remains_ok_allow_warning_confirm_blocker_block() -> None:
    ok_snapshot = build_preflight_gate_snapshot("/tmp/sources", "DS0001", "L001", make_report(status="OK"))
    warning_snapshot = build_preflight_gate_snapshot(
        "/tmp/sources", "DS0001", "L001", make_report(status="WARNING")
    )
    blocker_snapshot = build_preflight_gate_snapshot(
        "/tmp/sources", "DS0001", "L001", make_report(status="BLOCKER")
    )

    assert evaluate_docx_generation_gate("/tmp/sources", "DS0001", "L001", ok_snapshot).status == DOCX_GATE_ALLOW
    warning_decision = evaluate_docx_generation_gate("/tmp/sources", "DS0001", "L001", warning_snapshot)
    blocker_decision = evaluate_docx_generation_gate("/tmp/sources", "DS0001", "L001", blocker_snapshot)

    assert warning_decision.status == DOCX_GATE_CONFIRM
    assert warning_decision.message == PREFLIGHT_WARNING_CONFIRMATION_MESSAGE
    assert blocker_decision.status == DOCX_GATE_BLOCK


def test_01c_existing_wording_is_not_modified() -> None:
    assert (
        PREFLIGHT_NEXT_STEP_OK_MESSAGE
        == "Pas următor: preflight OK. Operatorul poate continua normal spre preview / DOCX."
    )
    assert PREFLIGHT_NEXT_STEP_WARNING_MESSAGE == (
        "Pas următor: preflight WARNING. Operatorul poate continua doar cu atenție după revizuirea observațiilor. "
        "Diagnostic ZIP este recomandat pentru păstrarea dovezilor."
    )
    assert PREFLIGHT_NEXT_STEP_BLOCKER_MESSAGE == (
        "Pas următor: preflight BLOCKER. Operatorul trebuie să se oprească, să corecteze sursele sau să escaladeze. "
        "Diagnostic ZIP este recomandat pentru investigație."
    )
    assert build_preflight_operator_next_step(make_report(status="WARNING")) == PREFLIGHT_NEXT_STEP_WARNING_MESSAGE


def make_report(
    status: str,
    warnings: list[str] | None = None,
    blockers: list[str] | None = None,
) -> PreflightReport:
    default_warnings = ["warning"] if status == "WARNING" else []
    default_blockers = ["blocker"] if status == "BLOCKER" else []
    guidance = {
        "OK": "Sursele sunt pregătite. Poți continua cu generarea raportului.",
        "WARNING": "Există observații la surse. Poți continua cu atenție.",
        "BLOCKER": "Există blocaje la surse. Oprește-te înainte de generare.",
    }[status]
    return PreflightReport(
        schema_version="preflight-report.v1",
        source_directory="/tmp/sources",
        build_info={},
        sources=[],
        subject=PreflightSubjectStatus(
            code="DS0001",
            lot="L001",
            status="OK",
            total_records=2,
            records_by_source={"production": 1, "wms": 1},
        ),
        status=status,
        operator_guidance=guidance,
        warnings=default_warnings if warnings is None else warnings,
        blockers=default_blockers if blockers is None else blockers,
    )
