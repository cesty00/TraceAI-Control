"""Minimal visual UI shell for TraceAI Control.

The visual UI is intentionally thin. It collects the same four fields as the CLI,
builds a UiGenerationRequest, calls the UI orchestrator, and displays the
returned status.

It does not read operational source files directly and does not contain business
logic.
"""

from __future__ import annotations

from collections.abc import Callable

from src.ui.orchestrator import UiGenerationRequest, UiGenerationResult, generate_report_from_ui_request

VisualRequestHandler = Callable[[UiGenerationRequest], UiGenerationResult]

APP_TITLE = "TraceAI Control — Modul Trasabilitate"


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


def run_visual_app(request_handler: VisualRequestHandler = generate_report_from_ui_request) -> int:
    """Run the minimal Tkinter visual shell.

    The function imports Tkinter lazily so the module remains importable in
    headless test environments.
    """

    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry("720x320")
    root.minsize(680, 300)

    main_frame = ttk.Frame(root, padding=18)
    main_frame.grid(row=0, column=0, sticky="nsew")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    main_frame.columnconfigure(1, weight=1)

    title_label = ttk.Label(main_frame, text="Generare raport DOCX trasabilitate", font=("Segoe UI", 14, "bold"))
    title_label.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 14))

    source_var = tk.StringVar()
    code_var = tk.StringVar()
    lot_var = tk.StringVar()
    output_var = tk.StringVar()
    status_var = tk.StringVar(value="Completați câmpurile și generați raportul.")

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

    ttk.Button(main_frame, text="Generează raport DOCX", command=on_generate).grid(
        row=5, column=1, columnspan=2, sticky="e", pady=(16, 8)
    )

    status_label = ttk.Label(main_frame, textvariable=status_var, wraplength=640)
    status_label.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(10, 0))

    root.mainloop()
    return 0


def main() -> int:
    """Entry point for the minimal visual UI shell."""

    return run_visual_app()


if __name__ == "__main__":
    raise SystemExit(main())
