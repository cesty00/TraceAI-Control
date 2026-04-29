from src.ui.orchestrator import UiGenerationRequest, UiGenerationResult
from src.ui.visual import build_request_from_form_values, submit_visual_form_values


def test_build_request_from_form_values_maps_visual_fields() -> None:
    request = build_request_from_form_values(
        source_directory="/data",
        code="DS0001",
        lot="L001",
        output_docx_path="/tmp/report.docx",
    )

    assert request == UiGenerationRequest(
        source_directory="/data",
        code="DS0001",
        lot="L001",
        output_docx_path="/tmp/report.docx",
    )


def test_submit_visual_form_values_calls_orchestrator_handler() -> None:
    received_requests: list[UiGenerationRequest] = []

    def handler(request: UiGenerationRequest) -> UiGenerationResult:
        received_requests.append(request)
        return UiGenerationResult(
            success=True,
            output_path="/tmp/report.docx",
            message="Raport generat cu succes: /tmp/report.docx",
        )

    result = submit_visual_form_values(
        source_directory="/data",
        code="DS0001",
        lot="L001",
        output_docx_path="/tmp/report.docx",
        request_handler=handler,
    )

    assert result.success is True
    assert result.output_path == "/tmp/report.docx"
    assert received_requests == [
        UiGenerationRequest(
            source_directory="/data",
            code="DS0001",
            lot="L001",
            output_docx_path="/tmp/report.docx",
        )
    ]


def test_submit_visual_form_values_returns_error_from_handler() -> None:
    def handler(request: UiGenerationRequest) -> UiGenerationResult:
        return UiGenerationResult(
            success=False,
            output_path=None,
            message="Eroare la generarea raportului.",
            error="missing code",
        )

    result = submit_visual_form_values(
        source_directory="/data",
        code="",
        lot="L001",
        output_docx_path="/tmp/report.docx",
        request_handler=handler,
    )

    assert result.success is False
    assert result.output_path is None
    assert result.error == "missing code"
