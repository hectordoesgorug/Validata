"""Structural Counter workspace; sequence analysis is intentionally unavailable."""

import customtkinter as ctk

from .results_table import ResultsTable


class CounterView(ctk.CTkFrame):
    COLUMNS = (
        ("folder", "Folder", 260),
        ("pattern", "Pattern / group", 200),
        ("files", "Files", 90),
        ("expected", "Expected sequence", 180),
        ("findings", "Findings", 220),
        ("status", "Status", 140),
    )

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text="Counter", font=ctk.CTkFont(size=23, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=18, pady=(16, 8)
        )
        source = ctk.CTkFrame(self)
        source.grid(row=1, column=0, sticky="ew", padx=18, pady=8)
        source.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(source, text="Select folder — unavailable", state="disabled").grid(
            row=0, column=0, padx=12, pady=12
        )
        ctk.CTkLabel(
            source,
            text="Folder selection and sequence analysis are planned for a later milestone.",
            anchor="w",
            justify="left",
            wraplength=620,
        ).grid(row=0, column=1, sticky="ew", padx=12, pady=12)

        self.results = ResultsTable(self, self.COLUMNS, height=14)
        self.results.grid(row=2, column=0, sticky="nsew", padx=18, pady=6)
        ctk.CTkLabel(
            self,
            text="Findings will appear here after Counter is implemented. No folders are being processed.",
            anchor="w",
            text_color=("gray35", "gray70"),
        ).grid(row=3, column=0, sticky="ew", padx=20, pady=(4, 16))
