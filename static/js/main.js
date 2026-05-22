/* ══════════════════════════════════════════════════════════
   LAYOSAM  ·  Shared JS  ·  main.js
══════════════════════════════════════════════════════════ */

/* ── Mobile nav drawer ── */
(function () {
  var burger = document.getElementById("nav-burger");
  var drawer = document.getElementById("nav-drawer");
  if (!burger || !drawer) return;
  burger.addEventListener("click", function () {
    var open = drawer.classList.toggle("open");
    burger.classList.toggle("open", open);
    burger.setAttribute("aria-expanded", String(open));
    drawer.setAttribute("aria-hidden", String(!open));
  });
  drawer.querySelectorAll("a").forEach(function (a) {
    a.addEventListener("click", function () {
      drawer.classList.remove("open");
      burger.classList.remove("open");
      burger.setAttribute("aria-expanded", "false");
      drawer.setAttribute("aria-hidden", "true");
    });
  });
  // Close on Escape key
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && drawer.classList.contains("open")) {
      drawer.classList.remove("open");
      burger.classList.remove("open");
      burger.setAttribute("aria-expanded", "false");
      drawer.setAttribute("aria-hidden", "true");
      burger.focus();
    }
  });
})();

/* ── Scroll reveal ── */
(function () {
  var els = document.querySelectorAll(".rev");
  // Respect prefers-reduced-motion — skip animation, show instantly
  var prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (prefersReduced) {
    els.forEach(function (el) { el.classList.add("in"); });
    return;
  }
  var obs = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) {
        e.target.classList.add("in");
        // Remove will-change after animation completes to free compositor layer
        setTimeout(function () {
          e.target.style.willChange = "auto";
        }, 600);
        obs.unobserve(e.target);
      }
    });
  }, { threshold: 0.08 });
  els.forEach(function (el) { obs.observe(el); });
})();

/* ── Smart job counter ── */
(function () {
  const MONTHS = ['January','February','March','April','May','June',
                  'July','August','September','October','November','December'];

  function seededRng(seed) {
    let s = (seed ^ 0xdeadbeef) >>> 0;
    return function () {
      s = Math.imul(s ^ (s >>> 15), 1 | s);
      s ^= s + Math.imul(s ^ (s >>> 7), 61 | s);
      return ((s ^ (s >>> 14)) >>> 0) / 4294967295;
    };
  }

  const now = new Date();
  const yr = now.getFullYear(), mo = now.getMonth(), day = now.getDate(), dow = now.getDay();

  const moRng = seededRng(yr * 1000 + mo);
  let monthJobs = 0;
  for (let d = 1; d <= day; d++) {
    const r = moRng();
    monthJobs += r < 0.38 ? 0 : r < 0.76 ? 1 : 2;
  }
  monthJobs = Math.min(monthJobs, 22);

  const dW = dow === 0 ? 0 : dow, wkS = day - dW;
  const wkRng = seededRng(yr * 100000 + mo * 1000 + wkS);
  let weekJobs = 0;
  for (let d = 0; d < dW; d++) {
    const r = wkRng();
    weekJobs += r < 0.30 ? 0 : r < 0.72 ? 1 : 2;
  }
  weekJobs = Math.min(weekJobs, 9);

  const BASE = 200, BYR = 2024, BMO = 0;
  let total = BASE;
  const mEl = (yr - BYR) * 12 + (mo - BMO);
  for (let m = 0; m < mEl; m++) {
    const aM = BMO + m;
    const mRng = seededRng((BYR + Math.floor(aM / 12)) * 1000 + (aM % 12));
    let mJ = 0;
    const dim = new Date(BYR + Math.floor(aM / 12), (aM % 12) + 1, 0).getDate();
    for (let d = 1; d <= dim; d++) {
      const r = mRng();
      mJ += r < 0.38 ? 0 : r < 0.76 ? 1 : 2;
    }
    total += Math.min(mJ, 22);
  }
  total += monthJobs;

  // Update slot badges
  const hr = now.getHours();
  const slots = hr < 9 ? 5 : hr < 12 ? 4 : hr < 15 ? 3 : hr < 18 ? 2 : 1;
  document.querySelectorAll(".slot-badge-text").forEach(function (el) {
    el.textContent = slots + " inspection slot" + (slots === 1 ? "" : "s") + " available today";
  });
  document.querySelectorAll(".urg-slots-text").forEach(function (el) {
    el.textContent = "Only " + slots + " inspection slot" + (slots === 1 ? "" : "s") + " left today";
  });

  // Update totals
  document.querySelectorAll(".jobs-total").forEach(function (el) { el.textContent = total + "+"; });
  document.querySelectorAll(".jobs-month").forEach(function (el) { el.textContent = monthJobs; });
  document.querySelectorAll(".jobs-week").forEach(function (el) { el.textContent = weekJobs; });
  document.querySelectorAll(".month-name").forEach(function (el) { el.textContent = MONTHS[mo]; });
  document.querySelectorAll(".projects-sub-dynamic").forEach(function (el) {
    el.textContent = monthJobs + " jobs completed in " + MONTHS[mo] + " across Ibadan.";
  });
  document.querySelectorAll(".cnt-desc-dynamic").forEach(function (el) {
    el.innerHTML = "<strong>" + monthJobs + " electrical jobs</strong> completed in " + MONTHS[mo] +
      " &nbsp;·&nbsp; <strong>" + weekJobs + "</strong> this week";
  });

  // Animated counters
  function anim(el, target, dur, sfx) {
    if (!el) return;
    const t0 = performance.now();
    function s(ts) {
      const p = Math.min((ts - t0) / dur, 1), e = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(e * target) + (sfx || "");
      if (p < 1) requestAnimationFrame(s); else el.textContent = target + (sfx || "");
    }
    requestAnimationFrame(s);
  }

  const cW = document.querySelector(".counter-wrap");
  let fired = false;
  if (cW) {
    const obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting && !fired) {
          fired = true;
          anim(document.getElementById("cnt-total"),  total,     1800, "+");
          anim(document.getElementById("cnt-month"),  monthJobs, 1200, "");
          anim(document.getElementById("cnt-week"),   weekJobs,  900,  "");
          obs.unobserve(e.target);
        }
      });
    }, { threshold: 0.2 });
    obs.observe(cW);
  }

  // Expose for templates
  window.layosamStats = { total: total, monthJobs: monthJobs, weekJobs: weekJobs, slots: slots };
})();

/* ── Project filter chips ── */
(function () {
  const chips = document.querySelectorAll(".filter-chip");
  const cards = document.querySelectorAll(".filterable-card");
  if (!chips.length) return;
  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      chips.forEach(function (c) { c.classList.remove("active"); });
      chip.classList.add("active");
      const cat = chip.dataset.cat;
      cards.forEach(function (card) {
        if (cat === "all" || card.dataset.cat === cat) {
          card.style.display = "";
        } else {
          card.style.display = "none";
        }
      });
    });
  });
})();
