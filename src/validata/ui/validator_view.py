"""Structural Validator workspace; file processing is intentionally unavailable."""

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
        source.grid(row=1, column=0, sticky="ew", padx=18, pady=8)
        source.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(source, text="Select files or folders — unavailable", state="disabled").grid(
            row=0, column=0, padx=12, pady=12
        )
        ctk.CTkLabel(
            source,
            text="File selection and validation are planned for a later milestone.",
            anchor="w",
            justify="left",
            wraplength=620,
        ).grid(row=0, column=1, sticky="ew", padx=12, pady=12)

        ctk.CTkLabel(self, text="Default profile: Balanced", anchor="w").grid(
            row=2, column=0, sticky="ew", padx=20, pady=(4, 8)
        )
        self.results = ResultsTable(self, self.COLUMNS, height=14)
        self.results.grid(row=3, column=0, sticky="nsew", padx=18, pady=6)
        ctk.CTkLabel(
            self,
            text="Results will appear here after validation is implemented. No files are being processed.",
            anchor="w",
            text_color=("gray35", "gray70"),
        ).grid(row=4, column=0, sticky="ew", padx=20, pady=(4, 16))
