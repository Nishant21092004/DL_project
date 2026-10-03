#!/usr/bin/env python
"""Build and execute the synthetic OPM/OGM-GE walkthrough notebook.

Usage:
    python scripts/build_walkthrough_notebook.py

The script runs two four-epoch synthetic experiments, plots accuracy and
modality discrepancy, and computes XAI attribution for a trained checkpoint.
Temporary run artifacts are written to ``notebooks/_walkthrough_tmp/``.
"""
from __future__ import annotations

import os
import time

import nbformat as nbf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NB_PATH = os.path.join(ROOT, "notebooks", "01_walkthrough.ipynb")

MD = nbf.v4.new_markdown_cell
CODE = nbf.v4.new_code_cell


def build() -> nbf.NotebookNode:
    """Create the notebook without executing its code cells."""
    nb = nbf.v4.new_notebook()
    nb.metadata["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    nb.cells = [
        MD("""# OPM / OGM-GE walkthrough (text + image)

This CPU-oriented walkthrough demonstrates:

1. training a synthetic text/image model without modulation;
2. training the same model with OGM-GE;
3. comparing validation accuracy and modality discrepancy curves; and
4. measuring modality attribution with Integrated Gradients and gradient × input.

To reproduce the complete benchmark, run `scripts/run_synthetic_compare.sh` and
`scripts/run_seed_sweep.sh`, followed by `python scripts/make_report.py`."""),

        CODE("""%matplotlib inline
import json
import os
import sys

import matplotlib.pyplot as plt
import torch

# Resolve the package root from either balanced_mm/ or balanced_mm/notebooks/.
ROOT = os.path.abspath(os.getcwd())
if os.path.basename(ROOT) == "notebooks":
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
TMP = os.path.join(ROOT, "notebooks", "_walkthrough_tmp")
os.makedirs(TMP, exist_ok=True)

from train import main as train_main

print("root:", ROOT)
print("torch:", torch.__version__, "| cuda:", torch.cuda.is_available())"""),

        MD("""## 1. Train the baseline and OGM-GE models

Both runs use the same seed and configuration: 800 training samples, 300
validation samples, four epochs, a 64 × 64 SmallCNN image encoder, a two-layer
Transformer text encoder, and SGD with a learning rate of 0.01."""),

        CODE("""def run(modulation, out_name):
    out_dir = os.path.join(TMP, out_name)
    summary = train_main([
        "--data", "synthetic", "--image_encoder", "smallcnn", "--img_size", "64",
        "--epochs", "4", "--batch_size", "32",
        "--syn_train_n", "800", "--syn_val_n", "300",
        "--lr", "0.01", "--num_workers", "0", "--log_interval", "0", "--seed", "0",
        "--modulation", modulation, "--out_dir", out_dir,
    ])
    return out_dir, summary


dir_none, sum_none = run("none", "none")
dir_ogm, sum_ogm = run("ogm", "ogm")
print()
print(f"best val acc | none: {sum_none['best_val_acc']:.3f}   ogm: {sum_ogm['best_val_acc']:.3f}")"""),

        MD("""## 2. Accuracy and discrepancy curves

`ρ_image` is the image discrepancy ratio from Eq. 7. A value of one represents
balanced modality scores; a value above one indicates image dominance."""),

        CODE("""def hist(directory):
    with open(os.path.join(directory, "history.json")) as handle:
        return json.load(handle)


h0, h1 = hist(dir_none), hist(dir_ogm)
fig, ax = plt.subplots(1, 2, figsize=(11, 3.6))
for name, history, color in [("none", h0, "#888888"), ("OGM-GE", h1, "#d62728")]:
    xs = [row["epoch"] for row in history if "val_acc" in row]
    ys = [row["val_acc"] for row in history if "val_acc" in row]
    ax[0].plot(xs, ys, marker="o", label=name, color=color, lw=2)
    ax[1].plot(
        [row["epoch"] for row in history],
        [row["train_rho_image"] for row in history],
        marker="o", label=name, color=color, lw=2,
    )
ax[0].set_xlabel("epoch")
ax[0].set_ylabel("validation accuracy")
ax[0].set_title("Validation accuracy")
ax[0].grid(alpha=0.3)
ax[0].legend()
ax[1].axhline(1.0, ls=":", c="k", label="balanced (ρ=1)")
ax[1].set_xlabel("epoch")
ax[1].set_ylabel("ρ image")
ax[1].set_title("Image discrepancy ratio")
ax[1].grid(alpha=0.3)
ax[1].legend()
plt.tight_layout()
plt.show()"""),

        MD("""## 3. Modality attribution

The attribution analysis applies Integrated Gradients to image pixels and
gradient × input to text embeddings. Absolute attribution values are normalized
across modalities to produce modality contribution shares."""),

        CODE("""from argparse import Namespace

from bml.data import build_dataloaders
from bml.xai import modality_attribution
from train import build_model

with open(os.path.join(dir_none, "config.json")) as handle:
    cfg = Namespace(**json.load(handle))
data = build_dataloaders(cfg, out_dir=dir_none)
model = build_model(cfg, data["num_classes"], data["vocab_size"])
checkpoint = torch.load(
    os.path.join(dir_none, "best.pt"), map_location="cpu", weights_only=False
)
model.load_state_dict(checkpoint["model"])
model.eval()

inputs, labels = next(iter(data["loaders"]["val"]))
attribution = modality_attribution(model, inputs, steps=16)
print("prediction vs truth:", attribution["predicted"][:8], labels[:8].tolist())
print(
    "attribution shares:",
    {name: round(value, 3) for name, value in attribution["share"].items()},
)

fig, ax = plt.subplots(figsize=(5.2, 3.2))
modalities = list(attribution["share"])
ax.bar(
    modalities,
    [attribution["share"][name] for name in modalities],
    color=["#1f77b4", "#9467bd"],
)
ax.set_ylim(0, 1)
ax.set_ylabel("share of absolute attribution")
ax.set_title("Modality attribution")
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.show()"""),

        MD("""## Reproduction commands

- Aggregate benchmark: `python scripts/make_report.py`
- Run comparison: `python compare.py runs/syn_none runs/syn_opm runs/syn_ogm runs/syn_both`
- Custom CSV data: `python train.py --data csv --train_csv ... --modulation both`
- Tests: `python -m pytest tests`

The `--modulation` option accepts `none`, `opm`, `ogm`, or `both`. The core
implementation in `bml/modulation.py` is independent of the dataset pipeline."""),
    ]
    return nb


def execute(nb: nbf.NotebookNode) -> None:
    """Execute every code cell from the package root."""
    from nbclient import NotebookClient

    os.chdir(ROOT)
    client = NotebookClient(
        nb,
        timeout=900,
        kernel_name="python3",
        allow_errors=False,
    )
    client.execute()


def main() -> None:
    """Build, execute, and save the walkthrough notebook."""
    started = time.time()
    notebook = build()
    print("executing notebook ...")
    execute(notebook)
    os.makedirs(os.path.dirname(NB_PATH), exist_ok=True)
    nbf.write(notebook, NB_PATH)

    size = os.path.getsize(NB_PATH)
    code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
    cells_with_output = sum(bool(cell.outputs) for cell in code_cells)
    print(
        f"wrote {NB_PATH} ({size / 1e6:.2f} MB, "
        f"{cells_with_output}/{len(code_cells)} code cells with output, "
        f"{time.time() - started:.0f}s)"
    )


if __name__ == "__main__":
    main()
