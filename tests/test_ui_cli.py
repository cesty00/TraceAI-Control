from src.ui.cli import build_parser, build_request_from_args, main
from src.ui.orchestrator import UiGenerationRequest, UiGenerationResult


def test_build_request_from_args_maps_cli_arguments() -> None:
    parser = build_parser()
    args = parser.parse_args([
        "/data",
        "--code",
        "DS0001",
        "--lot",
        "L001",
        "--output",
        "/tmp/report.docx",
    ])

    request = build_request_from_args(args)

    assert request == UiGenerationRequest(
        source_directory="/data",
        code="DS0001",
        lot="L001",
        output_docx_path="/tmp/report.docx",
    )


def test_main_returns_zero_and_prints_success_message(capsys) -> None:
    received_requests: list[UiGenerationRequest] = []

    def handler(request: UiGenerationRequest) -> UiGenerationResult:
        received_requests.append(request)
        return UiGenerationResult(
            success=True,
            output_path="/tmp/report.docx",
            message="Raport generat cu succes: /tmp/report.docx",
        )

    exit_code = main(
        ["/data", "--code", "DS0001", "--lot", "L001", "--output", "/tmp/report.docx"],
        request_handler=handler,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Raport generat cu succes" in captured.out
    assert received_requests == [
        UiGenerationRequest(
            source_directory="/data",
            code="DS0001",
            lot="L001",
            output_docx_path="/tmp/report.docx",
        )
    ]


def test_main_returns_one_and_prints_error_message(capsys) -> None:
    def handler(request: UiGenerationRequest) -> UiGenerationResult:
        return UiGenerationResult(
            success=False,
            output_path=None,
            message="Eroare la generarea raportului.",
            error="engine failed",
        )

    exit_code = main(
        ["/data", "--code", "DS0001", "--lot", "L001", "--output", "/tmp/report.docx"],
        request_handler=handler,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "engine failed" in captured.out
