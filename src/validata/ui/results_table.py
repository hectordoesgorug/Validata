"""Reusable, main-thread-only ttk results table."""

from __future__ import annotations

from threading import get_ident
from tkinter import ttk
from uuid import uuid4


_STATUS_COLORS = {
    "valid": ("#e7f4e4", "#153d18"),
    "corrupted": ("#f9e3e3", "#6b1111"),
    "incomplete": ("#fff2d5", "#553900"),
    "unsupported": ("#fff2d5", "#553900"),
    "encrypted": ("#fff2d5", "#553900"),
    "validation-error": ("#fff2d5", "#553900"),
    "skipped": ("#fff2d5", "#553900"),
    "warning": ("#fff2d5", "#553900"),
}


class ResultsTable(ttk.Frame):
    def __init__(self, master, columns: tuple[tuple[str, str, int], ...], *, height: int = 12):
        super().__init__(master)
        self._owner_thread = get_ident()
        self._column_ids = tuple(column[0] for column in columns)
        self.tree = ttk.Treeview(
            self,
            columns=self._column_ids,
            show="headings",
            height=height,
            selectmode="browse",
        )
        self.vertical_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.horizontal_scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(
            yscrollcommand=self.vertical_scrollbar.set,
            xscrollcommand=self.horizontal_scrollbar.set,
        )

        for column_id, heading, width in columns:
            self.tree.heading(column_id, text=heading, anchor="w")
            self.tree.column(column_id, width=width, minwidth=70, stretch=True, anchor="w")

        for tag, (background, foreground) in _STATUS_COLORS.items():
            self.tree.tag_configure(tag, background=background, foreground=foreground)

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.vertical_scrollbar.grid(row=0, column=1, sticky="ns")
        self.horizontal_scrollbar.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def insert_row(self, values: tuple[object, ...], *, row_id: str | None = None, status: str | None = None) -> str:
        self._assert_main_thread()
        if len(values) != len(self._column_ids):
            raise ValueError("row value count must match the configured columns")
        identifier = row_id or f"row-{uuid4().hex}"
        tags = (status,) if status in _STATUS_COLORS else ()
        self.tree.insert("", "end", iid=identifier, values=values, tags=tags)
        return identifier

    def update_row(
        self,
        row_id: str,
        *,
        values: tuple[object, ...] | None = None,
        status: str | None = None,
    ) -> None:
        self._assert_main_thread()
        if values is not None and len(values) != len(self._column_ids):
            raise ValueError("row value count must match the configured columns")
        options = {}
        if values is not None:
            options["values"] = values
        if status is not None:
            options["tags"] = (status,) if status in _STATUS_COLORS else ()
        self.tree.item(row_id, **options)

    def remove_row(self, row_id: str) -> None:
        self._assert_main_thread()
        self.tree.delete(row_id)

    def clear(self) -> None:
        self._assert_main_thread()
        self.tree.delete(*self.tree.get_children())

    def _assert_main_thread(self) -> None:
        if get_ident() != self._owner_thread:
            raise RuntimeError("results table may only be accessed on its creating thread")
