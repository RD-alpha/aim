from __future__ import annotations

import ast
import json
import pickle
from pathlib import Path
from typing import Any

from IPython.display import display
from ipywidgets import (
    Button,
    Dropdown,
    HBox,
    HTML,
    Layout,
    Output,
    Text,
    Textarea,
    VBox,
)
from rdkit import Chem
from rdkit.Chem import Draw


VALID_ROOTS = ["finetuning_combined"]


def _load_record(folder: Path) -> tuple[Chem.Mol, dict[str, Any]]:
    with (folder / "sm.pkl").open("rb") as f:
        mol = pickle.load(f)
    with (folder / "data.json").open() as f:
        data = json.load(f)
    return mol, data


def _draw_molecule(mol: Chem.Mol):
    options = Draw.rdMolDraw2D.MolDrawOptions()
    options.addAtomIndices = True
    return Draw.MolToImage(mol, size=(900, 600), options=options)


def _mechanism_key(mechanism: list[Any]) -> str:
    return repr(mechanism)


def _format_mechanisms(data: dict[str, Any], probable_value: int) -> str:
    choices = data.get("choices", {})
    selected = [
        choice["mechanism"]
        for _, choice in sorted(choices.items(), key=lambda item: int(item[0]))
        if choice.get("probable") == probable_value
    ]
    return "\n".join(repr(mech) for mech in selected)


def _parse_mechanism_text(text: str) -> list[list[Any]]:
    mechanisms: list[list[Any]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        value = ast.literal_eval(line)
        if not isinstance(value, list) or len(value) != 5:
            raise ValueError(f"Mechanism must be a 5-item list: {line}")
        mechanisms.append(value)
    return mechanisms


def _all_choice_lines(data: dict[str, Any]) -> str:
    lines = []
    for key, choice in sorted(data.get("choices", {}).items(), key=lambda item: int(item[0])):
        lines.append(f"{key}: probable={choice.get('probable')} mechanism={choice.get('mechanism')}")
    return "\n".join(lines)


def _folder_options(root: Path) -> list[str]:
    return sorted([p.name for p in root.iterdir() if p.is_dir()])


def _next_choice_key(choices: dict[str, Any]) -> str:
    if not choices:
        return "0"
    return str(max(int(key) for key in choices) + 1)


def make_finetuning_labeler(default_root: str = "finetuning_combined"):
    root_dropdown = Dropdown(
        options=VALID_ROOTS,
        value=default_root if default_root in VALID_ROOTS else VALID_ROOTS[0],
        description="Root:",
    )
    folder_dropdown = Dropdown(description="Folder:", layout=Layout(width="220px"))
    goto_text = Text(description="Go to:", layout=Layout(width="180px"))
    prev_button = Button(description="Previous")
    next_button = Button(description="Next")
    reload_button = Button(description="Reload")
    save_button = Button(description="Save", button_style="success")

    contributor_text = Text(description="Contributor:", layout=Layout(width="500px"))
    good_box = Textarea(
        description="Good",
        layout=Layout(width="48%", height="240px"),
        placeholder="One mechanism list per line",
    )
    bad_box = Textarea(
        description="Bad",
        layout=Layout(width="48%", height="240px"),
        placeholder="One mechanism list per line",
    )
    choices_box = Textarea(
        description="Choices",
        layout=Layout(width="100%", height="240px"),
        disabled=True,
    )
    summary_html = HTML()
    status_html = HTML()
    mol_output = Output()

    state: dict[str, Any] = {"folder_names": []}

    def current_root() -> Path:
        return Path(root_dropdown.value)

    def refresh_folder_options(selected: str | None = None) -> None:
        names = _folder_options(current_root())
        state["folder_names"] = names
        folder_dropdown.options = names
        if not names:
            folder_dropdown.value = None
            return
        if selected in names:
            folder_dropdown.value = selected
        elif folder_dropdown.value in names:
            return
        else:
            folder_dropdown.value = names[0]

    def render_current() -> None:
        if not folder_dropdown.value:
            summary_html.value = "<b>No folders found.</b>"
            return

        folder = current_root() / folder_dropdown.value
        mol, data = _load_record(folder)
        contributor_text.value = data.get("contributor", "") or ""
        good_box.value = _format_mechanisms(data, 1)
        bad_box.value = _format_mechanisms(data, 0)
        choices_box.value = _all_choice_lines(data)

        choices = data.get("choices", {})
        good_count = sum(1 for choice in choices.values() if choice.get("probable") == 1)
        bad_count = sum(1 for choice in choices.values() if choice.get("probable") == 0)
        unlabelled_count = sum(1 for choice in choices.values() if choice.get("probable") is None)
        summary_html.value = (
            f"<b>{folder}</b><br>"
            f"choices: {len(choices)} | good: {good_count} | bad: {bad_count} | unlabelled: {unlabelled_count}"
        )

        with mol_output:
            mol_output.clear_output(wait=True)
            display(_draw_molecule(mol))

        status_html.value = ""

    def set_folder_by_offset(offset: int) -> None:
        names = state["folder_names"]
        if not names or folder_dropdown.value is None:
            return
        idx = names.index(folder_dropdown.value)
        new_idx = min(max(0, idx + offset), len(names) - 1)
        folder_dropdown.value = names[new_idx]

    def save_current(_=None) -> None:
        if not folder_dropdown.value:
            return

        folder = current_root() / folder_dropdown.value
        _, data = _load_record(folder)
        choices = data.setdefault("choices", {})

        try:
            good_mechanisms = _parse_mechanism_text(good_box.value)
            bad_mechanisms = _parse_mechanism_text(bad_box.value)
        except Exception as exc:
            status_html.value = f"<span style='color:red'><b>Parse error:</b> {exc}</span>"
            return

        good_keys = {_mechanism_key(mech) for mech in good_mechanisms}
        bad_keys = {_mechanism_key(mech) for mech in bad_mechanisms}
        overlap = sorted(good_keys & bad_keys)
        if overlap:
            status_html.value = (
                "<span style='color:red'><b>Error:</b> the same mechanism appears in both Good and Bad.</span>"
            )
            return

        existing_by_mech = {
            _mechanism_key(choice["mechanism"]): key for key, choice in choices.items()
        }

        for choice in choices.values():
            choice["probable"] = None

        for mech in good_mechanisms:
            mech_key = _mechanism_key(mech)
            if mech_key in existing_by_mech:
                choices[existing_by_mech[mech_key]]["probable"] = 1
            else:
                new_key = _next_choice_key(choices)
                choices[new_key] = {"mechanism": mech, "probable": 1}
                existing_by_mech[mech_key] = new_key

        for mech in bad_mechanisms:
            mech_key = _mechanism_key(mech)
            if mech_key in existing_by_mech:
                choices[existing_by_mech[mech_key]]["probable"] = 0
            else:
                new_key = _next_choice_key(choices)
                choices[new_key] = {"mechanism": mech, "probable": 0}
                existing_by_mech[mech_key] = new_key

        data["contributor"] = contributor_text.value
        with (folder / "data.json").open("w") as f:
            json.dump(data, f)

        status_html.value = "<span style='color:green'><b>Saved.</b></span>"
        render_current()

    def on_root_change(change):
        if change["name"] == "value":
            refresh_folder_options()
            render_current()

    def on_folder_change(change):
        if change["name"] == "value" and change["new"] is not None:
            render_current()

    def on_goto_submit(_):
        target = goto_text.value.strip()
        if target and target in state["folder_names"]:
            folder_dropdown.value = target
        elif target:
            status_html.value = f"<span style='color:red'><b>Folder not found:</b> {target}</span>"

    root_dropdown.observe(on_root_change)
    folder_dropdown.observe(on_folder_change)
    goto_text.on_submit(on_goto_submit)
    prev_button.on_click(lambda _: set_folder_by_offset(-1))
    next_button.on_click(lambda _: set_folder_by_offset(1))
    reload_button.on_click(lambda _: render_current())
    save_button.on_click(save_current)

    refresh_folder_options()
    render_current()

    controls = HBox([root_dropdown, folder_dropdown, goto_text, prev_button, next_button, reload_button, save_button])
    editors = HBox([good_box, bad_box])
    return VBox([controls, contributor_text, summary_html, mol_output, editors, choices_box, status_html])


__all__ = ["make_finetuning_labeler"]
