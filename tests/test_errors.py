from src.errors import MissingSourceFileError, TraceAIError


def test_traceai_error_formats_user_message_detail_and_action() -> None:
    error = TraceAIError(
        user_message="Nu pot genera raportul.",
        technical_detail="Detaliu tehnic pentru diagnostic.",
        recommended_action="Corectează datele și reîncearcă.",
    )

    rendered = str(error)

    assert "Nu pot genera raportul." in rendered
    assert "Detalii tehnice: Detaliu tehnic pentru diagnostic." in rendered
    assert "Acțiune recomandată: Corectează datele și reîncearcă." in rendered


def test_specific_traceai_errors_remain_catchable_as_base_error() -> None:
    error = MissingSourceFileError(
        user_message="Lipsește o sursă obligatorie.",
        technical_detail="Fișier lipsă: trasabilitate_wms.csv",
    )

    assert isinstance(error, TraceAIError)
    assert error.user_message == "Lipsește o sursă obligatorie."
