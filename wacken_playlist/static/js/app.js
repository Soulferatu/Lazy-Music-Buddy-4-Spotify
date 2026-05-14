if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/static/service-worker.js").catch(() => {
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

const translations = {
  en: {
    hero_eyebrow: "Wacken Open Air playlist builder",
    hero_lede: "Select the Wacken 2026 bands you want to hear, name the playlist, and the app will use Spotify artist matches to pick each band's top streamed tracks. The playlist is created through the app account, so visitors can get a Spotify link without connecting their own Spotify account.",
    stage_eyebrow: "Stage 1",
    language_label: "Language",
    selection_title: "Wacken 2026 selection",
    band_count: (count) => `${count} bands`,
    playlist_name_label: "Playlist name",
    playlist_name_placeholder: "Wacken 2026 must-see list",
    filter_bands_label: "Filter bands",
    search_placeholder: "Search lineup",
    clear_button: "Clear",
    choose_bands: "Choose bands",
    source_note: "Starter lineup data is curated from official W:O:A 2026 announcements and can be refreshed before Spotify matching.",
    selected_label: "selected",
    preview_button: "Preview playlist",
    local_preview: "Local preview",
    preview_tracks: (count) => `Spotify will later try to add up to ${count} tracks: 10 top songs for each selected band.`,
    preview_eyebrow: "Preview",
    ready_title: "Ready for your picks",
    ready_copy: "This step stays local. Spotify search, warnings, and playlist creation begin in later stages.",
    playlist_name_required: "Name the playlist before previewing it.",
    bands_required: "Select at least one Wacken 2026 band.",
  },
  "pt-BR": {
    hero_eyebrow: "Criador de playlists do Wacken Open Air",
    hero_lede: "Selecione as bandas do Wacken 2026 que quer ouvir, dê um nome à playlist e o app usará correspondências de artistas no Spotify para escolher as faixas mais tocadas de cada banda. A playlist é criada pela conta do app, então visitantes recebem um link do Spotify sem conectar a própria conta.",
    stage_eyebrow: "Etapa 1",
    language_label: "Idioma",
    selection_title: "Seleção Wacken 2026",
    band_count: (count) => `${count} bandas`,
    playlist_name_label: "Nome da playlist",
    playlist_name_placeholder: "Lista imperdível Wacken 2026",
    filter_bands_label: "Filtrar bandas",
    search_placeholder: "Buscar na escalação",
    clear_button: "Limpar",
    choose_bands: "Escolha as bandas",
    source_note: "A escalação inicial foi curada a partir de anúncios oficiais do W:O:A 2026 e pode ser atualizada antes da busca no Spotify.",
    selected_label: "selecionadas",
    preview_button: "Pré-visualizar playlist",
    local_preview: "Prévia local",
    preview_tracks: (count) => `Mais tarde, o Spotify tentará adicionar até ${count} faixas: 10 músicas principais para cada banda selecionada.`,
    preview_eyebrow: "Prévia",
    ready_title: "Pronto para suas escolhas",
    ready_copy: "Esta etapa fica local. Busca no Spotify, avisos e criação da playlist começam nas próximas etapas.",
    playlist_name_required: "Dê um nome à playlist antes de visualizar.",
    bands_required: "Selecione pelo menos uma banda do Wacken 2026.",
  },
};

function getInitialLanguage() {
  const serverLanguage = languageInput?.value;
  const savedLanguage = window.localStorage.getItem("language");
  return translations[savedLanguage] ? savedLanguage : serverLanguage || "en";
}

function updateSelectedCount() {
  if (!selectedCount) return;
  selectedCount.textContent = bandCheckboxes.filter((checkbox) => checkbox.checked).length;
}

function applyLanguage(language) {
  const dictionary = translations[language] || translations.en;
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
    if (typeof dictionary[key] === "function") {
      element.textContent = dictionary[key](count);
    }
  });

  document.querySelectorAll("[data-i18n-track-preview]").forEach((element) => {
    const count = Number(element.dataset.trackCount);
    element.textContent = dictionary.preview_tracks(count);
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
