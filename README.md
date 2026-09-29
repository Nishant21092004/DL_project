# XAI-Driven Modality Bias Detection and Mitigation in Multimodal Deep Learning Models

Deep Learning semester project — see [`Project_Proposal.md`](Project_Proposal.md) for the full proposal
(PaliGemma-3B bias detection with attention analysis / Integrated Gradients, Balanced Modal Attention, bias regularization).

## Repository layout

| Path | What it is |
|---|---|
| `Project_Proposal.md` | One-page project proposal |
| `multimodal (2).ipynb` | Colab notebook: PaliGemma-3B loading, prompt/VQA demo, attention heat-map (XAI) |
| **`balanced_mm/`** | **Training-time modality-bias mitigation baseline: OPM / OGM-GE** (Wei et al., TPAMI 2024) — full PyTorch implementation for Text + Image late-fusion models, with tests, synthetic benchmark and plug-in module. See [`balanced_mm/README.md`](balanced_mm/README.md). |
| `docs/OGM_OPM_Explanation.pdf` | Hinglish notes: derivations (cross-entropy gradient, GD/SGD), why one modality dominates, OPM/OGM/GE equations, all techniques compared |
| `docs/Wei2024_On-the-fly_Modulation_TPAMI.pdf` | The reference paper (arXiv:2410.11582) |

## Modality-bias mitigation baseline (`balanced_mm/`)

The proposal's *Modality Bias Score* measures **where the model looks** (attention mass on image vs. text tokens).
`balanced_mm/` adds the complementary **optimisation-side** view from the TPAMI-2024 paper: in joint training the
logits are a sum of uni-modal contributions `f = W¹φ¹ + W²φ² + b`, so the more discriminative modality drives
`∂ℓ/∂f = softmax(f) − onehot(y) → 0` and the other encoder is left under-optimised.
The module monitors a per-batch **discrepancy ratio ρᵐ** (Eq. 6–7) and

* **OPM** – drops the dominant modality's feature with adaptive probability `q = q_base(1 + λ·tanh(ρ−1))` (forward pass),
* **OGM-GE** – scales the dominant encoder's gradient by `k = 1 − α·tanh(ρ−1)` and re-injects Gaussian noise so the
  SGD-noise variance becomes `(k²+1)×` the original (backward pass).

```bash
cd balanced_mm
pip install -r requirements.txt
python tests/test_modulation.py                                   # 7 unit tests
bash scripts/run_synthetic_compare.sh                             # image-only / text-only / none / opm / ogm / both
python train.py --data csv --train_csv data/train.csv --val_csv data/val.csv --img_root data/images \
                --modulation ogm --probe                          # your own Text+Image data
python plug_in_example.py                                         # add OPM/OGM to an existing training loop in 3 lines
```

Synthetic reference run (CPU, 15 epochs): fused val acc `none 0.885 → OGM 0.898 → OPM 0.905 → OPM+OGM 0.908`,
discrepancy ratio `1.45 → 1.13`. Curves: `balanced_mm/runs/curves.png`.

## Team
I24AI001, I24AI009, I24AI026, I24AI028
