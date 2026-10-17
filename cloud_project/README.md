# 🌸 PhoolWala — Online Flower & Plant Store

A fully-responsive e-commerce demo website for buying **fresh flowers, potted plants and bouquets**, built as a **Cloud Computing course project**. Zero frameworks, zero dependencies — pure HTML + CSS + JavaScript, so it runs anywhere (laptop, GitHub Pages, S3, any static cloud host).

**⭐ Live on GitHub Pages:** `https://nishant21092004.github.io/cloud_project/`

---

## ✨ Features

### Shopping
- **114 products** — 52 flowers, 41 plants, 21 bouquets, each with **3–4 real photos**
- **Real flower images** sourced from public web photography (stock/nursery/product photos)
- **Hover slideshow** — hover on any product card and its 3–4 photos auto-cycle like a mini slideshow (with dots + fade animation); click for full Quick View gallery with arrows & thumbnails
- **Live search** with Hindi tags — try `gulab`, `genda`, `surajmukhi`, `mogra`, `tulsi`, `kamal`, `rajnigandha`…
- **Smart "Out of Stock" search result** — search something we don't sell (e.g. `blue rose`) and instead of "no results", you get a proper **"Out of Stock" card with image** + bestseller suggestions
- Category tabs (All / Flowers / Plants / Bouquets), sorting (popularity, price, name), ratings & discount badges
- Cart drawer with quantity control, **free-delivery progress bar** (₹499 threshold), saved in `localStorage`

### Checkout
- **Delivery across ALL of India** 🇮🇳 — full form with all **28 states + 8 UTs**, 6-digit pincode validation and **auto delivery estimate by pincode zone** (2–7 days)
- **Multiple payment options** (not just COD!):
  - 💵 **Cash on Delivery**
  - 📱 **UPI** (GPay / PhonePe / Paytm — UPI ID validation)
  - 💳 **Debit / Credit Card** (16-digit formatting, expiry & CVV validation)
  - 🏦 **Net Banking** (all major Indian banks)
- **Working "Place Order" button** — validates the form, shows inline errors, simulates payment, and renders a full **order-confirmation screen** with Order ID, delivery dates & address summary

## 📁 Project Structure

```
cloud_project/
├── index.html          # Shop page (hero, search, filters, product grid, cart drawer)
├── checkout.html       # Address form + payment methods + order summary
├── css/style.css       # Complete responsive styling
├── js/
│   ├── products.js     # 114-product catalogue (auto-generated)
│   ├── app.js          # Grid, hover slideshow, search, cart, quick view
│   └── checkout.js     # Validation, payment, place order, success screen
├── assets/
│   ├── hero.jpg
│   ├── out-of-stock.jpg
│   └── products/       # 459 product photos (114 folders × 3–4 images)
└── tools/              # Image pipeline + data generator (dev-only)
```

## 🚀 Run Locally

**Option 1 — just open it:** double-click `index.html`.

**Option 2 — local server (recommended):**
```bash
cd cloud_project
python3 -m http.server 8080
# open http://localhost:8080
```

## ☁️ Cloud Deployment (for the CC course project)

1. **GitHub Pages** (already configured):
   ```bash
   git clone https://github.com/Nishant21092004/cloud_project.git
   ```
   The repo has Pages enabled from the `main` branch → live at
   `https://nishant21092004.github.io/cloud_project/`

2. **AWS S3 static hosting:** upload the folder contents to a bucket, enable *Static website hosting* (index: `index.html`).

3. **Netlify / Vercel:** drag-and-drop the folder — zero build settings needed.

## 🛠️ How the images were built

`tools/img_manifest.txt` lists 114 products + their search queries.
`tools/process_images.py` downloads → validates → center-crops (4:3) → resizes (800×600) → compresses every photo into `assets/products/<slug>/1..4.jpg`.
`tools/build_products.py` generates `js/products.js` from the product spec + the actual images on disk.

Re-generate any time:
```bash
python3 tools/build_products.py
```

## 📝 Notes

- Demo store for a college project — **payments are simulated**, no real gateway is connected.
- Product photos were collected from public web sources via image search for educational use.
