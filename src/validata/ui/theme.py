"""Small helpers for the approved CustomTkinter appearance modes."""

import customtkinter as ctk


def apply_appearance_mode(mode: str) -> None:
    if mode not in {"System", "Light", "Dark"}:
        raise ValueError(f"Unsupported appearance mode: {mode!r}")
    ctk.set_appearance_mode(mode)
