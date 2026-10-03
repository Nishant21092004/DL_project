# Balanced Multimodal Learning with OPM and OGM-GE

PyTorch implementation of the training-time modulation methods described in:

- Y. Wei, D. Hu, H. Du, and J.-R. Wen, **“On-the-fly Modulation for Balanced Multimodal Learning,”** IEEE TPAMI, 2024.
- X. Peng et al., **“Balanced Multimodal Learning via On-the-fly Gradient Modulation,”** CVPR, 2022.

The package provides late-fusion image/text and audio/text models, modality discrepancy measurement, OPM, OGM-GE, attribution utilities, experiment scripts, and automatic reports. The core modulator supports two or more modalities.

## Package layout

```text
balanced_mm/
├── bml/
│   ├── modulation.py     discrepancy ratios, OPM, OGM-GE, BalancedModulator
│   ├── models.py         image, text, and vector encoders; late-fusion model
│   ├── data.py           CSV and synthetic datasets, tokenization, collation
│   ├── engine.py         training, evaluation, and uni-modal probing
│   ├── xai.py            image IG, token relevance, modality attribution
│   ├── metrics.py        accuracy, confusion matrix, macro-F1, ECE
│   ├── analysis.py       run aggregation, tables, and plots
│   └── utils.py          reproducibility, logging, and checkpoint helpers
├── train.py              training CLI
├── eval.py               checkpoint evaluation CLI
├── compare.py            comparison table for multiple runs
├── plot_history.py       learning and discrepancy curves
├── plug_in_example.py    minimal integration example
├── notebooks/
│   └── 01_walkthrough.ipynb
├── scripts/
│   ├── run_synthetic_compare.sh
│   ├── run_seed_sweep.sh
│   ├── run_food101.sh
│   ├── run_meld.sh
│   ├── make_food101_csv.py
│   ├── make_meld_csv.py
│   ├── make_report.py
│   ├── build_walkthrough_notebook.py
│   └── make_demo_csv.py
├── results/              generated report and figures
├── runs/                 run configurations, histories, summaries, and logs
├── tests/                33 test functions
└── requirements.txt
```

## Method

A block-linear late-fusion classifier can be written as

```text
f = Σₘ Wᵐφᵐ + b,
```

where `φᵐ` is the feature vector produced by modality encoder `m`. The true-class confidence of an individual modality is

```text
sᵢᵐ = softmax(Wᵐφᵢᵐ + b/M)[yᵢ].
```

The per-batch discrepancy ratio is

```text
ρᵐ = (1/(M-1)) Σⱼ≠ₘ (Σᵢ sᵢᵐ / Σᵢ sᵢʲ).
```

A value above one indicates that modality `m` is more discriminative than the other modalities in the current batch.

| Component | Stage | Operation |
|---|---|---|
| OPM | forward | drops a dominant modality feature with adaptive probability `q = q_base(1 + λ tanh(ρ-1))` |
| OGM | backward | scales a dominant encoder gradient by `k = 1 - α tanh(ρ-1)` |
| GE | backward | adds Gaussian noise based on gradient standard deviation |

Modulation is disabled during evaluation, so inference has no additional cost.

## Installation

```bash
cd balanced_mm
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest
```

Optional dependencies:

```bash
# Hugging Face text encoder
pip install transformers

# Notebook generation
pip install nbformat nbclient ipykernel
```

Install the appropriate PyTorch build separately when CUDA support is required.

## Synthetic quick start

The synthetic dataset independently makes each modality informative with probability `0.7`. A fused model must therefore learn both branches to outperform either uni-modal baseline.

```bash
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

Run image-only, text-only, unmodulated, OPM, OGM-GE, and combined baselines:

```bash
bash scripts/run_synthetic_compare.sh 15 2400 smallcnn 3
bash scripts/run_seed_sweep.sh
python scripts/make_report.py
python plot_history.py \
  runs/syn_none runs/syn_opm runs/syn_ogm runs/syn_both \
  --out runs/curves.png
```

## CSV data

### Image and text

```csv
image,text,label
images/000.jpg,"a red car parked near the beach",car
images/001.jpg,"golden retriever playing with a ball",dog
```

Train a late-fusion model:

```bash
python train.py \
  --data csv \
  --train_csv data/train.csv \
  --val_csv data/val.csv \
  --img_root data/images \
  --image_encoder resnet18 \
  --text_encoder transformer \
  --max_len 64 \
  --modulation ogm \
  --alpha 0.5 \
  --epochs 60 \
  --batch_size 32 \
  --lr 1e-3 \
  --sched cos \
  --out_dir runs/ogm \
  --probe
```

Column names can be changed with `--col_image`, `--col_text`, and `--col_label`. If no validation CSV is provided, the loader reserves ten percent of the training data for validation.

### Audio features and text

The audio column accepts either a NumPy file or an entry in a packed archive:

```csv
audio,text,label
audio/000.npy,"dialogue text",neutral
audio.npz::train_00001,"another utterance",joy
```

The loader automatically omits the image encoder when no image column is present.

## Training variants

```bash
--modulation none
--modulation opm --q_base 0.5 --lam 0.5
--modulation ogm --alpha 0.5
--modulation both

--only image
--only text
--only audio

--pretrained_image
--text_encoder hf --hf_model distilbert-base-uncased --lr_text 2e-5
--head mlp --score_mode zero_out
--amp
```

Evaluate and compare completed runs:

```bash
python eval.py --run_dir runs/ogm --test_csv data/test.csv --img_root data/images --probe
python compare.py runs/none runs/opm runs/ogm runs/both
python plot_history.py runs/none runs/opm runs/ogm runs/both --out curves.png
```

Each run directory contains `config.json`, `history.json`, `summary.json`, `label_map.json`, `vocab.json`, `train.log`, and model checkpoints. Checkpoints are excluded from Git by default.

## Integration into another training loop

```python
from bml.modulation import BalancedModulator

modulator = BalancedModulator(
    num_modalities=2,
    mode="both",
    q_base=0.5,
    lam=0.5,
    alpha=0.5,
    ge=True,
)

for inputs, labels in loader:
    optimizer.zero_grad()
    features = [image_encoder(inputs["image"]), text_encoder(inputs["text"])]
    features, rho = modulator.before_fusion(
        features, labels, unimodal_logits, epoch
    )
    logits = fusion_head(torch.cat(features, dim=1))
    loss = F.cross_entropy(logits, labels)
    loss.backward()
    modulator.after_backward(
        [image_encoder.parameters(), text_encoder.parameters()], epoch
    )
    optimizer.step()
```

`unimodal_logits` should return one logit tensor per modality. For a linear fusion head, split the weight matrix into modality blocks and assign `b/M` to each block. For an MLP fusion head, use `unimodal_logits_zero_out` from `bml.modulation`.

A complete executable example is available in [`plug_in_example.py`](plug_in_example.py).

## Equation-to-code mapping

| Paper item | Implementation |
|---|---|
| Eq. 2: fusion decomposition | `LateFusionModel.fuse` and `LateFusionModel.unimodal_logits` |
| Eq. 6: uni-modal score | `unimodal_scores_from_logits` |
| Eq. 7: discrepancy ratio | `discrepancy_ratios` |
| Eq. 8: OPM | `OPM.update` and `OPM.apply` |
| Eq. 11–12: OGM | `OGMGE.coefficients` and `OGMGE.apply_` |
| Eq. 16–17: GE | noise injection in `OGMGE.apply_` |
| zero-out scoring | `unimodal_logits_zero_out` |
| training order | `engine.train_one_epoch` |
| uni-modal probing | `engine.probe_unimodal_encoders` |

## Hyperparameters

| Argument | Default | Purpose |
|---|---:|---|
| `--alpha` | 0.5 | OGM strength |
| `--q_base` | 0.5 | base OPM drop probability |
| `--lam` | 0.5 | sensitivity of OPM to discrepancy |
| `--z` | `tanh` | discrepancy mapping (`tanh` or `sigmoid`) |
| `--mod_start` | 0 | first modulation epoch |
| `--mod_end` | no limit | final modulation epoch |
| `--ge_scope` | `all` | modalities receiving GE noise |

Practical considerations:

1. OGM is most direct with momentum SGD. Adaptive optimizers can partially cancel uniform gradient scaling through their second-moment normalization.
2. Compare each modulated run against `--modulation none` with the same seed and training configuration.
3. If `ρ` remains close to one, the modalities are already balanced and modulation should have little effect.
4. A higher training loss under modulation is expected because the dominant branch is deliberately constrained.
5. With automatic mixed precision, call `scaler.unscale_(optimizer)` before gradient modulation. Apply gradient clipping after modulation.
6. Multi-layer fusion heads require zero-out scoring.

## Datasets

### Food-101

Food-101 contains images but no text. `make_food101_csv.py` creates a controlled text modality: with probability `--text_p` (default `0.7`) the prompt names the correct class; otherwise it uses a generic food prompt. This derived modality is intended for a controlled imbalance experiment and is not an original Food-101 annotation.

```bash
python scripts/make_food101_csv.py --root data/food101
bash scripts/run_food101.sh
python scripts/make_report.py
```

The committed protocol uses ten classes, 2,500 training samples, 1,000 validation samples, 12 epochs, and three seeds.

### MELD

`make_meld_csv.py` converts the official MELD dialogue text and 300-dimensional per-utterance audio features into CSV files and a packed `audio.npz` archive.

```bash
python scripts/make_meld_csv.py \
  --features_dir <meld-features-directory> \
  --out data/meld
bash scripts/run_meld.sh
python scripts/make_report.py
```

The protocol uses the official split sizes: 9,989 training, 1,109 validation, and 2,610 test examples.

## Benchmark results

Full per-seed details and figures are generated in [`results/RESULTS.md`](results/RESULTS.md).

### Synthetic benchmark

| Method | Best validation accuracy | Final `ρ_image` |
|---|---:|---:|
| None | 0.887 ± 0.022 | 1.344 |
| OGM-GE | 0.898 ± 0.017 | 1.188 |
| OPM | 0.904 ± 0.023 | 1.140 |
| OPM + OGM-GE | **0.906 ± 0.025** | **1.121** |

Uni-modal validation accuracies are `0.715` for image and `0.738` for text.

### Food-101

| Method | Best validation accuracy | Final `ρ_text` | Final `ρ_image` |
|---|---:|---:|---:|
| None | 0.812 ± 0.004 | 2.726 | 0.381 |
| OGM-GE | 0.814 ± 0.005 | 2.694 | 0.385 |
| OPM | **0.845 ± 0.000** | 2.085 | 0.494 |
| OPM + OGM-GE | 0.842 ± 0.005 | **2.005** | **0.512** |

Uni-modal validation accuracies are `0.554` for image and `0.739` for text.

### MELD

| Method | Best validation accuracy | Final `ρ_text` | Final `ρ_audio` |
|---|---:|---:|---:|
| None | **0.578 ± 0.002** | 2.219 | 0.458 |
| OGM-GE | 0.573 ± 0.002 | 1.598 | 0.632 |
| OPM | 0.565 ± 0.004 | 1.237 | 0.819 |
| OPM + OGM-GE | 0.561 ± 0.006 | **1.219** | **0.832** |

Uni-modal validation accuracies are `0.560` for text and `0.469` for audio. The modulation methods reduce the text/audio discrepancy but lower validation accuracy in this setup, indicating that aggressively balancing a strong text branch with a weaker audio branch is not always beneficial.

## Report generation

```bash
python scripts/make_report.py
```

The report generator discovers completed runs through `summary.json`, groups them by dataset and modulation method, computes mean and standard deviation across seeds, and writes markdown tables and figures to `results/`.

## Tests

```bash
python -m pytest tests
```

The test suite covers:

- two- and three-modality discrepancy ratios
- OPM probabilities and masks
- OGM coefficients and GE variance
- fusion-head decomposition
- model factories and parameter groups
- image/text and audio/text data loading
- metrics and calibration
- Integrated Gradients and token relevance
- report aggregation and artifact generation

## Citation

```bibtex
@article{wei2024onthefly,
  title={On-the-fly Modulation for Balanced Multimodal Learning},
  author={Wei, Yake and Hu, Di and Du, Henghui and Wen, Ji-Rong},
  journal={IEEE Transactions on Pattern Analysis and Machine Intelligence},
  year={2024}
}

@inproceedings{peng2022balanced,
  title={Balanced Multimodal Learning via On-the-fly Gradient Modulation},
  author={Peng, Xiaokang and Wei, Yake and Deng, Andong and Wang, Dong and Hu, Di},
  booktitle={Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition},
  year={2022}
}
```
