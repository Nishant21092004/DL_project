# Monday review — likely questions + crisp answers (Hinglish)

> Sir keh rahe hain implementation dekhenge aur poochhenge. Ye doc hai "jaldi se revise karne ke liye" —
> har answer ke saath reference hai ki code/docs me kahan dikhega. Equations paper
> (`docs/Wei2024_On-the-fly_Modulation_TPAMI.pdf`) ke numbering se hain; notes:
> `docs/OGM_OPM_Explanation.pdf`.

---

## A. Concepts — "modality bias hota kya hai"

**Q1. Modality bias / imbalance samjhao.**
Joint training me fusion logit **sum** hota hai: `f = W¹φ¹ + W²φ² + b` (Eq 2). Jo modality
zyada discriminative hoti hai, uska contribution bada → usi ka gradient `∂ℓ/∂f = softmax(f) − 1[y]`
(Eq 5) seedha usi encoder ko push karta hai → **rich-get-richer**: ek modality dominate karne
lagti hai, doosri underfit. Paper ka observation: gradient ka direction ek hi modality decide
karta hai.
*Code:* `bml/modulation.py` (Eq 6/7 ρ), `bml/engine.py` (Alg 1/2 order).

**Q2. Bias hai ya phir wahi hota hai ki ek modality strong hai?**
Strong hona alag baat hai — **imbalance** tab hai jab training me *consistently* ek hi ka
contribution badhta jaye. Measure karte hain **discrepancy ratio ρ** (Eq 6/7): 1 = balanced,
>1 = pehli modality dominant. Hamare synthetic runs me `none` pe ρ_image ≈ 1.3–1.4 rehta hai,
modulation ke baad ≈ 1.1–1.2.
*Output:* `results/RESULTS.md`, `balanced_mm/runs/curves.png`.

**Q3. Bias ko detect kaise karo? (XAI wala part)**
Hamare proposal ke hisaab se teen tarike, repo me teeno implemented:
1. **Uni-modal probe** — frozen encoder pe linear classifier; jiska acc kam uska encoder
   weak (`train.py --probe`, paper footnote 1).
2. **Attention / Integrated Gradients** — model *kahan dekh raha hai* (`bml/xai.py`:
   `integrated_gradients_image`, `token_importance_text`, `modality_attribution`).
3. **ρ ratio** — optimization-side signal, bina kisi extra model ke (Eq 6/7).

**Q4. Uni-modal baselines ka point?**
`--only image` / `--only text` se pata chalta hai fusion **actually** kar kya raha hai.
Hamare results: image-only 0.715, text-only 0.738 → fusion 0.885 (≈ +15 pts). Matlab fusion
sach me dono use kar raha hai; modulation usko aur balanced banata hai.
*Output:* `results/RESULTS.md` → "Uni-modal baselines" table.

---

## B. Math — equations jo poochi ja sakti hain

**Q5. Eq 6/7 — score kaise banta hai?**
Per block: `s^m_i = softmax(W^m φ^m_i + b/M)_{y_i}` — i.e. **sirf modality m ke contribution**
ka true-class probability (bias b/M share hota hai).
`ρ^m = (1/(M−1)) Σ_{j≠m} (Σ_i s^m_i) / (Σ_i s^j_i)` — dominant modality ka score doosre se
kitna bara (batch-averaged). ρ=1 → balance.
*Code:* `discrepancy_ratios()` + `unimodal_scores_from_logits()` in `bml/modulation.py` (no_grad).

**Q6. ρ se modulation factor kaise milta hai?**
`z = tanh(ρ − 1)` — saturating, sign rakhta hai (ρ>1 → z>0).

- **OPM (Eq 8):** dominant modality ke samples ko **randomly drop** karta hai training forward me:
  `q^m = q_base·(1 + λ·z)` probability se feature zero (sirf tab jab ρ>1; drop = `q/2` rate se
  Bernoulli, no rescale). Doosre modality ka gradient ≈ free pass milta hai.
- **OGM-GE (Eq 11/12):** dominant modality ke **encoder parameters** ke gradients ko scale:
  `k^m = 1 − α·z` (jab ρ>1, doosre modality ka k=1). Gradient badhta nahi — sirf *kam* hota hai
  (k ∈ [0,1]) → train stability.
- **GE (Eq 16/17):** OGM ke baad un sabhi parameters me Gaussian noise add jo `std(grad)` se aata
  hai → dono modalities ke gradients ka **ratio** preserve rehta hai + regularization milta hai.
  `(k²+1) × noise` factor paper me derive hota hai.
*Code:* `OPM`, `OGMGE`, `BalancedModulator` in `bml/modulation.py`; hooks `before_fusion` /
`after_backward` in `bml/engine.py`.

**Q7. Defaults / hyper-parameters?**
`q_base = λ = α = 0.5`, `z = tanh`, SGD momentum 0.9 (paper recommendation: OGM ko momentum
SGD chahiye; OPM Adam/SGD dono chalta hai). Sab flags se changeable:
`train.py --q_base --lam --alpha --z --mod_start --mod_end`.

**Q8. Overhead kitna hai?**
ρ nikalne ke liye **sirf ek no-grad pass** over block logits (linear head me exact, cheap);
OPM forward me ek Bernoulli mask; OGM backward me element-wise grad multiply + optional noise.
FLOPs pe ~0 overhead, memory me batch ka ek extra tuple (`last_unimodal_logits`).
Paper me bhi inference pe **zero cost** (modulation training-time only).

**Q9. ρ>1 wali condition kyu?**
Agar kisi ki bhi ρ<1 (wo dominant nahi) to usse **kuch nahi karna** — sirf dominant modality ko
rokna hai. Isliye `if ρ>1: apply else: q=0 / k=1`. Agle step ρ phir measure hota hai (Alg 1/2).

---

## C. Code — "yeh file kya karti hai"

**Q10. Repo ka map (30 sec me):**
| File | Kaam |
|---|---|
| `bml/modulation.py` | Eq 6/7 ρ + OPM (Eq 8) + OGM-GE (Eq 11/17) + `BalancedModulator` — **standalone, kahin bhi plug-in** |
| `bml/engine.py` | training/eval loops — Alg 1/2 ka exact order (encode → before_fusion → CE → after_backward → step) |
| `bml/models.py` | ResNet-18 / SmallCNN image encoder, Transformer/HF text, late-fusion head + block logits |
| `bml/data.py` | CSV pipeline (`image,text,label`) + synthetic imbalance dataset |
| `bml/xai.py` | **detection side**: IG, grad×input tokens, modality attribution shares |
| `bml/metrics.py` | confusion matrix, per-class acc, macro-F1, ECE |
| `bml/analysis.py` + `scripts/make_report.py` | runs → `results/RESULTS.md` + plots (auto report) |
| `train.py / eval.py / compare.py` | CLI training, checkpoint eval, multi-run table |
| `tests/` | 27 unit tests (`python -m pytest tests/`) |
| `notebooks/01_walkthrough.ipynb` | 4-epoch demo + plots + XAI attribution — **Preview tab me code + output dono** |

**Q11. Modulation lagane ka exact order?**
```
feats = model.encode(inputs)                    # ek baar forward
feats, rho = modulator.before_fusion(...)       # ρ (Eq 6/7), OPM drop, ρ update
logits = model.fuse(feats); loss.backward()
modulator.after_backward(model.modality_parameters(), epoch)   # OGM: grad × k (+ GE noise)
optimizer.step()
```
*Proof:* `bml/engine.py` docstring + `train_one_epoch()`.

**Q12. Drop ka matlab output zero ho gayi to agla layer?**
OPM drop **training forward** me hota hai (batch ke kuch samples me), aur linear head ke paas
bias `b/M` hota hi hai → NaN/undefined nahi. Eval/val me drop **nahi** hota (modulator eval
mode me pass-through) — isliye val acc inflated nahi hota.

**Q13. OPM aur OGM me difference?**
| | OPM | OGM-GE |
|---|---|---|
| kya badalta hai | forward — dominant samples ka **feature drop** | backward — dominant encoder ka **grad scale** |
| granularity | per-sample, random | poore modality parameters par constant factor |
| noise | nahi | GE Gaussian (Eq 17) |
| combo dono chalta hai? | haan — `--modulation both` (humne 4 configs chalayi hain) | |

---

## D. Experiments — numbers jo yaad rakhne hain

**Q14. Synthetic data kaisa hai?**
6 classes; har sample ka text **prob 0.7** pe class-keyword (uske baad synonyms) rakhta hai,
image **prob 0.7** pe class-patch rakhti hai (baaki noise). Modality-wise informative
probability hi **imbalance ka source** (aur `--syn_synonyms 6` se severe). 2400 train / 600 val,
64×64 images, SmallCNN + 2-layer Transformer, SGD lr 0.01, 15 epochs, seed sweep {0,1,2}.

**Q15. Main result?**
`results/RESULTS.md` (auto-generated, mean ± std over seeds {0,1,2}):
- fusion: **none 0.887 ± 0.022 → OGM 0.898 → OPM 0.904 → both 0.906 ± 0.025** (har seed me same ordering)
- ρ_image: none 1.34 → both **1.12** (bias kam hua, acc upar)
- uni baselines: image 0.715 / text 0.738 — fusion +15 pts
- stress (`--syn_synonyms 6`): none ρ 4.8 → OPM 2.3
Paper (real datasets, Concat→OPM/OGM/both): CREMA-D 66.9→75.1/74.6/76.7 etc. — hamara code
wahi method, Text+Image setting me.

**Q16. "Output kam hai" — repo me kya dekhna hai?**
1. `results/RESULTS.md` + `results/*.png` — mean±std tables + curves (auto-generated)
2. `balanced_mm/runs/` — har run ka `train.log`, `history.json`, `summary.json` + `compare_log.txt`
3. `notebooks/01_walkthrough.ipynb` — executed notebook (Preview me output ke saath)
4. `tests/` — 27 tests green

**Q17. Ye kyu credible hai — one seed nahi?**
3 seeds {0,1,2} × 4 methods = 12 runs; tables me mean ± std. Script:
`bash scripts/run_seed_sweep.sh` → `python scripts/make_report.py`.

**Q18. Limitation bolo pehle (impress karta hai):**
- abhi synthetic benchmark (imbalance controlled) — **next step**: real dataset
  (proposal wala domain) + ResNet-18/HF encoders (`--pretrained_image --text_encoder hf`)
- modulation mitigation ka part hai; **detection/XAI** side hamare proposal ka MBS + IG hai
  (`bml/xai.py`) — dono milke "detect → mitigate" pipeline banate hain.

---

## E. Proposal se connection (link to project title)

**Q19. Hamare XAI proposal se ye paper kaise relate hota hai?**
Proposal: *"XAI-Driven Modality Bias **Detection** and Mitigation"*.
- **Detection:** attention heat-maps (Colab notebook) + Integrated Gradients + MBS score →
  *where* model dekh raha hai; ρ + probe → *how strongly* ek modality dominate.
- **Mitigation:** training-time modulation (OPM/OGM-GE) — TPAMI 2024 ka strong baseline jo
  humne implement kiya; aage "Balanced Modal Attention" (proposal ka apna idea) isi ke
  comparison me aayega.
*Flow:* detect (XAI) → quantify (ρ) → mitigate (modulation) → verify (probe, curves).

**Q20. PaliGemma 3B kahan gaya? (unofficially poochhenge)**
`multimodal (2).ipynb` me loading + prompt demo + attention heat-map hai (Colab GPU).
End-to-end modulation 3B pe Colab free tier me possible nahi isliye **method ko chhota karke**
Text+Image late-fusion pe validate kiya (repo ka `balanced_mm/`) — method same, compute feasible.
Aage ka plan: detection scores (MBS/IG) ko modulation ke saath jodna.

---

## Quick revise (last-minute)

1. `f = Σ W^m φ^m + b` → softmax − y gradient → strong modality ko zyada push
2. ρ (Eq 6/7) = score ratio, 1 = balanced
3. `z = tanh(ρ−1)`; OPM = drop, OGM = grad×k, GE = noise (Eq 17); `both` sabse best
4. Repo map: modulation.py / engine.py / xai.py / analysis.py / tests / notebook
5. Numbers: none 0.885 → both ≈ 0.908; ρ 1.45 → 1.13; uni 0.715/0.738; 3 seeds
6. Limitation + next step ready rakho
