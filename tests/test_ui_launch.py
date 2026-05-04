import sys
import types

from src.ui import launch



def test_run_branded_visual_app_patches_tk_creation_and_applies_icon(monkeypatch) -> None:
    events: dict[str, object] = {}

    def original_tk() -> object:
        root = object()
        events["root"] = root
        return root

    fake_tk = types.SimpleNamespace(Tk=original_tk)

    def fake_apply_app_icon(root: object) -> None:
        events["icon_root"] = root

    def fake_visual_main() -> int:
        events["main_root"] = fake_tk.Tk()
        return 123

    monkeypatch.setitem(sys.modules, "tkinter", fake_tk)
    monkeypatch.setitem(sys.modules, "src.ui.visual", types.SimpleNamespace(main=fake_visual_main))
    monkeypatch.setattr(launch, "apply_app_icon", fake_apply_app_icon)

    result = launch.run_branded_visual_app()

    assert result == 123
    assert events["root"] is events["icon_root"]
    assert events["root"] is events["main_root"]
    assert fake_tk.Tk is original_tk