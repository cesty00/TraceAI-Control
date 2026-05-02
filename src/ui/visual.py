"""Minimal visual UI shell for TraceAI Control.

The visual UI is intentionally thin. It collects the same core fields as the
CLI, calls the UI orchestration boundary, and displays the returned status.

For audit checklist preview, it consumes the stable ``audit-checklist-ui.v1``
view model. It does not rebuild report data, read operational source files, or
contain traceability business logic.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from src.ui.audit_checklist_view_model import (
    AuditChecklistUiSection,
    AuditChecklistUiViewModel,
    build_audit_checklist_ui_view_model,
)
from src.ui.orchestrator import UiGenerationRequest, UiGenerationResult, generate_report_from_ui_request

VisualRequestHandler = Callable[[UiGenerationRequest], UiGenerationResult]
AuditChecklistPayloadBuilder = Callable[[str, str, str], dict[str, Any]]
AuditChecklistViewModelBuilder = Callable[[dict[str, Any]], AuditChecklistUiViewModel]

APP_TITLE = "TraceAI Control — Modul Trasabilitate"


@dataclass(frozen=True)
class VisualAuditChecklistResult:
    """Stable status returned when the visual UI asks for audit checklist data."""

    success: bool
    view_model: AuditChecklistUiViewModel | None
    message: str
    error: str | None = None


def build_request_from_form_values(
    source_directory: str,
    code: str,
    lot: str,
    output_docx_path: str,
) -> UiGenerationRequest:
    """Build a UiGenerationRequest from visual form values."""

    return UiGenerationRequest(
        source_directory=source_directory,
        code=code,
        lot=lot,
        output_docx_path=output_docx_path,
    )


def submit_visual_form_values(
    source_directory: str,
    code: str,
    lot: str,
    output_docx_path: str,
    request_handler: VisualRequestHandler = generate_report_from_ui_request,
) -> UiGenerationResult:
    """Submit visual form values through the orchestration boundary."""

    request = build_request_from_form_values(
        source_directory=source_directory,
        code=code,
        lot=lot,
        output_docx_path=output_docx_path,
    )
    return request_handler(request)


def submit_audit_checklist_form_values(
    source_directory: str,
    code: str,
    lot: str,
    payload_builder: AuditChecklistPayloadBuilder | None = None,
    view_model_builder: AuditChecklistViewModelBuilder = build_audit_checklist_ui_view_model,
) -> VisualAuditChecklistResult:
    """Build the audit checklist view model from visual form values.

    This is UI orchestration only: source parsing and report construction remain
    behind ``build_audit_checklist_ui_payload``; section mapping remains behind
    ``build_audit_checklist_ui_view_model``.
    """

    validation_error = validate_audit_checklist_form_values(source_directory, code, lot)
    if validation_error:
        return VisualAuditChecklistResult(
            success=False,
            view_model=None,
            message="Date UI incomplete pentru previzualizarea audit checklist.",
            error=validation_error,
        )

    try:
        builder = payload_builder or default_audit_checklist_payload_builder
        payload = builder(source_directory, code, lot)
        view_model = view_model_builder(payload)
    except Exception as exc:  # pragma: no cover - exact exception belongs to engine/audit layer
        return VisualAuditChecklistResult(
            success=False,
            view_model=None,
            message="Eroare la generarea previzualizării audit checklist.",
            error=str(exc),
        )

    return VisualAuditChecklistResult(
        success=True,
        view_model=view_model,
        message="Previzualizare audit checklist generată cu succes.",
        error=None,
    )


def default_audit_checklist_payload_builder(source_directory: str, code: str, lot: str) -> dict[str, Any]:
    """Import the payload builder lazily to keep runnable UI modules isolated.

    The diagnostics workflow executes ``python -m src.ui.audit_checklist_json``.
    Importing that runnable module eagerly from ``src.ui.visual`` would load it
    before runpy executes it and would reintroduce a warning. Lazy import keeps
    the visual UI API stable without side effects.
    """

    from src.ui.audit_checklist_json import build_audit_checklist_ui_payload

    return build_audit_checklist_ui_payload(source_directory, code, lot)


def validate_audit_checklist_form_values(source_directory: str, code: str, lot: str) -> str | None:
    """Validate only UI fields needed for audit checklist preview."""

    missing_fields = [
        field_name
        for field_name, field_value in (
            ("source_directory", source_directory),
            ("code", code),
            ("lot", lot),
        )
        if not str(field_value).strip()
    ]
    if missing_fields:
        return "Câmpuri obligatorii lipsă: " + ", ".join(missing_fields)
    return None


def format_audit_checklist_preview(view_model: AuditChecklistUiViewModel, max_rows_per_section: int = 3) -> str:
    """Format a compact text preview from the audit checklist view model.

    The visual UI uses this as a safe first rendering step. It displays only data
    already present in the view model and limits table output for readability.
    """

    subject = view_model.subject
    lines = [
        f"Schema: {view_model.schema_version}",
        f"Produs: {subject.get('code', '')} / {subject.get('lot', '')}",
        f"Denumire: {subject.get('product_name', '')}",
        f"Rezultat: {subject.get('result', '')}",
        "",
    ]
    for index, section in enumerate(view_model.sections, start=1):
        lines.extend(format_audit_section_preview(index, section, max_rows_per_section))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def format_audit_section_preview(
    index: int,
    section: AuditChecklistUiSection,
    max_rows_per_section: int = 3,
) -> list[str]:
    """Format one section from the view model for display."""

    lines = [f"{index}. {section.title}"]
    if section.description:
        lines.append(f"   {section.description}")
    if section.kind == "details":
        if not section.data:
            lines.append(f"   {section.empty_message}")
            return lines
        for key in section.field_keys:
            lines.append(f"   - {key}: {section.data.get(key, '')}")
        return lines
    if section.kind == "table":
        if not section.rows:
            lines.append(f"   {section.empty_message}")
            return lines
        lines.append(f"   Rânduri: {len(section.rows)}")
        visible_rows = section.rows[:max_rows_per_section]
        for row_index, row in enumerate(visible_rows, start=1):
            row_preview = "; ".join(f"{key}={row.get(key, '')}" for key in section.column_keys[:4])
            lines.append(f"   [{row_index}] {row_preview}")
        hidden_count = len(section.rows) - len(visible_rows)
        if hidden_count > 0:
            lines.append(f"   ... încă {hidden_count} rând(uri)")
        return lines
    lines.append(f"   {section.empty_message}")
    return lines


def run_visual_app(
    request_handler: VisualRequestHandler = generate_report_from_ui_request,
    audit_request_handler: Callable[[str, str, str], VisualAuditChecklistResult] = submit_audit_checklist_form_values,
) -> int:
    """Run the minimal Tkinter visual shell.

    The function imports Tkinter lazily so the module remains importable in
    headless test environments.
    """

    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry("940x680")
    root.minsize(860, 600)

    main_frame = ttk.Frame(root, padding=18)
    main_frame.grid(row=0, column=0, sticky="nsew")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    main_frame.columnconfigure(1, weight=1)
    main_frame.rowconfigure(7, weight=1)

    title_label = ttk.Label(main_frame, text="TraceAI Control — audit checklist și raport DOCX", font=("Segoe UI", 14, "bold"))
    title_label.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 14))

    source_var = tk.StringVar()
    code_var = tk.StringVar()
    lot_var = tk.StringVar()
    output_var = tk.StringVar()
    status_var = tk.StringVar(value="Completați câmpurile și generați raportul sau previzualizarea audit checklist.")

    def choose_source_directory() -> None:
        selected = filedialog.askdirectory(title="Alege folderul cu sursele oficiale")
        if selected:
            source_var.set(selected)

    def choose_output_file() -> None:
        selected = filedialog.asksaveasfilename(
            title="Alege raportul DOCX generat",
            defaultextension=".docx",
            filetypes=[("Word document", "*.docx"), ("All files", "*.*")],
        )
        if selected:
            output_var.set(selected)

    def set_preview_text(text: str) -> None:
        preview_text.configure(state="normal")
        preview_text.delete("1.0", tk.END)
        preview_text.insert("1.0", text)
        preview_text.configure(state="disabled")

    def on_generate() -> None:
        result = submit_visual_form_values(
            source_directory=source_var.get(),
            code=code_var.get(),
            lot=lot_var.get(),
            output_docx_path=output_var.get(),
            request_handler=request_handler,
        )
        status_var.set(result.message if result.success else result.error or result.message)
        if result.success:
            messagebox.showinfo(APP_TITLE, result.message)
        else:
            messagebox.showerror(APP_TITLE, result.error or result.message)

    def on_preview_audit() -> None:
        result = audit_request_handler(source_var.get(), code_var.get(), lot_var.get())
        status_var.set(result.message if result.success else result.error or result.message)
        if result.success and result.view_model is not None:
            set_preview_text(format_audit_checklist_preview(result.view_model))
        else:
            set_preview_text(result.error or result.message)
            messagebox.showerror(APP_TITLE, result.error or result.message)

    ttk.Label(main_frame, text="Folder surse oficiale").grid(row=1, column=0, sticky="w", pady=4)
    ttk.Entry(main_frame, textvariable=source_var).grid(row=1, column=1, sticky="ew", pady=4, padx=(8, 8))
    ttk.Button(main_frame, text="Alege...", command=choose_source_directory).grid(row=1, column=2, sticky="ew", pady=4)

    ttk.Label(main_frame, text="Cod articol").grid(row=2, column=0, sticky="w", pady=4)
    ttk.Entry(main_frame, textvariable=code_var).grid(row=2, column=1, columnspan=2, sticky="ew", pady=4, padx=(8, 0))

    ttk.Label(main_frame, text="Lot").grid(row=3, column=0, sticky="w", pady=4)
    ttk.Entry(main_frame, textvariable=lot_var).grid(row=3, column=1, columnspan=2, sticky="ew", pady=4, padx=(8, 0))

    ttk.Label(main_frame, text="Raport DOCX output").grid(row=4, column=0, sticky="w", pady=4)
    ttk.Entry(main_frame, textvariable=output_var).grid(row=4, column=1, sticky="ew", pady=4, padx=(8, 8))
    ttk.Button(main_frame, text="Alege...", command=choose_output_file).grid(row=4, column=2, sticky="ew", pady=4)

    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=5, column=1, columnspan=2, sticky="e", pady=(16, 8))
    ttk.Button(button_frame, text="Previzualizează audit checklist", command=on_preview_audit).grid(row=0, column=0, padx=(0, 8))
    ttk.Button(button_frame, text="Generează raport DOCX", command=on_generate).grid(row=0, column=1)

    status_label = ttk.Label(main_frame, textvariable=status_var, wraplength=820)
    status_label.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(10, 8))

    preview_frame = ttk.LabelFrame(main_frame, text="Previzualizare audit checklist")
    preview_frame.grid(row=7, column=0, columnspan=3, sticky="nsew")
    preview_frame.columnconfigure(0, weight=1)
    preview_frame.rowconfigure(0, weight=1)

    preview_text = tk.Text(preview_frame, wrap="word", height=18)
    preview_text.grid(row=0, column=0, sticky="nsew")
    preview_scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=preview_text.yview)
    preview_scrollbar.grid(row=0, column=1, sticky="ns")
    preview_text.configure(yscrollcommand=preview_scrollbar.set, state="disabled")

    root.mainloop()
    return 0


def main() -> int:
    """Entry point for the minimal visual UI shell."""

    return run_visual_app()


if __name__ == "__main__":
    raise SystemExit(main())
