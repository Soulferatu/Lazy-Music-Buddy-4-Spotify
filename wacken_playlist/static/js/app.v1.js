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

bandSearch?.addEventListener("input", () => {
  const query = bandSearch.value.trim().toLowerCase();
  bandOptions.forEach((option) => {
    option.hidden = query && !option.dataset.bandName.includes(query);
  });
});

clearSelection?.addEventListener("click", () => {
  bandCheckboxes.forEach((checkbox) => {
    checkbox.checked = false;
  });
  updateSelectedCount();
});

bandCheckboxes.forEach((checkbox) => {
  checkbox.addEventListener("change", updateSelectedCount);
});

languageButtons.forEach((button) => {
  button.addEventListener("click", () => {
    applyLanguage(button.dataset.languageChoice);
  });
});

applyLanguage(getInitialLanguage());
