"""Validator source selection and progressive results workspace."""

import tkinter as tk
import customtkinter as ctk

from .results_table import ResultsTable


class ValidatorView(ctk.CTkFrame):
    COLUMNS = (
        ("filename", "Filename", 220),
        ("location", "Location", 300),
        ("file_type", "File type", 110),
        ("profile", "Profile", 100),
        ("status", "Status", 150),
        ("details", "Details", 260),
    )

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        ctk.CTkLabel(self, text="Validator", font=ctk.CTkFont(size=23, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=18, pady=(16, 8)
        )

        source = ctk.CTkFrame(self)
        source.grid(row=1, column=0, sticky="ew", padx=18, pady=6)
        source.grid_columnconfigure(0, weight=1)
        self.source_list = tk.Listbox(source, height=3, selectmode=tk.EXTENDED, exportselection=False)
        scrollbar = tk.Scrollbar(source, orient="vertical", command=self.source_list.yview)
        self.source_list.configure(yscrollcommand=scrollbar.set)
        self.source_list.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(10, 0), pady=10)
        scrollbar.grid(row=0, column=1, rowspan=2, sticky="ns", pady=10)
        buttons = ctk.CTkFrame(source, fg_color="transparent")
        buttons.grid(row=0, column=2, rowspan=2, sticky="ns", padx=10, pady=8)
        self.add_files_button = ctk.CTkButton(buttons, text="Add Files", command=lambda: None)
        self.add_folder_button = ctk.CTkButton(buttons, text="Add Folder", command=lambda: None)
        self.remove_button = ctk.CTkButton(buttons, text="Remove Selected", command=lambda: None)
        self.clear_button = ctk.CTkButton(buttons, text="Clear Sources", command=lambda: None)
        self.start_button = ctk.CTkButton(buttons, text="Start", command=lambda: None, state="disabled")
        self.cancel_button = ctk.CTkButton(buttons, text="Cancel", command=lambda: None, state="disabled")
        for row, button in enumerate((self.add_files_button, self.add_folder_button,
                                      self.remove_button, self.clear_button,
                                      self.start_button, self.cancel_button)):
            button.grid(row=row, column=0, sticky="ew", pady=2)

        self.status_label = ctk.CTkLabel(
            self, text="No sources selected. Integrity checks are not implemented.",
            anchor="w", justify="left", wraplength=1000,
        )
        self.status_label.grid(row=2, column=0, sticky="ew", padx=20, pady=6)
        self.results = ResultsTable(self, self.COLUMNS, height=14)
        self.results.grid(row=3, column=0, sticky="nsew", padx=18, pady=6)
        ctk.CTkLabel(
            self, text="This milestone discovers files only; no file-integrity validation is performed.",
            anchor="w", text_color=("gray35", "gray70"),
        ).grid(row=4, column=0, sticky="ew", padx=20, pady=(4, 16))

    def set_active(self, active: bool) -> None:
        state = "disabled" if active else "normal"
        for button in (self.add_files_button, self.add_folder_button,
                       self.remove_button, self.clear_button, self.start_button):
            button.configure(state=state)
        self.cancel_button.configure(state="normal" if active else "disabled")
