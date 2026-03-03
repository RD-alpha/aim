#!/usr/bin/env python3
from __future__ import annotations

from IPython.display import display, Image as IPyImage
from ipywidgets import Button, Output, VBox, HBox, HTML
from rdkit import Chem
from rdkit.Chem import Draw
import os
import pickle


def _visualise_tree(node):
    mols = [Chem.MolFromSmiles(node.smiles)]
    while not node.is_root:
        node = node.parent
        mols.append(Chem.MolFromSmiles(node.smiles))
    mols.reverse()
    return Draw.MolsToGridImage(
        mols,
        molsPerRow=3,
        subImgSize=(400, 400),
        legends=[f"Mol {i}" for i in range(len(mols))],
    )


def _get_node_from_slurm(slurm_id):
    node = None
    for path in [
        f"old_slurm/slurm-{slurm_id}.out",
        f"slurm_out/slurm-{slurm_id}.out",
        f"slurm-{slurm_id}.out",
    ]:
        try:
            with open(path, "r") as f:
                lines = f.readlines()
            for line in lines:
                if "Running on master node:" in line:
                    node = line.split(":")[-1].split(".")[0].strip()
                    return node
        except Exception:
            continue
    return None


def _load_and_visualize_tree(slurm_id, node_dir_root="/nodescratch", save_dir="./images"):
    node = _get_node_from_slurm(slurm_id)
    if node is None:
        raise RuntimeError(f"Could not find slurm output for {slurm_id}")

    node_dir = os.path.join(node_dir_root, node, "rd611", str(slurm_id))
    os.makedirs(save_dir, exist_ok=True)

    if not os.path.isdir(node_dir):
        raise RuntimeError(f"Node directory not found: {node_dir}")

    files = os.listdir(node_dir)
    if len(files) == 1:
        filename = files[0]
        pickle_path = os.path.join(node_dir, filename)
        with open(pickle_path, "rb") as file:
            node = pickle.load(file)
        image = _visualise_tree(node)
        image_path = os.path.join(save_dir, f"{slurm_id}.png")
        image.save(image_path)
        return [image_path]

    out_paths = []
    for filename in files:
        if filename.startswith(str(slurm_id)) and filename.endswith(".pkl"):
            parts = filename.split(".")[0].split("_")[1:]
            suffix = "_".join(parts) if parts else ""
            pickle_path = os.path.join(node_dir, filename)
            with open(pickle_path, "rb") as file:
                node = pickle.load(file)
            image = _visualise_tree(node)
            image_path = os.path.join(save_dir, f"{slurm_id}_{suffix}.png")
            image.save(image_path)
            out_paths.append(image_path)
    return out_paths


def make_success_viewer(success_slurm_ids, node_dir_root="/nodescratch", save_dir="./images"):
    current_idx = {"value": 0}
    output_display = Output()
    status = HTML()

    def show_success(idx):
        with output_display:
            output_display.clear_output()
            if idx >= len(success_slurm_ids):
                print("No more reactions to review")
                return

            slurm_id = success_slurm_ids[idx]
            status.value = f"<b>Success {idx + 1}/{len(success_slurm_ids)}</b> (SLURM {slurm_id})"
            try:
                image_paths = _load_and_visualize_tree(
                    slurm_id, node_dir_root=node_dir_root, save_dir=save_dir
                )
            except Exception as e:
                print(f"Failed to visualize {slurm_id}: {e}")
                return

            for image_path in image_paths:
                display(HTML(f"<div>{os.path.basename(image_path)}</div>"))
                display(IPyImage(filename=image_path))

    def on_next(_):
        current_idx["value"] += 1
        show_success(current_idx["value"])

    def on_prev(_):
        current_idx["value"] = max(0, current_idx["value"] - 1)
        show_success(current_idx["value"])

    prev_btn = Button(description="Previous")
    next_btn = Button(description="Next")
    prev_btn.on_click(on_prev)
    next_btn.on_click(on_next)

    show_success(0)
    return VBox([status, output_display, HBox([prev_btn, next_btn])])


__all__ = ["make_success_viewer"]
