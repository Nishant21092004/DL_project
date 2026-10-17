/* ============ PhoolWala — checkout logic ============ */
(function () {
  "use strict";

  const STORE_KEY = "phoolwala_cart_v1";
  const FREE_DELIVERY_ABOVE = 499;
  const DELIVERY_FEE = 49;

  const STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa",
    "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
    "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman & Nicobar Islands", "Chandigarh", "Dadra & Nagar Haveli and Daman & Diu",
    "Delhi (NCT)", "Jammu & Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
  ];

  // pincode first digit → delivery zone & days
  const PIN_ZONES = {
    1: "Delhi, Haryana, Punjab, HP, J&K (North)",
    2: "Uttar Pradesh, Uttarakhand",
    3: "Rajasthan, Gujarat, Daman",
    4: "Maharashtra, MP, Chhattisgarh, Goa",
    5: "Telangana, Andhra Pradesh, Karnataka",
    6: "Tamil Nadu, Kerala, Puducherry",
    7: "West Bengal, Odisha, North-East",
    8: "Bihar, Jharkhand",
  };
  const PIN_DAYS = { 1: 2, 2: 3, 3: 3, 4: 3, 5: 3, 6: 4, 7: 5, 8: 4 };

  const $ = (s) => document.querySelector(s);
  const fmt = (n) => "₹" + n.toLocaleString("en-IN");
  const bySlug = Object.fromEntries(PRODUCTS.map((p) => [p.slug, p]));

  let cart = loadCart();
  function loadCart() {
    try { return JSON.parse(localStorage.getItem(STORE_KEY)) || {}; } catch (e) { return {}; }
  }
  function saveCart() { localStorage.setItem(STORE_KEY, JSON.stringify(cart)); }
  function entries() { return Object.entries(cart).filter(([s]) => bySlug[s]); }
  function subtotal() { return entries().reduce((s, [slug, q]) => s + bySlug[slug].price * q, 0); }
  function mrpTotal() { return entries().reduce((s, [slug, q]) => s + bySlug[slug].mrp * q, 0); }

  /* ---------------- toast ---------------- */
  let toastTimer;
  function toast(msg) {
    const t = $("#toast");
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove("show"), 2400);
  }

  /* ---------------- states dropdown ---------------- */
  const stateSel = $("#in-state");
  STATES.forEach((s) => {
    const o = document.createElement("option");
    o.textContent = s;
    stateSel.appendChild(o);
  });

  /* ---------------- summary ---------------- */
  function renderSummary() {
    const wrap = $("#sumItems");
    const list = entries();
    if (!list.length) {
      wrap.innerHTML = `<div class="empty-cart" style="padding:20px"><div class="big">🌼</div><b>Your cart is empty</b><p><a href="index.html" style="color:var(--green-dark);font-weight:700">← Back to shopping</a></p></div>`;
      $("#placeOrder").style.display = "none";
      return;
    }
    $("#placeOrder").style.display = "";
    wrap.innerHTML = list.map(([slug, q]) => {
      const p = bySlug[slug];
      return `
        <div class="sum-item">
          <img src="${p.images[0]}" alt="${p.name}">
          <div>
            <div class="nm">${p.name}</div>
            <div class="qt">Qty:
              <span class="qty" style="display:inline-flex;margin-left:6px">
                <button data-dec="${slug}">−</button><span>${q}</span><button data-inc="${slug}">+</button>
              </span>
            </div>
          </div>
          <div class="amt">${fmt(p.price * q)}</div>
        </div>`;
    }).join("");
    $$("#sumItems [data-inc]").forEach((b) => b.addEventListener("click", () => { cart[b.dataset.inc]++; saveCart(); renderSummary(); }));
    $$("#sumItems [data-dec]").forEach((b) => b.addEventListener("click", () => {
      const s = b.dataset.dec;
      cart[s]--; if (cart[s] <= 0) delete cart[s];
      saveCart(); renderSummary();
    }));

    const sub = subtotal();
    const fee = sub >= FREE_DELIVERY_ABOVE ? 0 : DELIVERY_FEE;
    $("#sumSub").textContent = fmt(sub);
    $("#sumDel").textContent = fee === 0 ? "FREE 🎉" : fmt(fee);
    $("#sumSave").textContent = fmt(mrpTotal() - sub + (sub && fee ? 0 : 0));
    $("#sumTotal").textContent = fmt(sub + fee);
  }

  /* ---------------- pincode → ETA ---------------- */
  const pinInput = $("#in-pincode");
  pinInput.addEventListener("input", () => {
    pinInput.value = pinInput.value.replace(/\D/g, "").slice(0, 6);
    const eta = $("#etaBox");
    if (pinInput.value.length === 6) {
      const d = +pinInput.value[0];
      const zone = PIN_ZONES[d] || "your region";
      const days = PIN_DAYS[d] || 5;
      const from = new Date(Date.now() + days * 864e5).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
      const to = new Date(Date.now() + (days + 2) * 864e5).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
      eta.innerHTML = `🚚 <b>Delivery available!</b> Estimated delivery to ${zone}: <b>${from} – ${to}</b> (${days}–${days + 2} days)`;
      eta.classList.add("show");
    } else {
      eta.classList.remove("show");
    }
  });

  /* ---------------- input formatting ---------------- */
  const phoneInput = $("#in-phone");
  phoneInput.addEventListener("input", () => { phoneInput.value = phoneInput.value.replace(/\D/g, "").slice(0, 10); });

  const cardInput = $("#in-cardnum");
  cardInput.addEventListener("input", () => {
    const v = cardInput.value.replace(/\D/g, "").slice(0, 16);
    cardInput.value = v.replace(/(\d{4})(?=\d)/g, "$1 ");
  });
  const expInput = $("#in-exp");
  expInput.addEventListener("input", () => {
    let v = expInput.value.replace(/\D/g, "").slice(0, 4);
    if (v.length > 2) v = v.slice(0, 2) + "/" + v.slice(2);
    expInput.value = v;
  });
  const cvvInput = $("#in-cvv");
  cvvInput.addEventListener("input", () => { cvvInput.value = cvvInput.value.replace(/\D/g, "").slice(0, 3); });

  /* ---------------- validation ---------------- */
  function setErr(fieldId, on) {
    const f = $("#" + fieldId);
    if (f) f.classList.toggle("error", !!on);
    return !on;
  }
  function markErrors(errors) {
    // errors: {fieldId: true}
    Object.entries(errors).forEach(([id, bad]) => setErr(id, bad));
    const firstBad = Object.keys(errors).find((id) => errors[id] && $("#" + id));
    if (firstBad) {
      const el = $("#" + firstBad).scrollIntoView({ behavior: "smooth", block: "center" });
    }
    return !Object.values(errors).some(Boolean);
  }
  function clearAllErrors() {
    $$(".field.error").forEach((f) => f.classList.remove("error"));
  }
  // live clearing
  ["in-name", "in-phone", "in-pincode", "in-city", "in-address", "in-upi", "in-cardnum", "in-exp", "in-cvv", "in-cardname"].forEach((id) => {
    const el = $("#" + id);
    if (el) el.addEventListener("input", () => { const f = el.closest(".field"); if (f) f.classList.remove("error"); });
  });
  stateSel.addEventListener("change", () => setErr("f-state", false));
  $("#in-bank").addEventListener("change", () => setErr("f-bank", false));

  function validateAddress() {
    const name = $("#in-name").value.trim();
    const phone = $("#in-phone").value.trim();
    const pin = $("#in-pincode").value.trim();
    const city = $("#in-city").value.trim();
    const addr = $("#in-address").value.trim();
    return markErrors({
      "f-name": name.length < 3,
      "f-phone": !/^[6-9]\d{9}$/.test(phone),
      "f-pincode": !/^[1-9]\d{5}$/.test(pin),
      "f-state": !stateSel.value,
      "f-city": city.length < 2,
      "f-address": addr.length < 10,
    });
  }

  function currentPayMethod() {
    return document.querySelector('input[name="pay"]:checked').value;
  }
  const PAY_LABEL = {
    cod: "Cash on Delivery",
    upi: "UPI",
    card: "Debit / Credit Card",
    netbanking: "Net Banking",
  };

  function validatePayment() {
    const m = currentPayMethod();
    if (m === "cod") return true;
    if (m === "upi") {
      const upi = $("#in-upi").value.trim();
      return markErrors({ "f-upi": !/^[\w.\-]{3,}@[a-zA-Z]{3,}$/.test(upi) });
    }
    if (m === "card") {
      const num = $("#in-cardnum").value.replace(/\s/g, "");
      const exp = $("#in-exp").value;
      const cvv = $("#in-cvv").value;
      const cname = $("#in-cardname").value.trim();
      let expOk = /^\d{2}\/\d{2}$/.test(exp);
      if (expOk) {
        const [mm, yy] = exp.split("/").map(Number);
        const now = new Date();
        expOk = mm >= 1 && mm <= 12 && (2000 + yy > now.getFullYear() || (2000 + yy === now.getFullYear() && mm >= now.getMonth() + 1));
      }
      return markErrors({
        "f-cardnum": !/^\d{16}$/.test(num),
        "f-exp": !expOk,
        "f-cvv": !/^\d{3}$/.test(cvv),
        "f-cardname": cname.length < 3,
      });
    }
    if (m === "netbanking") {
      return markErrors({ "f-bank": !$("#in-bank").value });
    }
    return true;
  }

  /* ---------------- place order ---------------- */
  const placeBtn = $("#placeOrder");
  placeBtn.addEventListener("click", () => {
    if (!entries().length) { toast("Your cart is empty 🌼"); return; }
    clearAllErrors();
    const addrOk = validateAddress();
    const payOk = validatePayment();
    if (!addrOk || !payOk) {
      placeBtn.classList.remove("shake");
      void placeBtn.offsetWidth;
      placeBtn.classList.add("shake");
      toast("Please fill the highlighted details ⚠️");
      return;
    }
    // simulate payment processing
    placeBtn.disabled = true;
    placeBtn.innerHTML = `<span class="spinner"></span> ${currentPayMethod() === "cod" ? "Placing your order…" : "Processing payment…"}`;
    setTimeout(() => {
      placeOrder();
    }, 1500);
  });

  function placeOrder() {
    const sub = subtotal();
    const fee = sub >= FREE_DELIVERY_ABOVE ? 0 : DELIVERY_FEE;
    const total = sub + fee;
    const pin = $("#in-pincode").value.trim();
    const days = PIN_DAYS[+pin[0]] || 5;
    const from = new Date(Date.now() + days * 864e5).toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short" });
    const to = new Date(Date.now() + (days + 2) * 864e5).toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short" });
    const orderId = "PW" + String(Date.now()).slice(-6) + String(Math.floor(Math.random() * 90) + 10);

    const order = {
      id: orderId,
      items: entries().map(([slug, q]) => ({ name: bySlug[slug].name, qty: q, price: bySlug[slug].price })),
      total,
      payment: PAY_LABEL[currentPayMethod()],
      name: $("#in-name").value.trim(),
      phone: $("#in-phone").value.trim(),
      address: `${$("#in-address").value.trim()}, ${$("#in-city").value.trim()}, ${stateSel.value} — ${pin}` + ($("#in-landmark").value.trim() ? ` (Landmark: ${$("#in-landmark").value.trim()})` : ""),
      etaFrom: from, etaTo: to,
      placedAt: new Date().toLocaleString("en-IN"),
    };
    try { localStorage.setItem("phoolwala_last_order", JSON.stringify(order)); } catch (e) {}

    // clear cart
    cart = {};
    saveCart();

    // render success
    $("#checkoutMain").style.display = "none";
    const s = $("#successScreen");
    s.style.display = "";
    s.innerHTML = `
      <div class="steps">
        <span class="step done"><span class="n">✓</span> Cart</span><span class="sep">——</span>
        <span class="step done"><span class="n">✓</span> Delivery &amp; Payment</span><span class="sep">——</span>
        <span class="step active"><span class="n">✓</span> Order Placed</span>
      </div>
      <div class="success-card">
        <div class="success-check">✓</div>
        <h2>Order Placed Successfully! 🎉</h2>
        <div class="oid">Order ID: <b>${order.id}</b> &nbsp;•&nbsp; ${order.placedAt}</div>
        <div class="success-eta">🚚 Arriving between <b>${order.etaFrom}</b> and <b>${order.etaTo}</b><br><small style="font-weight:600">Delivering to your address in ${stateSel.value} 🇮🇳</small></div>
        <div class="success-details">
          <div class="row"><span>Deliver to</span><b>${order.name} • ${order.phone}</b></div>
          <div class="row"><span>Address</span><b>${order.address}</b></div>
          <div class="row"><span>Payment</span><b>${order.payment}${order.payment === "UPI" || order.payment === "Debit / Credit Card" || order.payment === "Net Banking" ? " ✅ Paid" : ""}</b></div>
          <div class="row"><span>Items</span><b>${order.items.reduce((a, i) => a + i.qty, 0)} item(s)</b></div>
          <div class="row"><span>Total Paid</span><b>${fmt(order.total)}</b></div>
        </div>
        <div style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap">
          <a class="btn btn-primary" href="index.html">Continue Shopping 🌸</a>
        </div>
        <div class="secure-line" style="margin-top:16px">A confirmation SMS will be sent to your mobile number 📱</div>
      </div>`;
    window.scrollTo({ top: 0, behavior: "smooth" });
    toast("Order placed successfully! 🎉");
  }

  /* ---------------- init ---------------- */
  renderSummary();
})();
