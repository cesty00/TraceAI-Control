"""Minimal visual UI shell for TraceAI Control.

The visual UI is intentionally thin. It collects the same core fields as the
CLI, calls orchestration/core boundaries, and displays returned status.

For audit checklist preview, it consumes the stable ``audit-checklist-ui.v1``
view model. For source validation, it consumes the stable
``preflight-report.v1`` report. It does not contain traceability business logic.
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import Executor, Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.core.build_info import format_build_info_line
from src.core.preflight_report import PreflightReport, build_preflight_report, format_preflight_report
from src.ui.audit_checklist_section_widgets import (
    SectionDisplayModel,
    build_section_display_model,
    build_section_list_items,
    export_section_display_as_text,
    export_section_display_as_tsv,
    find_section_by_key,
)
from src.ui.audit_checklist_view_model import (
    AuditChecklistUiSection,
    AuditChecklistUiViewModel,
    build_audit_checklist_ui_view_model,
)
from src.ui.diagnostic_bundle_actions import (
    VisualDiagnosticBundleResult,
    submit_diagnostic_bundle_form_values,
    submit_diagnostic_bundle_form_values_async,
    suggest_diagnostic_zip_path,
)
from src.ui.orchestrator import UiGenerationRequest, UiGenerationResult, generate_report_from_ui_request

VisualRequestHandler = Callable[[UiGenerationRequest], UiGenerationResult]
AuditChecklistPayloadBuilder = Callable[[str, str, str], dict[str, Any]]
AuditChecklistViewModelBuilder = Callable[[dict[str, Any]], AuditChecklistUiViewModel]
AuditChecklistRequestHandler = Callable[[str, str, str], "VisualAuditChecklistResult"]
PreflightRequestHandler = Callable[[str, str, str], "VisualPreflightResult"]
DiagnosticBundleRequestHandler = Callable[[str, str, str, str, str | None], VisualDiagnosticBundleResult]

APP_TITLE = "TraceAI Control — Modul Trasabilitate"


@dataclass(frozen=True)
class VisualAuditChecklistResult:
    """Stable status returned when the visual UI asks for audit checklist data."""

    success: bool
    view_model: AuditChecklistUiViewModel | None
    message: str
    error: str | None = None


@dataclass(frozen=True)
class VisualPreflightResult:
    """Stable status returned when the visual UI asks for source preflight."""

    success: bool
    report: PreflightReport | None
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


def submit_visual_form_values_async(
    source_directory: str,
    code: str,
    lot: str,
    output_docx_path: str,
    executor: Executor,
    request_handler: VisualRequestHandler = generate_report_from_ui_request,
) -> Future[UiGenerationResult]:
    """Submit DOCX generation on a background executor."""

    return executor.submit(
        submit_visual_form_values,
        source_directory,
        code,
        lot,
        output_docx_path,
        request_handler,
    )


def validate_audit_checklist_form_values(source_directory: str, code: str, lot: str) -> str | None:
    """Validate only UI fields needed for audit checklist preview/preflight."""

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


def submit_preflight_form_values(source_directory: str, code: str, lot: str) -> VisualPreflightResult:
    """Build the source preflight report from visual form values."""

    validation_error = validate_audit_checklist_form_values(source_directory, code, lot)
    if validation_error:
        return VisualPreflightResult(
            success=False,
            report=None,
            message="Date UI incomplete pentru verificarea surselor.",
            error=validation_error,
        )

    try:
        report = build_preflight_report(source_directory, code, lot)
    except Exception as exc:  # pragma: no cover - exact exception belongs to core/source layer
        return VisualPreflightResult(
            success=False,
            report=None,
            message="Eroare la verificarea surselor.",
            error=str(exc),
        )

    return VisualPreflightResult(
        success=True,
        report=report,
        message=f"Verificare surse finalizată: {report.status}.",
        error=None,
    )


def submit_preflight_form_values_async(
    source_directory: str,
    code: str,
    lot: str,
    executor: Executor,
    preflight_request_handler: PreflightRequestHandler = submit_preflight_form_values,
) -> Future[VisualPreflightResult]:
    """Submit source preflight on a background executor."""

    return executor.submit(preflight_request_handler, source_directory, code, lot)


def submit_audit_checklist_form_values(
    source_directory: str,
    code: str,
    lot: str,
    payload_builder: AuditChecklistPayloadBuilder | None = None,
    view_model_builder: AuditChecklistViewModelBuilder = build_audit_checklist_ui_view_model,
) -> VisualAuditChecklistResult:
    """Build the audit checklist view model from visual form values."""

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


def submit_audit_checklist_form_values_async(
    source_directory: str,
    code: str,
    lot: str,
    executor: Executor,
    audit_request_handler: AuditChecklistRequestHandler = submit_audit_checklist_form_values,
) -> Future[VisualAuditChecklistResult]:
    """Submit audit checklist preview generation on a background executor."""

    return executor.submit(audit_request_handler, source_directory, code, lot)


def default_audit_checklist_payload_builder(source_directory: str, code: str, lot: str) -> dict[str, Any]:
    """Import the payload builder lazily to keep runnable UI modules isolated."""

    from src.ui.audit_checklist_json import build_audit_checklist_ui_payload

    return build_audit_checklist_ui_payload(source_directory, code, lot)


def write_selected_section_tsv(display_model: SectionDisplayModel, output_path: str | Path) -> Path:
    """Write the selected section display model as TSV for external use."""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(export_section_display_as_tsv(display_model), encoding="utf-8")
    return output


def format_audit_checklist_preview(view_model: AuditChecklistUiViewModel, max_rows_per_section: int = 3) -> str:
    """Format a compact text preview from the audit checklist view model."""

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


def format_section_display_text(display_model: SectionDisplayModel) -> str:
    """Format a selected-section display model for text fallback/export."""

    lines = [display_model.title]
    if display_model.description:
        lines.append(display_model.description)
    if display_model.summary:
        lines.append(display_model.summary)
    if display_model.kind == "details":
        for key, value in display_model.detail_pairs:
            lines.append(f"- {key}: {value}")
    elif display_model.kind == "table":
        if display_model.table_columns:
            lines.append(" | ".join(display_model.table_columns))
        for row in display_model.table_rows:
            lines.append(" | ".join(row))
    else:
        lines.append(display_model.empty_message)
    return "\n".join(lines).rstrip() + "\n"


def run_visual_app(
    request_handler: VisualRequestHandler = generate_report_from_ui_request,
    audit_request_handler: AuditChecklistRequestHandler = submit_audit_checklist_form_values,
    preflight_request_handler: PreflightRequestHandler = submit_preflight_form_values,
    diagnostic_request_handler: DiagnosticBundleRequestHandler = submit_diagnostic_bundle_form_values,
) -> int:
    """Run the minimal Tkinter visual shell."""

    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry("1120x800")
    root.minsize(980, 720)

    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="traceai-ui-worker")
    busy = False
    current_view_model: AuditChecklistUiViewModel | None = None
    current_display_model: SectionDisplayModel | None = None
    section_by_tree_id: dict[str, str] = {}
    build_info_line = format_build_info_line()

    main_frame = ttk.Frame(root, padding=18)
    main_frame.grid(row=0, column=0, sticky="nsew")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    main_frame.columnconfigure(1, weight=1)
    main_frame.rowconfigure(9, weight=1)

    ttk.Label(main_frame, text="TraceAI Control — audit checklist și raport DOCX", font=("Segoe UI", 14, "bold")).grid(
        row=0, column=0, columnspan=3, sticky="w", pady=(0, 14)
    )

    source_var = tk.StringVar()
    code_var = tk.StringVar()
    lot_var = tk.StringVar()
    output_var = tk.StringVar()
    diagnostic_zip_var = tk.StringVar()
    status_var = tk.StringVar(value="Completați câmpurile, verificați sursele și generați raportul.")
    build_info_var = tk.StringVar(value=build_info_line)
    section_title_var = tk.StringVar(value="Nicio secțiune selectată")
    section_summary_var = tk.StringVar(value="Verificați sursele sau generați previzualizarea audit checklist.")

    def choose_source_directory() -> None:
        selected = filedialog.askdirectory(title="Alege folderul cu sursele oficiale")
        if selected:
            source_var.set(selected)
            if not diagnostic_zip_var.get().strip():
                diagnostic_zip_var.set(suggest_diagnostic_zip_path(selected, code_var.get() or "cod", lot_var.get() or "lot"))

    def choose_output_file() -> None:
        selected = filedialog.asksaveasfilename(
            title="Alege raportul DOCX generat",
            defaultextension=".docx",
            filetypes=[("Word document", "*.docx"), ("All files", "*.*")],
        )
        if selected:
            output_var.set(selected)

    def choose_diagnostic_zip_file() -> None:
        initial_dir = source_var.get().strip() or str(Path.cwd())
        initial_file = Path(suggest_diagnostic_zip_path(initial_dir, code_var.get() or "cod", lot_var.get() or "lot")).name
        selected = filedialog.asksaveasfilename(
            title="Alege diagnosticul ZIP generat",
            defaultextension=".zip",
            initialfile=initial_file,
            filetypes=[("ZIP archive", "*.zip"), ("All files", "*.*")],
        )
        if selected:
            diagnostic_zip_var.set(selected)

    def set_preview_text(text: str) -> None:
        section_text.configure(state="normal")
        section_text.delete("1.0", tk.END)
        section_text.insert("1.0", text)
        section_text.configure(state="disabled")

    def clear_table() -> None:
        section_table.delete(*section_table.get_children())
        section_table["columns"] = ()
        section_table["show"] = "headings"

    def clear_sections() -> None:
        nonlocal current_view_model, current_display_model
        current_view_model = None
        current_display_model = None
        section_by_tree_id.clear()
        section_tree.delete(*section_tree.get_children())
        clear_table()

    def render_section_display(display_model: SectionDisplayModel) -> None:
        nonlocal current_display_model
        current_display_model = display_model
        section_title_var.set(display_model.title)
        section_summary_var.set(display_model.summary or display_model.empty_message)
        set_preview_text(format_section_display_text(display_model))
        clear_table()
        if display_model.kind != "table" or not display_model.table_columns:
            return
        section_table["columns"] = display_model.table_columns
        for column in display_model.table_columns:
            section_table.heading(column, text=column)
            section_table.column(column, width=140, minwidth=80, stretch=True)
        for row in display_model.table_rows:
            section_table.insert("", "end", values=row)

    def load_sections(view_model: AuditChecklistUiViewModel) -> None:
        nonlocal current_view_model
        current_view_model = view_model
        section_by_tree_id.clear()
        section_tree.delete(*section_tree.get_children())
        for item in build_section_list_items(view_model):
            tree_id = section_tree.insert("", "end", text=item.label, values=(item.kind,))
            section_by_tree_id[tree_id] = item.key
        first_item = section_tree.get_children()[0] if section_tree.get_children() else None
        if first_item:
            section_tree.selection_set(first_item)
            section_tree.focus(first_item)
            render_selected_section()

    def render_selected_section(_event: object | None = None) -> None:
        if current_view_model is None:
            return
        selected = section_tree.selection()
        if not selected:
            return
        section_key = section_by_tree_id.get(selected[0])
        if not section_key:
            return
        section = find_section_by_key(current_view_model, section_key)
        if section is None:
            return
        render_section_display(build_section_display_model(section))

    def require_selected_section() -> SectionDisplayModel | None:
        if current_display_model is None:
            messagebox.showwarning(APP_TITLE, "Nu există secțiune selectată pentru copiere/export.")
            return None
        return current_display_model

    def on_copy_section_text() -> None:
        display_model = require_selected_section()
        if display_model is None:
            return
        root.clipboard_clear()
        root.clipboard_append(export_section_display_as_text(display_model))
        status_var.set("Secțiunea selectată a fost copiată în clipboard ca text.")

    def on_copy_section_tsv() -> None:
        display_model = require_selected_section()
        if display_model is None:
            return
        root.clipboard_clear()
        root.clipboard_append(export_section_display_as_tsv(display_model))
        status_var.set("Secțiunea selectată a fost copiată în clipboard ca TSV.")

    def on_export_section_tsv() -> None:
        display_model = require_selected_section()
        if display_model is None:
            return
        selected = filedialog.asksaveasfilename(
            title="Exportă secțiunea selectată ca TSV",
            defaultextension=".tsv",
            filetypes=[("TSV", "*.tsv"), ("Text", "*.txt"), ("All files", "*.*")],
        )
        if not selected:
            return
        output_path = write_selected_section_tsv(display_model, selected)
        status_var.set(f"Secțiunea selectată a fost exportată: {output_path}")
        messagebox.showinfo(APP_TITLE, f"Export finalizat: {output_path}")

    def set_busy(is_busy: bool, message: str | None = None) -> None:
        nonlocal busy
        busy = is_busy
        state = "disabled" if is_busy else "normal"
        preflight_button.configure(state=state)
        generate_button.configure(state=state)
        preview_button.configure(state=state)
        diagnostic_button.configure(state=state)
        if message:
            status_var.set(message)
        root.update_idletasks()

    def poll_docx_generation(future: Future[UiGenerationResult]) -> None:
        if not future.done():
            root.after(100, poll_docx_generation, future)
            return
        set_busy(False)
        try:
            result = future.result()
        except Exception as exc:  # pragma: no cover
            status_var.set(str(exc))
            messagebox.showerror(APP_TITLE, str(exc))
            return
        status_var.set(result.message if result.success else result.error or result.message)
        if result.success:
            messagebox.showinfo(APP_TITLE, f"{result.message}\n\n{build_info_line}")
        else:
            messagebox.showerror(APP_TITLE, result.error or result.message)

    def poll_diagnostic_bundle(future: Future[VisualDiagnosticBundleResult]) -> None:
        if not future.done():
            root.after(100, poll_diagnostic_bundle, future)
            return
        set_busy(False)
        try:
            result = future.result()
        except Exception as exc:  # pragma: no cover
            status_var.set(str(exc))
            set_preview_text(str(exc))
            messagebox.showerror(APP_TITLE, str(exc))
            return
        status_var.set(result.message if result.success else result.error or result.message)
        section_title_var.set("Diagnostic ZIP local")
        if result.success:
            message = f"{result.message}\n\nPath: {result.output_zip_path or ''}\n"
            section_summary_var.set("Diagnostic ZIP generat cu succes.")
            set_preview_text(message)
            messagebox.showinfo(APP_TITLE, result.message)
        else:
            section_summary_var.set("Diagnostic ZIP nu a fost generat.")
            set_preview_text(result.error or result.message)
            messagebox.showerror(APP_TITLE, result.error or result.message)

    def poll_preflight(future: Future[VisualPreflightResult]) -> None:
        if not future.done():
            root.after(100, poll_preflight, future)
            return
        set_busy(False)
        clear_sections()
        try:
            result = future.result()
        except Exception as exc:  # pragma: no cover
            status_var.set(str(exc))
            set_preview_text(str(exc))
            messagebox.showerror(APP_TITLE, str(exc))
            return
        status_var.set(result.message if result.success else result.error or result.message)
        section_title_var.set("Verificare surse înainte de generare")
        if result.success and result.report is not None:
            section_summary_var.set(f"Status preflight: {result.report.status}")
            set_preview_text(format_preflight_report(result.report))
            if result.report.status == "BLOCKER":
                messagebox.showwarning(APP_TITLE, "Preflight a găsit blocaje. Verificați detaliile înainte de generare.")
        else:
            section_summary_var.set("Verificarea surselor nu a reușit.")
            set_preview_text(result.error or result.message)
            messagebox.showerror(APP_TITLE, result.error or result.message)

    def poll_audit_preview(future: Future[VisualAuditChecklistResult]) -> None:
        if not future.done():
            root.after(100, poll_audit_preview, future)
            return
        set_busy(False)
        try:
            result = future.result()
        except Exception as exc:  # pragma: no cover
            status_var.set(str(exc))
            set_preview_text(str(exc))
            clear_table()
            messagebox.showerror(APP_TITLE, str(exc))
            return
        status_var.set(result.message if result.success else result.error or result.message)
        if result.success and result.view_model is not None:
            load_sections(result.view_model)
        else:
            set_preview_text(result.error or result.message)
            clear_table()
            messagebox.showerror(APP_TITLE, result.error or result.message)

    def on_generate() -> None:
        if busy:
            return
        set_busy(True, "Generare raport DOCX în curs... aplicația rămâne disponibilă.")
        future = submit_visual_form_values_async(
            source_directory=source_var.get(),
            code=code_var.get(),
            lot=lot_var.get(),
            output_docx_path=output_var.get(),
            executor=executor,
            request_handler=request_handler,
        )
        root.after(100, poll_docx_generation, future)

    def on_generate_diagnostic_zip() -> None:
        if busy:
            return
        if not diagnostic_zip_var.get().strip():
            base_dir = source_var.get().strip() or str(Path.cwd())
            diagnostic_zip_var.set(suggest_diagnostic_zip_path(base_dir, code_var.get() or "cod", lot_var.get() or "lot"))
        set_busy(True, "Generare diagnostic ZIP în curs... aplicația rămâne disponibilă.")
        future = submit_diagnostic_bundle_form_values_async(
            source_directory=source_var.get(),
            code=code_var.get(),
            lot=lot_var.get(),
            output_zip_path=diagnostic_zip_var.get(),
            generated_report_path=output_var.get() or None,
            executor=executor,
            request_handler=diagnostic_request_handler,
        )
        root.after(100, poll_diagnostic_bundle, future)

    def on_preflight() -> None:
        if busy:
            return
        set_busy(True, "Verificare surse în curs...")
        future = submit_preflight_form_values_async(
            source_directory=source_var.get(),
            code=code_var.get(),
            lot=lot_var.get(),
            executor=executor,
            preflight_request_handler=preflight_request_handler,
        )
        root.after(100, poll_preflight, future)

    def on_preview_audit() -> None:
        if busy:
            return
        set_busy(True, "Generare previzualizare audit checklist în curs...")
        future = submit_audit_checklist_form_values_async(
            source_directory=source_var.get(),
            code=code_var.get(),
            lot=lot_var.get(),
            executor=executor,
            audit_request_handler=audit_request_handler,
        )
        root.after(100, poll_audit_preview, future)

    def on_close() -> None:
        executor.shutdown(wait=False, cancel_futures=True)
        root.destroy()

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

    ttk.Label(main_frame, text="Diagnostic ZIP output").grid(row=5, column=0, sticky="w", pady=4)
    ttk.Entry(main_frame, textvariable=diagnostic_zip_var).grid(row=5, column=1, sticky="ew", pady=4, padx=(8, 8))
    ttk.Button(main_frame, text="Alege...", command=choose_diagnostic_zip_file).grid(row=5, column=2, sticky="ew", pady=4)

    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=6, column=1, columnspan=2, sticky="e", pady=(16, 8))
    preflight_button = ttk.Button(button_frame, text="Verifică surse", command=on_preflight)
    preflight_button.grid(row=0, column=0, padx=(0, 8))
    preview_button = ttk.Button(button_frame, text="Previzualizează audit checklist", command=on_preview_audit)
    preview_button.grid(row=0, column=1, padx=(0, 8))
    diagnostic_button = ttk.Button(button_frame, text="Generează Diagnostic ZIP", command=on_generate_diagnostic_zip)
    diagnostic_button.grid(row=0, column=2, padx=(0, 8))
    generate_button = ttk.Button(button_frame, text="Generează raport DOCX", command=on_generate)
    generate_button.grid(row=0, column=3)

    ttk.Label(main_frame, textvariable=status_var, wraplength=980).grid(row=7, column=0, columnspan=3, sticky="ew", pady=(10, 2))
    ttk.Label(main_frame, textvariable=build_info_var, wraplength=980).grid(row=8, column=0, columnspan=3, sticky="ew", pady=(0, 8))

    preview_frame = ttk.LabelFrame(main_frame, text="Verificare surse / Audit checklist pe secțiuni")
    preview_frame.grid(row=9, column=0, columnspan=3, sticky="nsew")
    preview_frame.columnconfigure(1, weight=1)
    preview_frame.rowconfigure(0, weight=1)

    section_tree = ttk.Treeview(preview_frame, columns=("kind",), show="tree", selectmode="browse", height=18)
    section_tree.grid(row=0, column=0, sticky="nsw", padx=(0, 10))
    section_tree.column("#0", width=300, minwidth=220, stretch=False)
    section_tree.bind("<<TreeviewSelect>>", render_selected_section)

    detail_frame = ttk.Frame(preview_frame)
    detail_frame.grid(row=0, column=1, sticky="nsew")
    detail_frame.columnconfigure(0, weight=1)
    detail_frame.rowconfigure(4, weight=1)

    ttk.Label(detail_frame, textvariable=section_title_var, font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w")
    ttk.Label(detail_frame, textvariable=section_summary_var, wraplength=720).grid(row=1, column=0, sticky="ew", pady=(4, 8))

    export_frame = ttk.Frame(detail_frame)
    export_frame.grid(row=2, column=0, sticky="e", pady=(0, 8))
    ttk.Button(export_frame, text="Copiază text", command=on_copy_section_text).grid(row=0, column=0, padx=(0, 6))
    ttk.Button(export_frame, text="Copiază TSV", command=on_copy_section_tsv).grid(row=0, column=1, padx=(0, 6))
    ttk.Button(export_frame, text="Exportă TSV...", command=on_export_section_tsv).grid(row=0, column=2)

    section_text = tk.Text(detail_frame, wrap="word", height=8)
    section_text.grid(row=3, column=0, sticky="ew")
    section_text.configure(state="disabled")

    table_frame = ttk.Frame(detail_frame)
    table_frame.grid(row=4, column=0, sticky="nsew", pady=(8, 0))
    table_frame.columnconfigure(0, weight=1)
    table_frame.rowconfigure(0, weight=1)
    section_table = ttk.Treeview(table_frame, show="headings")
    section_table.grid(row=0, column=0, sticky="nsew")
    table_scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=section_table.yview)
    table_scrollbar_y.grid(row=0, column=1, sticky="ns")
    table_scrollbar_x = ttk.Scrollbar(table_frame, orient="horizontal", command=section_table.xview)
    table_scrollbar_x.grid(row=1, column=0, sticky="ew")
    section_table.configure(yscrollcommand=table_scrollbar_y.set, xscrollcommand=table_scrollbar_x.set)

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
    return 0


def main() -> int:
    """Entry point for the minimal visual UI shell."""

    return run_visual_app()


if __name__ == "__main__":
    raise SystemExit(main())
