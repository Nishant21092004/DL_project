# XAI-Driven Modality Bias Detection and Mitigation

Semester project on detecting, measuring, and reducing modality imbalance in multimodal deep learning models.

The repository contains two complementary experiments:

1. **PaliGemma attention analysis** — an exploratory notebook for multimodal inference and attention heat-map visualization.
2. **Balanced multimodal learning** — a reproducible PyTorch implementation of On-the-fly Prediction Modulation (OPM) and On-the-fly Gradient Modulation with Generalization Enhancement (OGM-GE), evaluated on synthetic data, Food-101, and MELD.

The complete project proposal is available in [`Project_Proposal.md`](Project_Proposal.md). A concise end-to-end explanation is available as a [PDF guide](docs/Repository_Guide.pdf) and an [editable Markdown guide](docs/Repository_Guide.md). Balanced Modal Attention (BMA), described in the proposal, remains a proposed extension; the current mitigation experiments use OPM and OGM-GE as training-time baselines.

## Implemented components

- per-batch modality discrepancy ratio `ρ` (Wei et al., Eq. 6–7)
- OPM feature dropping during the forward pass
- OGM-GE gradient scaling and noise injection during the backward pass
- image, text, and precomputed audio-feature encoders
- late-fusion classification with modality-wise logit decomposition
- Integrated Gradients for images and gradient × input attribution for text
- uni-modal probing, confusion matrices, macro-F1, and calibration error
- deterministic synthetic experiments and three-seed benchmark scripts
- automatic result tables and plots
- 33 test functions covering modulation, models, data, metrics, XAI, and reporting

## Repository structure

| Path | Description |
|---|---|
| [`Project_Proposal.md`](Project_Proposal.md) | Problem statement, objectives, methodology, and project plan |
| [`multimodal (2).ipynb`](multimodal%20%282%29.ipynb) | PaliGemma loading, inference, attention extraction, and heat-map visualization |
| [`balanced_mm/`](balanced_mm/) | Training and evaluation package for OPM and OGM-GE |
| [`balanced_mm/bml/modulation.py`](balanced_mm/bml/modulation.py) | Discrepancy ratio, OPM, OGM-GE, and the unified modulator |
| [`balanced_mm/bml/xai.py`](balanced_mm/bml/xai.py) | Integrated Gradients, token relevance, and modality attribution |
| [`balanced_mm/notebooks/01_walkthrough.ipynb`](balanced_mm/notebooks/01_walkthrough.ipynb) | Executed synthetic walkthrough with plots and attribution output |
| [`balanced_mm/results/RESULTS.md`](balanced_mm/results/RESULTS.md) | Auto-generated benchmark tables and figures |
| [`docs/Repository_Guide.pdf`](docs/Repository_Guide.pdf) | Concise project architecture, methodology, results, and usage guide |
| [`docs/Repository_Guide.md`](docs/Repository_Guide.md) | Editable source for the repository guide |
| [`docs/OGM_OPM_Explanation.pdf`](docs/OGM_OPM_Explanation.pdf) | Supporting derivation notes |
| [`docs/Wei2024_On-the-fly_Modulation_TPAMI.pdf`](docs/Wei2024_On-the-fly_Modulation_TPAMI.pdf) | Reference paper |

A detailed implementation guide is provided in [`balanced_mm/README.md`](balanced_mm/README.md).

## Method summary

For late fusion, the classifier logit is decomposed into modality-specific contributions:

```text
f = W¹φ¹ + W²φ² + b
```

For each modality `m`, the true-class score is computed from its individual logit block. The discrepancy ratio compares that score with the scores of the other modalities:

```text
sᵢᵐ = softmax(Wᵐφᵢᵐ + b/M)[yᵢ]
ρᵐ = (1/(M-1)) Σⱼ≠ₘ (Σᵢ sᵢᵐ / Σᵢ sᵢʲ)
```

`ρᵐ > 1` identifies a dominant modality. OPM responds by adaptively dropping dominant features, while OGM-GE scales the corresponding encoder gradients and adds Gaussian noise. These operations are used only during training, so they add no inference-time cost.

## Installation

```bash
cd balanced_mm
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest
```

For GPU training, install the PyTorch build matching the local CUDA version before installing the remaining requirements.

## Quick start

Run one synthetic experiment:

```bash
cd balanced_mm
python train.py \
  --data synthetic \
  --image_encoder smallcnn \
  --img_size 64 \
  --epochs 15 \
  --syn_train_n 2400 \
  --lr 0.01 \
  --modulation ogm \
  --out_dir runs/syn_ogm
```

Run all synthetic baselines and generate a report:

```bash
bash scripts/run_synthetic_compare.sh 15 2400 smallcnn 3
bash scripts/run_seed_sweep.sh
python scripts/make_report.py
```

Run the test suite:

```bash
python -m pytest tests
```

## Datasets and protocols

### Synthetic benchmark

Each modality is independently informative with probability `0.7`. The benchmark uses 2,400 training examples, 600 validation examples, six classes, a SmallCNN image encoder, a Transformer text encoder, and three random seeds.

### Food-101

The experiment uses a 10-class image subset. Since Food-101 does not contain text, the data-preparation script constructs a controlled text modality: the prompt contains the correct class name with probability `0.7` and a generic food prompt otherwise. This setup evaluates imbalance under a deliberately constructed image/text pairing; it is not an original Food-101 multimodal annotation.

```bash
cd balanced_mm
python scripts/make_food101_csv.py --root data/food101
bash scripts/run_food101.sh
```

### MELD

The MELD experiment combines dialogue text with the official 300-dimensional per-utterance audio features. It uses the official train and validation splits.

```bash
cd balanced_mm
python scripts/make_meld_csv.py --features_dir <features-directory> --out data/meld
bash scripts/run_meld.sh
```

## Results

The following values are means over three seeds. Full per-run results and plots are in [`balanced_mm/results/RESULTS.md`](balanced_mm/results/RESULTS.md).

### Synthetic

| Method | Best validation accuracy | Final `ρ_image` |
|---|---:|---:|
| No modulation | 0.887 ± 0.022 | 1.344 |
| OGM-GE | 0.898 ± 0.017 | 1.188 |
| OPM | 0.904 ± 0.023 | 1.140 |
| OPM + OGM-GE | **0.906 ± 0.025** | **1.121** |

### Food-101

| Method | Best validation accuracy | Final `ρ_text` |
|---|---:|---:|
| No modulation | 0.812 ± 0.004 | 2.726 |
| OGM-GE | 0.814 ± 0.005 | 2.694 |
| OPM | **0.845 ± 0.000** | 2.085 |
| OPM + OGM-GE | 0.842 ± 0.005 | **2.005** |

### MELD

| Method | Best validation accuracy | Final `ρ_text` |
|---|---:|---:|
| No modulation | **0.578 ± 0.002** | 2.219 |
| OGM-GE | 0.573 ± 0.002 | 1.598 |
| OPM | 0.565 ± 0.004 | 1.237 |
| OPM + OGM-GE | 0.561 ± 0.006 | **1.219** |

The synthetic and Food-101 experiments show that lower modality discrepancy can coincide with higher validation accuracy. On MELD, modulation reduces the discrepancy substantially but also lowers accuracy because the text branch is considerably stronger than the audio branch. This is an accuracy–balance trade-off rather than a uniform improvement across datasets.

## Reproducibility

Each run stores its configuration, history, label mapping, summary, and training log under `balanced_mm/runs/`. Reports are generated from these files rather than manually entered values.

```bash
cd balanced_mm
python scripts/make_report.py
python compare.py runs/syn_none runs/syn_opm runs/syn_ogm runs/syn_both
```

## Current limitations

- Food-101 text is synthetically constructed and should not be interpreted as a native text annotation.
- The committed experiments use compact encoders and subset-scale settings to keep CPU execution practical.
- MELD audio uses precomputed features rather than end-to-end waveform training.
- The PaliGemma notebook demonstrates detection and visualization; end-to-end modulation of the 3B model is not included.
- The proposed BMA layer and full VQAv2/COCO evaluation remain future work.

## Reference

Y. Wei, D. Hu, H. Du, and J.-R. Wen, “On-the-fly Modulation for Balanced Multimodal Learning,” *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 2024.

## Team

I24AI001 · I24AI009 · I24AI026 · I24AI028
