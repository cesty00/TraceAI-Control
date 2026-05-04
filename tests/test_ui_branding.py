from src.ui import branding



def test_app_logo_png_bytes_returns_png_payload() -> None:
    payload = branding.app_logo_png_bytes()

    assert payload.startswith(b"\x89PNG\r\n\x1a\n")



def test_create_app_logo_image_passes_embedded_payload_to_factory() -> None:
    captured: dict[str, object] = {}

    def fake_factory(**kwargs: object) -> str:
        captured.update(kwargs)
        return "image"

    image = branding.create_app_logo_image(fake_factory, master="root")

    assert image == "image"
    assert captured["master"] == "root"
    assert isinstance(captured["data"], str)
    assert str(captured["data"]).startswith("iVBORw0KGgo")



def test_apply_app_icon_stores_photo_reference(monkeypatch) -> None:
    class FakeRoot:
        def __init__(self) -> None:
            self.calls: list[tuple[bool, object]] = []

        def iconphoto(self, default: bool, image: object) -> None:
            self.calls.append((default, image))

    root = FakeRoot()
    monkeypatch.setattr(branding, "load_tk_logo_image", lambda master=None: "image")

    result = branding.apply_app_icon(root)

    assert result is True
    assert root.calls == [(True, "image")]
    assert root._traceai_app_icon == "image"