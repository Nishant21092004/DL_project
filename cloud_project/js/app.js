/* ============ PhoolWala — shop page logic ============ */
(function () {
  "use strict";

  const STORE_KEY = "phoolwala_cart_v1";
  const FREE_DELIVERY_ABOVE = 499;
  const DELIVERY_FEE = 49;

  const $ = (s) => document.querySelector(s);
  const $$ = (s) => [...document.querySelectorAll(s)];
  const fmt = (n) => "₹" + n.toLocaleString("en-IN");
  const bySlug = Object.fromEntries(PRODUCTS.map((p) => [p.slug, p]));

  let state = { q: "", cat: "all", sort: "popular" };
  let cart = loadCart();

  /* ---------------- cart helpers ---------------- */
  function loadCart() {
    try { return JSON.parse(localStorage.getItem(STORE_KEY)) || {}; }
    catch (e) { return {}; }
  }
  function saveCart() {
    localStorage.setItem(STORE_KEY, JSON.stringify(cart));
    updateBadge();
  }
  function cartCount() { return Object.values(cart).reduce((a, b) => a + b, 0); }
  function cartSubtotal() {
    return Object.entries(cart).reduce((sum, [slug, q]) => {
      const p = bySlug[slug];
      return p ? sum + p.price * q : sum;
    }, 0);
  }
  function updateBadge() {
    const b = $("#cartBadge");
    b.textContent = cartCount();
    b.classList.remove("pop");
    void b.offsetWidth; // restart animation
    b.classList.add("pop");
  }

  /* ---------------- toast ---------------- */
  let toastTimer;
  function toast(msg) {
    const t = $("#toast");
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove("show"), 2200);
  }

  /* ---------------- filtering ---------------- */
  function haystack(p) {
    return (p.name + " " + p.tags + " " + p.category + " " + p.desc).toLowerCase();
  }
  function matches(p, q) {
    if (!q) return true;
    const hay = haystack(p);
    return q.toLowerCase().split(/\s+/).filter(Boolean).every((t) => hay.includes(t));
  }
  function filtered() {
    let list = PRODUCTS.filter((p) => (state.cat === "all" || p.category === state.cat) && matches(p, state.q));
    switch (state.sort) {
      case "price-asc": list = list.slice().sort((a, b) => a.price - b.price); break;
      case "price-desc": list = list.slice().sort((a, b) => b.price - a.price); break;
      case "name": list = list.slice().sort((a, b) => a.name.localeCompare(b.name)); break;
      default: list = list.slice().sort((a, b) => b.rating - a.rating || b.reviews - a.reviews);
    }
    return list;
  }

  /* ---------------- rendering ---------------- */
  const CAT_LABEL = { flowers: "Flower", plants: "Plant", bouquets: "Bouquet" };

  function cardHTML(p) {
    const off = Math.round((1 - p.price / p.mrp) * 100);
    const badge = p.badge
      ? `<span class="p-badge ${p.badge.toLowerCase()}">${p.badge}</span>` : "";
    const dots = p.images.length > 1
      ? `<div class="dots">${p.images.map((_, i) => `<span class="dot${i === 0 ? " active" : ""}"></span>`).join("")}</div>`
      : "";
    return `
      <article class="card" data-slug="${p.slug}">
        <div class="card-media" data-images='${JSON.stringify(p.images)}'>
          ${badge}
          <img src="${p.images[0]}" alt="${p.name}" loading="lazy">
          ${dots}
          <button class="quick-view-btn">👁 Quick View (${p.images.length} photos)</button>
        </div>
        <div class="card-body">
          <span class="card-cat">${CAT_LABEL[p.category]}</span>
          <div class="card-name">${p.name}</div>
          <div class="card-meta"><span class="stars">${"★".repeat(Math.round(p.rating))}${"☆".repeat(5 - Math.round(p.rating))}</span> ${p.rating} <span>(${p.reviews})</span></div>
          <div class="card-price"><b>${fmt(p.price)}</b><s>${fmt(p.mrp)}</s><span class="off">${off}% off</span></div>
          <button class="add-btn" data-add="${p.slug}">Add to Cart 🛒</button>
        </div>
      </article>`;
  }

  function render() {
    const grid = $("#grid");
    const list = filtered();
    const searched = state.q.trim().length > 0;
    const showOOS = searched && list.length === 0;

    $("#oosCard").style.display = showOOS ? "" : "none";
    if (showOOS) {
      const q = state.q.trim();
      $("#oosQuery").textContent = q;
      $("#oosQuery2").textContent = '"' + q + '"';
      // show bestsellers as suggestions inside the grid
      const best = PRODUCTS.filter((p) => p.badge).slice(0, 8);
      grid.innerHTML = best.map(cardHTML).join("");
      $("#resultCount").textContent = "No match for your search — showing our bestsellers instead";
    } else {
      grid.innerHTML = list.map(cardHTML).join("");
      $("#resultCount").textContent = `${list.length} product${list.length === 1 ? "" : "s"}` +
        (state.cat === "all" ? "" : ` in ${state.cat}`);
    }
    bindCards();
  }

  /* ---------------- card events (hover slideshow + actions) ---------------- */
  function bindCards() {
    $$("#grid .card").forEach((card) => {
      const p = bySlug[card.dataset.slug];
      // preload all gallery images for a smooth slideshow
      p.images.forEach((src) => { const im = new Image(); im.src = src; });

      const media = card.querySelector(".card-media");
      const img = media.querySelector("img");
      const dots = [...media.querySelectorAll(".dot")];
      let idx = 0, timer = null;

      const show = (i, instant) => {
        idx = i;
        if (instant) {
          img.src = p.images[i];
        } else {
          img.classList.add("fading");
          setTimeout(() => { img.src = p.images[idx]; img.classList.remove("fading"); }, 170);
        }
        dots.forEach((d, j) => d.classList.toggle("active", j === i));
      };

      if (p.images.length > 1) {
        media.addEventListener("mouseenter", () => {
          timer = setInterval(() => show((idx + 1) % p.images.length), 1100);
        });
        media.addEventListener("mouseleave", () => {
          clearInterval(timer);
          show(0, true);
        });
      }
      media.addEventListener("click", () => openModal(p));
    });

    $$("#grid [data-add]").forEach((btn) =>
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        addToCart(btn.dataset.add, 1);
      })
    );
  }

  /* ---------------- cart actions ---------------- */
  function addToCart(slug, qty) {
    const p = bySlug[slug];
    if (!p) return;
    cart[slug] = (cart[slug] || 0) + qty;
    saveCart();
    renderDrawer();
    toast(`Added ${p.name} × ${cart[slug]} 🌸`);
  }
  function setQty(slug, qty) {
    if (qty <= 0) delete cart[slug]; else cart[slug] = qty;
    saveCart();
    renderDrawer();
    renderCheckoutButtonState();
  }

  function renderDrawer() {
    const wrap = $("#drawerItems");
    const entries = Object.entries(cart).filter(([s]) => bySlug[s]);
    if (!entries.length) {
      wrap.innerHTML = `<div class="empty-cart"><div class="big">🌼</div><b>Your cart is empty</b><p>Add some flowers or plants to get started!</p></div>`;
    } else {
      wrap.innerHTML = entries.map(([slug, q]) => {
        const p = bySlug[slug];
        return `
        <div class="cart-item">
          <img src="${p.images[0]}" alt="${p.name}">
          <div>
            <div class="nm">${p.name}</div>
            <div class="pr">${fmt(p.price)} <small style="color:var(--muted)">× ${q} = ${fmt(p.price * q)}</small></div>
            <div style="display:flex;align-items:center;gap:10px;margin-top:6px">
              <span class="qty">
                <button data-dec="${slug}">−</button><span>${q}</span><button data-inc="${slug}">+</button>
              </span>
              <button class="rm" data-rm="${slug}">Remove</button>
            </div>
          </div>
        </div>`;
      }).join("");
      $$("#drawerItems [data-inc]").forEach((b) => b.addEventListener("click", () => setQty(b.dataset.inc, cart[b.dataset.inc] + 1)));
      $$("#drawerItems [data-dec]").forEach((b) => b.addEventListener("click", () => setQty(b.dataset.dec, cart[b.dataset.dec] - 1)));
      $$("#drawerItems [data-rm]").forEach((b) => b.addEventListener("click", () => { setQty(b.dataset.rm, 0); toast("Removed from cart"); }));
    }

    const sub = cartSubtotal();
    const free = sub >= FREE_DELIVERY_ABOVE || sub === 0;
    const fee = free ? 0 : DELIVERY_FEE;
    $("#drawerSubtotal").textContent = fmt(sub);
    $("#drawerDelivery").textContent = sub === 0 ? "—" : free ? "FREE 🎉" : fmt(DELIVERY_FEE) + " (free above ₹499)";
    $("#drawerTotal").textContent = fmt(sub + (sub ? fee : 0));

    const bar = $("#freeBar");
    if (sub === 0) { bar.innerHTML = "Add items worth ₹499 for <b>FREE delivery</b> 🚚"; }
    else if (free) { bar.innerHTML = "🎉 Yay! You've unlocked <b>FREE delivery</b>"; }
    else {
      const pct = Math.min(100, Math.round((sub / FREE_DELIVERY_ABOVE) * 100));
      bar.innerHTML = `Add ${fmt(FREE_DELIVERY_ABOVE - sub)} more for <b>FREE delivery</b><div class="track"><div class="fill" style="width:${pct}%"></div></div>`;
    }
    renderCheckoutButtonState();
  }
  function renderCheckoutButtonState() {
    const btn = $("#checkoutBtn");
    if (!cartCount()) {
      btn.textContent = "Cart is empty — keep shopping 🌷";
      btn.onclick = () => { closeDrawer(); window.scrollTo({ top: 0, behavior: "smooth" }); };
    } else {
      btn.textContent = "Proceed to Checkout →";
      btn.onclick = () => { window.location.href = "checkout.html"; };
    }
  }

  /* ---------------- drawer open/close ---------------- */
  function openDrawer() { $("#cartDrawer").classList.add("show"); $("#overlay").classList.add("show"); }
  function closeDrawer() { $("#cartDrawer").classList.remove("show"); $("#overlay").classList.remove("show"); }

  /* ---------------- quick view modal ---------------- */
  let modalState = { p: null, i: 0 };
  function openModal(p) {
    modalState = { p, i: 0 };
    renderModal();
    $("#modalWrap").classList.add("show");
  }
  function closeModal() { $("#modalWrap").classList.remove("show"); }
  function renderModal() {
    const { p, i } = modalState;
    const off = Math.round((1 - p.price / p.mrp) * 100);
    const box = $("#modalBox");
    box.innerHTML = `
      <button class="modal-close" id="mClose">✕</button>
      <div class="m-gallery">
        <img class="main" src="${p.images[i]}" alt="${p.name}">
        ${p.images.length > 1 ? `<button class="m-nav prev" id="mPrev">‹</button><button class="m-nav next" id="mNext">›</button>` : ""}
        <div class="m-thumbs">${p.images.map((src, j) => `<img src="${src}" data-thumb="${j}" class="${j === i ? "active" : ""}" alt="photo ${j + 1}">`).join("")}</div>
      </div>
      <div class="m-info">
        <span class="cat">${CAT_LABEL[p.category]} • ${p.images.length} real photos — hover on cards to see them all</span>
        <h3>${p.name}</h3>
        <div class="card-meta"><span class="stars">${"★".repeat(Math.round(p.rating))}${"☆".repeat(5 - Math.round(p.rating))}</span> ${p.rating} &nbsp;•&nbsp; ${p.reviews} reviews</div>
        <div class="m-price"><b>${fmt(p.price)}</b><s>${fmt(p.mrp)}</s><span class="off">${off}% OFF</span></div>
        <p class="m-desc">${p.desc}</p>
        <div class="m-meta">
          <span>🚚 <b>Delivery across India</b> — 19,000+ pincodes (2–7 days)</span>
          <span>💵 Pay via UPI, Card, Net Banking or Cash on Delivery</span>
          <span>🌿 Farm fresh quality guarantee</span>
        </div>
        <div class="m-actions">
          <span class="qty" style="padding:4px 2px">
            <button id="mDec">−</button><span id="mQty">1</span><button id="mInc">+</button>
          </span>
          <button class="btn btn-primary" id="mAdd">Add to Cart 🛒</button>
        </div>
      </div>`;
    let qty = 1;
    const setQ = (v) => { qty = Math.max(1, v); $("#mQty").textContent = qty; };
    $("#mDec").onclick = () => setQ(qty - 1);
    $("#mInc").onclick = () => setQ(qty + 1);
    $("#mAdd").onclick = () => { addToCart(p.slug, qty); closeModal(); openDrawer(); };
    $("#mClose").onclick = closeModal;
    const prev = $("#mPrev"), next = $("#mNext");
    if (prev) {
      prev.onclick = () => { modalState.i = (modalState.i - 1 + p.images.length) % p.images.length; renderModal(); };
      next.onclick = () => { modalState.i = (modalState.i + 1) % p.images.length; renderModal(); };
    }
    $$("#modalBox [data-thumb]").forEach((t) => t.onclick = () => { modalState.i = +t.dataset.thumb; renderModal(); });
  }

  /* ---------------- search / tabs / sort wiring ---------------- */
  let debounceT;
  const searchInput = $("#searchInput");
  searchInput.addEventListener("input", () => {
    state.q = searchInput.value;
    $("#searchClear").style.display = state.q ? "" : "none";
    clearTimeout(debounceT);
    debounceT = setTimeout(render, 180);
  });
  searchInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") { clearTimeout(debounceT); render(); searchInput.blur(); }
  });
  $("#searchClear").addEventListener("click", () => {
    searchInput.value = "";
    state.q = "";
    $("#searchClear").style.display = "none";
    render();
  });

  $$("#tabs .tab").forEach((tab) =>
    tab.addEventListener("click", () => {
      $$("#tabs .tab").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      state.cat = tab.dataset.cat;
      render();
    })
  );
  // footer category links
  $$("[data-cat-link]").forEach((a) =>
    a.addEventListener("click", () => {
      const cat = a.dataset.catLink;
      const tab = $(`#tabs .tab[data-cat="${cat}"]`);
      if (tab) tab.click();
    })
  );

  $("#sortSel").addEventListener("change", (e) => { state.sort = e.target.value; render(); });

  $$(".chip").forEach((chip) =>
    chip.addEventListener("click", () => {
      searchInput.value = chip.dataset.q;
      state.q = chip.dataset.q;
      $("#searchClear").style.display = "";
      render();
      $("#shop").scrollIntoView({ behavior: "smooth" });
    })
  );

  $("#oosClear").addEventListener("click", () => $("#searchClear").click());
  $("#oosBrowse").addEventListener("click", () => {
    $("#searchClear").click();
    const all = $('#tabs .tab[data-cat="all"]');
    if (all) all.click();
    $("#shop").scrollIntoView({ behavior: "smooth" });
  });

  /* ---------------- drawer & modal wiring ---------------- */
  $("#cartBtn").addEventListener("click", openDrawer);
  $("#drawerClose").addEventListener("click", closeDrawer);
  $("#overlay").addEventListener("click", closeDrawer);
  $("#modalWrap").addEventListener("click", (e) => { if (e.target === $("#modalWrap")) closeModal(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") { closeModal(); closeDrawer(); } });

  /* ---------------- init ---------------- */
  updateBadge();
  render();
  renderDrawer();
})();
