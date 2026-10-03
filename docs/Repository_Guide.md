# Repository Guide
## XAI-Driven Modality Bias Detection and Mitigation

**Project type:** Deep Learning semester project

**Team:** I24AI001, I24AI009, I24AI026, I24AI028

**Core stack:** Python, PyTorch, torchvision, Hugging Face (optional), NumPy, Matplotlib

---

## 1. One-minute summary

This project studies **modality bias** in multimodal models. A multimodal model may receive two useful inputs—for example, an image and text—but learn to depend mainly on the easier modality. The other encoder then remains under-trained, making the model less balanced and potentially less robust.

The repository has two connected parts:

1. **Detection / explanation:** PaliGemma attention visualization, image Integrated Gradients, text gradient × input, uni-modal accuracy, and modality attribution shares.
2. **Mitigation:** OPM and OGM-GE dynamically slow down the dominant modality during training so that the weaker encoder receives a better learning opportunity.

The main implemented pipeline is in `balanced_mm/`. It supports image + text, audio + text, synthetic data, Food-101, and MELD. Experiments compare four settings: no modulation, OPM, OGM-GE, and both methods together.

**Main finding:** modulation clearly reduces modality discrepancy. It also improves accuracy on the synthetic and Food-101 settings, but on MELD it reduces imbalance while slightly reducing accuracy because text is much stronger than the available audio features.

---

## 2. Problem intuition

Assume the model receives two modalities:

- image feature: `phi_image`
- text feature: `phi_text`

A late-fusion classifier combines both:

```text
logits = W_image * phi_image + W_text * phi_text + bias
```

If text is easier, its branch can reduce the classification loss quickly. Once the fused prediction is already confident, the loss gradient becomes small. The image branch then receives a weak learning signal and may remain under-optimized. This is the **rich-get-richer effect** behind modality imbalance.

The project follows this cycle:

```text
Detect -> Quantify -> Mitigate -> Verify
```

- **Detect:** attention, Integrated Gradients, gradient × input, and uni-modal probes
- **Quantify:** discrepancy ratio `rho`
- **Mitigate:** OPM and/or OGM-GE
- **Verify:** fused accuracy, uni-modal accuracy, `rho`, macro-F1, ECE, and plots

---

## 3. High-level architecture

```text
Image / Audio input             Text input
        |                            |
        v                            v
Image CNN or Audio MLP       Transformer / HF encoder
        |                            |
        +-------- feature list ------+
                     |
          modality score + rho
                     |
             optional OPM drop
                     |
              feature concat
                     |
          linear or MLP fusion head
                     |
              class prediction
                     |
             cross-entropy loss
                     |
              backward pass
                     |
       optional OGM-GE gradient update
                     |
              optimizer step
```

### Encoders

- **Image:** `SmallCNN` or ResNet-18
- **Text:** local Transformer encoder or optional Hugging Face model
- **Audio:** `VectorMLPEncoder` for precomputed feature vectors
- **Fusion:** concatenation followed by a linear or MLP classification head

The data loader automatically detects the modalities from CSV columns. For example, a CSV with `audio,text,label` builds an audio/text model without an image branch.

---

## 4. Core measurement: discrepancy ratio

For each modality `m`, the model first obtains that modality's contribution to the classifier logits. For a linear head:

```text
unimodal_logit_m = W_m * phi_m + bias / M
```

The true-class confidence of modality `m` for sample `i` is:

```text
s_i^m = softmax(unimodal_logit_m)[true_class_i]
```

The batch discrepancy ratio is:

```text
rho^m = average over j != m of:
        sum_i(s_i^m) / sum_i(s_i^j)
```

Interpretation:

- `rho = 1`: modality scores are balanced
- `rho > 1`: this modality is dominant
- `rho < 1`: this modality is weaker

`bml/modulation.py` implements the score and ratio calculations. `bml/engine.py` records them during both training and evaluation.

---

## 5. Mitigation methods

### 5.1 OPM: On-the-fly Prediction Modulation

OPM acts in the **forward pass**. It calculates an adaptive feature-drop probability for a dominant modality:

```text
z = tanh(rho - 1)
q = q_base * (1 + lambda * z), if rho > 1
q = 0,                         otherwise
```

A dominant feature is randomly removed for selected training samples. The weak modality is not dropped. This prevents the dominant branch from solving every sample by itself and allows the weak branch to learn.

Important implementation detail: the current `q` is applied first, and the latest `rho` updates `q` for the next iteration.

### 5.2 OGM: On-the-fly Gradient Modulation

OGM acts in the **backward pass**. It scales the dominant encoder's gradient:

```text
k = 1 - alpha * tanh(rho - 1), if rho > 1
k = 1,                         otherwise
```

- dominant encoder: gradient is reduced by factor `k`
- weak encoder: gradient is unchanged
- fusion head: not modulated

This slows the dominant branch rather than artificially increasing the weak branch's gradient.

### 5.3 GE: Generalization Enhancement

OGM-GE also adds Gaussian noise based on each parameter tensor's gradient standard deviation. The purpose is to recover useful stochasticity and improve generalization after gradient scaling.

### 5.4 Combined mode

`--modulation both` applies OPM in the forward pass and OGM-GE after backpropagation. Combined mode is strongest on the synthetic benchmark, but it is not guaranteed to be best on every dataset.

---

## 6. Exact training flow

For every mini-batch, `train_one_epoch()` performs these steps:

1. Move inputs and labels to the selected device.
2. Run each modality encoder once.
3. Compute uni-modal logits from the undropped features.
4. Compute true-class scores and `rho`.
5. Apply OPM feature dropping when enabled.
6. Concatenate features and calculate fused logits.
7. Compute cross-entropy loss.
8. Run backpropagation.
9. Apply OGM gradient scaling and GE noise when enabled.
10. Apply optional gradient clipping.
11. Run the optimizer step.
12. Log loss, accuracy, uni-modal accuracy, `rho`, `q`, and `k`.

The best validation checkpoint and final checkpoint are stored in the run directory. Model checkpoints are Git-ignored, while configuration, history, summary, vocabulary, label map, and logs are retained for reproducibility.

---

## 7. Repository map

| Path | Responsibility |
|---|---|
| `Project_Proposal.md` | original problem statement, objectives, and proposed BMA extension |
| `multimodal (2).ipynb` | exploratory PaliGemma inference and attention heat-map notebook |
| `balanced_mm/train.py` | CLI arguments, model construction, optimizer, scheduler, and training entry point |
| `balanced_mm/eval.py` | checkpoint evaluation, confusion matrix, macro-F1, ECE, and probes |
| `balanced_mm/compare.py` | side-by-side comparison of completed runs |
| `balanced_mm/plot_history.py` | training and discrepancy curves |
| `balanced_mm/bml/data.py` | tokenization, CSV loading, audio features, synthetic dataset, and data loaders |
| `balanced_mm/bml/models.py` | image, text, audio encoders and late-fusion model |
| `balanced_mm/bml/modulation.py` | discrepancy ratio, OPM, OGM-GE, and unified controller |
| `balanced_mm/bml/engine.py` | training, evaluation, and frozen-encoder probing |
| `balanced_mm/bml/xai.py` | Integrated Gradients, token relevance, and modality attribution |
| `balanced_mm/bml/metrics.py` | accuracy, confusion matrix, per-class accuracy, macro-F1, and ECE |
| `balanced_mm/bml/analysis.py` | aggregates runs and generates report tables/plots |
| `balanced_mm/scripts/` | dataset preparation, benchmark sweeps, report generation, notebook build |
| `balanced_mm/tests/` | tests for equations, models, data, XAI, metrics, and report generation |
| `balanced_mm/runs/` | raw run configuration, history, summary, and logs |
| `balanced_mm/results/` | aggregate `RESULTS.md` and benchmark figures |

---

## 8. Datasets and experimental setup

### 8.1 Synthetic benchmark

- modalities: generated image + generated text
- classes: 6
- training / validation: 2,400 / 600
- informative probability: `0.7` independently for each modality
- image signal: class-specific colored patch over Gaussian noise
- text signal: class-specific keyword among random tokens
- model: SmallCNN + two-layer Transformer
- training: 15 epochs, SGD, learning rate `0.01`, batch size `32`
- reporting: three seeds

The theoretical uni-modal ceiling is approximately `0.75`, while the fused ceiling is approximately `0.925`. A high fused score therefore requires learning both branches.

### 8.2 Food-101 experiment

- modalities: image + constructed prompt text
- subset: 10 classes
- training / validation: 2,500 / 1,000
- image encoder: SmallCNN at 64 × 64 model input
- text construction: correct class prompt with probability `0.7`; generic food prompt otherwise
- training: 12 epochs, three seeds

Food-101 has no native text annotation. The text modality is deliberately constructed for a controlled imbalance experiment and must not be described as an original Food-101 annotation.

### 8.3 MELD experiment

- modalities: dialogue text + official 300-dimensional audio features
- classes: 7 emotions
- official split sizes: 9,989 train / 1,109 validation / 2,610 test
- text encoder: local Transformer, maximum length 48
- audio encoder: MLP over precomputed features
- training: 12 epochs, three seeds

The experiment uses precomputed audio features, not end-to-end waveform learning.

---

## 9. Main results

All values below are mean ± standard deviation over three seeds. `rho` values are final training discrepancy ratios from the generated report.

### Synthetic

| Method | Best validation accuracy | Final `rho_image` |
|---|---:|---:|
| No modulation | 0.887 ± 0.022 | 1.344 |
| OGM-GE | 0.898 ± 0.017 | 1.188 |
| OPM | 0.904 ± 0.023 | 1.140 |
| OPM + OGM-GE | **0.906 ± 0.025** | **1.121** |

**Meaning:** all modulation methods reduce image dominance and improve validation accuracy. Combined modulation gives the best mean accuracy and lowest image discrepancy in this experiment.

### Food-101

| Method | Best validation accuracy | Final `rho_text` | Final `rho_image` |
|---|---:|---:|---:|
| No modulation | 0.812 ± 0.004 | 2.726 | 0.381 |
| OGM-GE | 0.814 ± 0.005 | 2.694 | 0.385 |
| OPM | **0.845 ± 0.000** | 2.085 | 0.494 |
| OPM + OGM-GE | 0.842 ± 0.005 | **2.005** | **0.512** |

**Meaning:** prompt text dominates because it frequently contains the class name. OPM gives the best accuracy improvement, while combined modulation gives the smallest modality gap.

### MELD

| Method | Best validation accuracy | Final `rho_text` | Final `rho_audio` |
|---|---:|---:|---:|
| No modulation | **0.578 ± 0.002** | 2.219 | 0.458 |
| OGM-GE | 0.573 ± 0.002 | 1.598 | 0.632 |
| OPM | 0.565 ± 0.004 | 1.237 | 0.819 |
| OPM + OGM-GE | 0.561 ± 0.006 | **1.219** | **0.832** |

**Meaning:** modulation strongly balances text and audio, but validation accuracy decreases. Text alone is already strong (`0.560`) and audio is weaker (`0.469`), so aggressively limiting text can reduce overall predictive performance. This demonstrates an accuracy–balance trade-off.

---

## 10. XAI and verification tools

### PaliGemma notebook

`multimodal (2).ipynb` is an exploratory notebook that loads PaliGemma, accepts an image and prompt, requests generation-time attention, and overlays image-token attention as a heat map. It demonstrates the detection side of the proposal; it does not apply OPM/OGM end-to-end to the 3B model.

### Integrated Gradients

`integrated_gradients_image()` interpolates from a zero-image baseline to the input image and accumulates predicted-class gradients. The result has the same shape as the image and estimates pixel contribution.

### Text relevance

`token_importance_text()` uses gradient × embedding because gradients with respect to discrete token IDs are not meaningful. Padding positions are masked out.

### Modality attribution

`modality_attribution()` converts absolute image and text attribution into normalized shares that sum to one. These shares provide an XAI view of relative modality contribution.

### Uni-modal probing

`--probe` freezes each trained encoder, extracts its features, and fits a new linear classifier. Probe accuracy measures encoder quality independently of the existing fusion head.

---

## 11. How to run the project

### Install

```bash
cd balanced_mm
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest
```

### Single synthetic run

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

### Complete synthetic comparison

```bash
bash scripts/run_synthetic_compare.sh 15 2400 smallcnn 3
bash scripts/run_seed_sweep.sh
python scripts/make_report.py
```

### Food-101

```bash
python scripts/make_food101_csv.py --root data/food101
bash scripts/run_food101.sh
python scripts/make_report.py
```

### MELD

```bash
python scripts/make_meld_csv.py \
  --features_dir <meld-features-directory> \
  --out data/meld
bash scripts/run_meld.sh
python scripts/make_report.py
```

### Evaluate and compare

```bash
python eval.py --run_dir runs/ogm --test_csv data/test.csv --probe
python compare.py runs/none runs/opm runs/ogm runs/both
python plot_history.py runs/none runs/opm runs/ogm runs/both --out curves.png
python -m pytest tests
```

---

## 12. Output files

Each training run can contain:

| File | Meaning |
|---|---|
| `config.json` | exact CLI configuration |
| `history.json` | epoch-wise training and validation metrics |
| `summary.json` | best accuracy, best epoch, and final metrics |
| `train.log` | readable training log |
| `vocab.json` | fitted word-level vocabulary |
| `label_map.json` | class-name to integer mapping |
| `best.pt` | best validation checkpoint; Git-ignored |
| `last.pt` | final checkpoint; Git-ignored |

`python scripts/make_report.py` scans completed runs and generates `results/RESULTS.md` plus accuracy and discrepancy plots.

---

## 13. What is implemented vs proposed

### Implemented

- discrepancy monitoring for two or more modalities
- OPM, OGM, and GE
- image/text and audio/text late fusion
- synthetic, Food-101, and MELD pipelines
- XAI attribution utilities
- PaliGemma attention demonstration
- metrics, tests, seed sweeps, run logs, and automatic reports

### Proposed or future work

- Balanced Modal Attention (BMA) inside PaliGemma cross-attention
- XAI-driven regularization directly on PaliGemma
- full VQAv2 / COCO evaluation
- end-to-end modulation of the 3B PaliGemma model
- full-resolution and larger-backbone experiments
- end-to-end MELD waveform training

This distinction is important: OPM/OGM-GE are the implemented mitigation baselines; BMA remains part of the proposal.

---

## 14. Limitations

1. Food-101 text is constructed rather than naturally annotated.
2. Food-101 uses a compact ten-class, low-resolution protocol.
3. MELD audio is represented by precomputed features.
4. Lower discrepancy does not guarantee higher task accuracy.
5. Hyperparameters are not exhaustively tuned for every dataset.
6. PaliGemma is used for exploratory detection, not full mitigation training.
7. Attention is useful for visualization but should not be treated as a complete causal explanation.

---

## 15. Short explanation script

> This project studies modality bias in multimodal learning. In joint training, one modality can become dominant and suppress learning in the weaker encoder. The repository detects this using attention, Integrated Gradients, uni-modal scores, and a discrepancy ratio called rho. It mitigates the problem using OPM, which adaptively drops dominant features in the forward pass, and OGM-GE, which scales dominant encoder gradients and adds controlled noise in the backward pass. The methods are evaluated on synthetic image/text data, a controlled Food-101 image/prompt setup, and MELD text/audio features. Modulation improves both balance and accuracy on synthetic and Food-101 data. On MELD it improves balance but slightly reduces accuracy, showing that balance and task performance can trade off when one modality is genuinely more informative.

---

## 16. Key terms

| Term | Meaning |
|---|---|
| Modality | one type of input, such as image, text, or audio |
| Modality bias | excessive dependence on one modality |
| Late fusion | concatenate modality features before classification |
| Uni-modal logit | prediction contribution from one modality |
| `rho` | relative true-class confidence of one modality vs the others |
| OPM | adaptive dominant-feature dropping in the forward pass |
| OGM | adaptive dominant-gradient scaling in the backward pass |
| GE | gradient-noise regularization used with OGM |
| Integrated Gradients | attribution from a baseline to the actual input |
| ECE | Expected Calibration Error |
| Probe | new classifier trained on frozen encoder features |

---

## Reference

Y. Wei, D. Hu, H. Du, and J.-R. Wen, “On-the-fly Modulation for Balanced Multimodal Learning,” *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 2024.
