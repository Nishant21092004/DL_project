# One-Page Project Proposal

**Course:** Deep Learning (Semester Project)
**Team:** I24AI001, I24AI009, I24AI026, I24AI028
**Date:** August 2026

---

## Project Title
**XAI-Driven Modality Bias Detection and Mitigation in Multimodal Deep Learning Models**

---

## Problem Description

Multimodal deep learning models that jointly process vision and language inputs have demonstrated remarkable capabilities, yet they suffer from a critical, often invisible flaw: **modality bias**. These models disproportionately rely on one modality — typically language — while underutilizing the other, leading to unreliable predictions, poor generalization, and lack of trustworthiness. Recent studies confirm that in large Vision-Language Models (VLMs), over 56% of predictions match text-only answers versus only 27% matching image-only inputs, revealing severe language dominance. This bias is difficult to detect without looking inside the model, and no general-purpose solution currently exists for dynamically equalizing modality contributions during inference or training.

---

## Objectives

1. **Detect and quantify modality bias** in a pretrained VLM (PaliGemma-3B) using XAI attribution methods — specifically attention weight analysis and Integrated Gradients — to produce a measurable *modality bias score* per sample and across datasets.

2. **Evaluate whether XAI attribution scores can mitigate modality bias** by using them as a feedback signal in a bias regularization loss during fine-tuning, inspired by the Reveal-to-Revise framework.

3. **Develop a novel Balanced Modal Attention (BMA) mechanism** — a lightweight, learnable reweighting layer that dynamically equalizes the contribution of visual and textual tokens within the cross-attention layers of PaliGemma, without degrading task performance.

4. **Benchmark and validate** the proposed approach on standard multimodal datasets (VQAv2 / COCO Captions), comparing bias scores and task accuracy before and after intervention.

---

## Plan of Action

| Phase | Task | Timeline |
|---|---|---|
| **Phase 1** | Literature review; baseline setup; load PaliGemma-3B on COCO/VQAv2 | Week 1–2 |
| **Phase 2** | Implement bias detection: extract per-layer attention weights, compute image vs. text attention mass ratio, generate heatmaps | Week 3–4 |
| **Phase 3** | Implement Integrated Gradients attribution (via Captum); compare with attention-based scores; quantify bias on 500+ samples | Week 5–6 |
| **Phase 4** | Design and integrate Balanced Modal Attention (BMA) layer; implement bias regularization loss `R_bias` | Week 7–8 |
| **Phase 5** | Fine-tune with BMA + regularization; evaluate accuracy vs. bias score tradeoff | Week 9–10 |
| **Phase 6** | Analysis, ablations, visualizations, report writing | Week 11–12 |

---

## Proposed Methodology

**Step 1 — Baseline Bias Measurement:**
Using PaliGemma-3B's attention outputs, we define the *Modality Bias Score (MBS)*:

> `MBS = Σ(attention on image tokens) / Σ(all attention weights)`

An MBS near 0 indicates language dominance; near 1 indicates vision dominance. A fair model should trend toward 0.5.

**Step 2 — XAI Attribution (Integrated Gradients):**
We apply Integrated Gradients on the fused token embeddings to compute true input-level attribution per modality, providing a more faithful measure of modality contribution than raw attention.

**Step 3 — Balanced Modal Attention (BMA) Layer:**
A lightweight learnable gate `α` is inserted into the cross-attention layers:

> `Attn_balanced = α · Attn_image + (1 − α) · Attn_text`

`α` is trained using the bias regularization term: `R_bias = (MBS − 0.5)²`, penalizing the model when one modality dominates.

**Step 4 — Evaluation:**
We report VQA accuracy, BLEU score (captioning), MBS distribution, and per-group fairness on COCO to measure the impact of the BMA layer.

---

## Expected Outcomes

- A working modality bias detection pipeline with quantitative metrics and XAI visualizations
- Empirical evidence on whether XAI attribution scores can serve as a bias mitigation signal
- A novel, plug-and-play Balanced Modal Attention layer that demonstrably reduces modality dominance
- A comparative analysis showing the accuracy–fairness tradeoff with and without bias correction

---

## Tools & Stack

Python · PyTorch · HuggingFace Transformers · Captum (XAI) · COCO / VQAv2 datasets · Google Colab (T4/A100 GPU) · PaliGemma-3B-pt-224

---

## References

1. *A Multimodal XAI Framework for Trustworthy CNNs* — arXiv:2510.12957
2. *MLLMs are Deeply Affected by Modality Bias* — arXiv:2505.18657
3. *The Multimodal Paradox* — arXiv:2505.03020
