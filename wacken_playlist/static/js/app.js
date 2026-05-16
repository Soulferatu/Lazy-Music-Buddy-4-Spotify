/*
  app.js — A1v3 "Embers" port
  ---------------------------
  Preserves all v1 behaviour (i18n, search, clear, selected-count, language
  switching, service worker registration) and adds the Embers visual layer:
    • Cursor-aware ember particle field on #embers canvas
    • Live nameplate on the banner that mirrors the playlist-name input
    • Spark flash on band tile toggle
  v1 backup: app.v1.js
*/

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/service-worker.js", { scope: "/" }).catch(() => {
      // Local development can still continue when service worker registration fails.
    });
  });
}

const bandSearch = document.querySelector("#band-search");
const bandOptions = Array.from(document.querySelectorAll(".band-option"));
const clearSelection = document.querySelector("#clear-selection");
const selectedCount = document.querySelector("#selected-count");
const bandCheckboxes = Array.from(document.querySelectorAll('input[name="bands"]'));
const languageInput = document.querySelector("#language");
const languageButtons = Array.from(document.querySelectorAll("[data-language-choice]"));
const playlistNameInput = document.querySelector("#playlist-name");
const bannerNameplate = document.querySelector("#banner-nameplate");
const bannerNameplateText = document.querySelector("#banner-nameplate-text");

const translations = window.__translations || {};
const DEFAULT_LANGUAGE = "en";

function format(template, params) {
  if (typeof template !== "string") return "";
  return template.replace(/\{(\w+)\}/g, (_, key) => (params[key] != null ? params[key] : ""));
}

function getInitialLanguage() {
  const serverLanguage = languageInput?.value;
  const savedLanguage = window.localStorage.getItem("language");
  if (translations[savedLanguage]) return savedLanguage;
  if (translations[serverLanguage]) return serverLanguage;
  return DEFAULT_LANGUAGE;
}

function updateSelectedCount() {
  if (!selectedCount) return;
  selectedCount.textContent = bandCheckboxes.filter((checkbox) => checkbox.checked).length;
}

function applyLanguage(language) {
  const dictionary = translations[language] || translations[DEFAULT_LANGUAGE] || {};
  document.documentElement.lang = language;

  if (languageInput) {
    languageInput.value = language;
  }

  window.localStorage.setItem("language", language);

  document.querySelectorAll("[data-i18n]").forEach((element) => {
    const key = element.dataset.i18n;
    if (typeof dictionary[key] === "string") {
      element.textContent = dictionary[key];
    }
  });

  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    const key = element.dataset.i18nPlaceholder;
    if (typeof dictionary[key] === "string") {
      element.placeholder = dictionary[key];
    }
  });

  document.querySelectorAll("[data-i18n-count]").forEach((element) => {
    const key = element.dataset.i18nCount;
    const count = Number(element.dataset.count);
    if (typeof dictionary[key] === "string") {
      element.textContent = format(dictionary[key], { count });
    }
  });

  document.querySelectorAll("[data-i18n-track-preview]").forEach((element) => {
    const count = Number(element.dataset.trackCount);
    const bandCount = element.dataset.bandCount != null ? Number(element.dataset.bandCount) : null;
    if (bandCount != null && typeof dictionary.preview_tracks_matched === "string") {
      element.textContent = format(dictionary.preview_tracks_matched, { count, band_count: bandCount });
    } else if (typeof dictionary.preview_tracks === "string") {
      element.textContent = format(dictionary.preview_tracks, { count });
    }
  });

  languageButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.languageChoice === language);
    button.setAttribute("aria-pressed", String(button.dataset.languageChoice === language));
  });
}

function filterBands() {
  const query = bandSearch ? bandSearch.value.trim().toLowerCase() : "";
  bandOptions.forEach((option) => {
    option.classList.toggle("is-hidden", Boolean(query) && !option.dataset.bandName.includes(query));
  });
}

bandSearch?.addEventListener("input", filterBands);
bandSearch?.addEventListener("search", filterBands);

clearSelection?.addEventListener("click", () => {
  bandCheckboxes.forEach((checkbox) => {
    checkbox.checked = false;
  });
  updateSelectedCount();
});

bandCheckboxes.forEach((checkbox) => {
  checkbox.addEventListener("change", updateSelectedCount);
});

// ───────── Embers visual layer additions ─────────

// Spark flash on band tile click
bandOptions.forEach((option) => {
  option.addEventListener("click", () => {
    requestAnimationFrame(() => {
      option.classList.remove("is-flash");
      // Force reflow so the animation restarts.
      void option.offsetWidth;
      option.classList.add("is-flash");
    });
  });
});

// Live banner nameplate — mirrors the playlist-name input
function syncNameplate() {
  if (!bannerNameplate || !bannerNameplateText || !playlistNameInput) return;
  const value = playlistNameInput.value.trim();
  bannerNameplateText.textContent = value;
  bannerNameplate.classList.toggle("is-live", Boolean(value));
}

playlistNameInput?.addEventListener("input", syncNameplate);
// Initial paint reflects any server-rendered playlist name (preview or form_values).
syncNameplate();

// Cursor-aware ember particle field
(function startEmbers() {
  const canvas = document.getElementById("embers");
  if (!canvas) return;
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const ctx = canvas.getContext("2d");
  let w = 0;
  let h = 0;
  let mx = -9999;
  let my = -9999;
  let mActive = false;
  const particles = [];

  function resize() {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
  }

  function spawn() {
    return {
      x: Math.random() * w,
      y: h + 10,
      vx: (Math.random() - 0.5) * 0.5,
      vy: -Math.random() * 1.4 - 0.4,
      r: Math.random() * 1.8 + 0.4,
      life: Math.random() * 220 + 140,
      age: 0,
      hue: 20 + Math.random() * 30,
    };
  }

  resize();
  window.addEventListener("resize", resize);
  window.addEventListener("pointermove", (e) => {
    mx = e.clientX;
    my = e.clientY;
    mActive = true;
  });
  window.addEventListener("pointerleave", () => {
    mActive = false;
  });

  for (let i = 0; i < 170; i++) {
    const p = spawn();
    p.y = Math.random() * h;
    particles.push(p);
  }

  function tick() {
    ctx.clearRect(0, 0, w, h);
    for (const p of particles) {
      if (mActive) {
        const dx = mx - p.x;
        const dy = my - p.y;
        const d2 = dx * dx + dy * dy;
        if (d2 < 40000) {
          const f = 0.0006;
          p.vx += dx * f;
          p.vy += dy * f;
        }
      }
      p.x += p.vx;
      p.y += p.vy;
      p.age += 1;
      p.vx *= 0.99;
      p.vy *= 0.995;
      if (p.age > p.life || p.y < -10) Object.assign(p, spawn());
      const a = 1 - p.age / p.life;
      const grad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 5);
      grad.addColorStop(0, `hsla(${p.hue}, 100%, 55%, ${0.65 * a})`);
      grad.addColorStop(1, "hsla(15, 100%, 40%, 0)");
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r * 5, 0, Math.PI * 2);
      ctx.fill();
    }
    if (!reduce) requestAnimationFrame(tick);
  }
  tick();
})();

languageButtons.forEach((button) => {
  button.addEventListener("click", () => {
    applyLanguage(button.dataset.languageChoice);
  });
});

applyLanguage(getInitialLanguage());

// ───────── Dynamic countdown ─────────

(function updateCountdown() {
  const el = document.getElementById("countdown-days");
  if (!el) return;
  const target = new Date(el.dataset.targetDate + "T00:00:00");
  const now = new Date();
  const msPerDay = 1000 * 60 * 60 * 24;
  const days = Math.ceil((target - now) / msPerDay);
  el.textContent = days > 0 ? days : 0;
})();

// ───────── Loading states on form submit ─────────

function applyLoadingState(fabId, translationKey, fallback) {
  const fab = document.getElementById(fabId);
  if (!fab) return;
  const lang = languageInput?.value || DEFAULT_LANGUAGE;
  const dict = translations[lang] || translations[DEFAULT_LANGUAGE] || {};
  fab.textContent = dict[translationKey] || fallback;
  fab.disabled = true;
}

document.getElementById("planner-form")?.addEventListener("submit", () => {
  applyLoadingState("fab-preview", "preview_loading", "Loading…");
});

document.getElementById("create-form-element")?.addEventListener("submit", () => {
  applyLoadingState("fab-create", "create_loading", "Creating…");
});

// ───────── Mobile auto-scroll to summary when there's a result ─────────

(function scrollToResultOnMobile() {
  const summary = document.querySelector('.summary');
  if (!summary) return;
  if (summary.dataset.state === 'idle') return;
  if (window.innerWidth >= 920) return;
  summary.scrollIntoView({ behavior: 'smooth', block: 'start' });
})();
