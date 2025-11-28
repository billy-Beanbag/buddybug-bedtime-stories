// ======== CONFIG ========

const API_BASE = "http://127.0.0.1:8001";

// Random generic names when none chosen/typed
const RANDOM_NAMES = [
  "Milo",
  "Rory",
  "Sky",
  "Luna",
  "Nova",
  "Harper",
  "Jasper",
  "Isla",
  "Elliot",
  "Zara",
];

// LocalStorage keys
const LS_CHILDREN = "buddybug_children_v1";
const LS_HISTORY = "buddybug_history_v1";
const LS_FAVS = "buddybug_favourites_v1";

// ======== STATE ========

let children = [];
let history = [];
let favourites = [];
let lastStory = null;

// ======== HELPERS ========

function load(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw);
  } catch {
    return fallback;
  }
}

function save(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (e) {
    console.warn("Failed to save", key, e);
  }
}

function randomItem(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

// ======== DOM ELEMENTS ========

const setupChildInput = document.getElementById("setup-child-name");
const addChildBtn = document.getElementById("add-child-btn");
const childrenListEl = document.getElementById("children-list");

const childSelect = document.getElementById("child-select");
const childNameInput = document.getElementById("child-name");
const siblingsChipsContainer = document.getElementById("siblings-chips");
const siblingsExtraInput = document.getElementById("siblings-extra");
const favouriteThingInput = document.getElementById("favourite-thing");
const styleSelect = document.getElementById("style");
const lengthSelect = document.getElementById("length");
const storyOutput = document.getElementById("story-output");

const generateBtn = document.getElementById("generate-btn");
const surpriseBtn = document.getElementById("surprise-btn");
const favoriteBtn = document.getElementById("favorite-btn");

const previousList = document.getElementById("previous-stories");
const favouriteList = document.getElementById("favourite-stories");
const clearHistoryBtn = document.getElementById("clear-history-btn");
const clearFavouritesBtn = document.getElementById("clear-favourites-btn");

// ======== CHILDREN RENDERING ========

function renderChildren() {
  // List under setup
  childrenListEl.innerHTML = "";
  if (children.length === 0) {
    const li = document.createElement("li");
    li.className = "small";
    li.textContent = "No names added yet.";
    childrenListEl.appendChild(li);
  } else {
    children.forEach((name) => {
      const li = document.createElement("li");
      li.className = "child-pill";
      li.textContent = name;
      childrenListEl.appendChild(li);
    });
  }

  // Child select
  childSelect.innerHTML = "";
  const defaultOpt = document.createElement("option");
  defaultOpt.value = "";
  defaultOpt.textContent = "— choose a saved name (optional) —";
  childSelect.appendChild(defaultOpt);

  children.forEach((name) => {
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = name;
    childSelect.appendChild(opt);
  });

  // Sibling chips
  siblingsChipsContainer.innerHTML = "";
  children.forEach((name) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "chip";
    chip.textContent = name;
    chip.addEventListener("click", () => {
      chip.classList.toggle("chip-selected");
    });
    siblingsChipsContainer.appendChild(chip);
  });
}

// ======== HISTORY & FAVS RENDER ========

function renderHistory() {
  previousList.innerHTML = "";

  if (history.length === 0) {
    const li = document.createElement("li");
    li.className = "small";
    li.textContent = "No stories yet. Generate one to see it here.";
    previousList.appendChild(li);
    return;
  }

  history.forEach((entry) => {
    const li = document.createElement("li");
    li.className = "story-card";

    const title = document.createElement("div");
    title.className = "story-card-title";
    title.textContent = entry.title;
    li.appendChild(title);

    const meta = document.createElement("div");
    meta.className = "story-card-meta";
    meta.textContent = `${entry.styleLabel} • ${entry.lengthLabel}`;
    li.appendChild(meta);

    const preview = document.createElement("div");
    preview.className = "story-card-preview";
    preview.textContent =
      entry.story.length > 120 ? entry.story.slice(0, 120) + "…" : entry.story;
    li.appendChild(preview);

    li.addEventListener("click", () => {
      storyOutput.textContent = entry.story;
      lastStory = entry;
      updateFavoriteButton();
    });

    previousList.appendChild(li);
  });
}

function renderFavourites() {
  favouriteList.innerHTML = "";

  if (favourites.length === 0) {
    const li = document.createElement("li");
    li.className = "small";
    li.textContent = "No favourites yet. Star a story to save it here.";
    favouriteList.appendChild(li);
    return;
  }

  favourites.forEach((entry) => {
    const li = document.createElement("li");
    li.className = "story-card";

    const title = document.createElement("div");
    title.className = "story-card-title";
    title.textContent = entry.title;
    li.appendChild(title);

    const meta = document.createElement("div");
    meta.className = "story-card-meta";
    meta.textContent = `${entry.styleLabel} • ${entry.lengthLabel}`;
    li.appendChild(meta);

    const preview = document.createElement("div");
    preview.className = "story-card-preview";
    preview.textContent =
      entry.story.length > 120 ? entry.story.slice(0, 120) + "…" : entry.story;
    li.appendChild(preview);

    li.addEventListener("click", () => {
      storyOutput.textContent = entry.story;
      lastStory = entry;
      updateFavoriteButton();
    });

    favouriteList.appendChild(li);
  });
}

function isFavourite(entry) {
  return favourites.some((f) => f.id === entry.id);
}

function updateFavoriteButton() {
  if (!lastStory) {
    favoriteBtn.disabled = true;
    favoriteBtn.textContent = "⭐ Add to favourites";
    return;
  }
  favoriteBtn.disabled = false;
  if (isFavourite(lastStory)) {
    favoriteBtn.textContent = "⭐ Remove from favourites";
  } else {
    favoriteBtn.textContent = "⭐ Add to favourites";
  }
}

// ======== STORY LABEL HELPERS ========

function styleLabel(style) {
  switch (style) {
    case "silly":
      return "Silly";
    case "adventurous":
      return "Adventurous";
    default:
      return "Gentle";
  }
}

function lengthLabel(len) {
  switch (len) {
    case "medium":
      return "Medium length";
    case "long":
      return "Long";
    default:
      return "Short";
  }
}

// ======== GENERATE STORY ========

async function generateStory(mode = "normal") {
  // Decide child name
  let finalName;

  if (mode === "surprise") {
    finalName = randomItem(RANDOM_NAMES);
  } else {
    const selected = childSelect.value;
    const custom = childNameInput.value.trim();
    finalName = custom || selected || randomItem(RANDOM_NAMES);
  }

  // Siblings from chips
  const siblingNames = Array.from(
    siblingsChipsContainer.querySelectorAll(".chip-selected")
  ).map((chip) => chip.textContent);

  // Extra siblings
  const extra = siblingsExtraInput.value
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  const allSiblings = [...siblingNames, ...extra];
  const siblingsString = allSiblings.length ? allSiblings.join(", ") : null;

  // Favourite thing
  const favThing = favouriteThingInput.value.trim() || "";

  const style = styleSelect.value;
  const length = lengthSelect.value;

  const payload = {
    child_name: finalName,
    favourite_thing: favThing,
    style,
    length,
    siblings: siblingsString,
  };

  storyOutput.textContent = "Creating your story...";

  try {
    const res = await fetch(`${API_BASE}/story`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      throw new Error(`Server error ${res.status}`);
    }

    const data = await res.json();

    storyOutput.textContent = data.story;

    const entry = {
      id: Date.now(),
      title: finalName || "Someone special",
      story: data.story,
      style,
      length,
      styleLabel: styleLabel(style),
      lengthLabel: lengthLabel(length),
    };

    lastStory = entry;
    history.unshift(entry);
    if (history.length > 20) history = history.slice(0, 20);
    save(LS_HISTORY, history);

    renderHistory();
    updateFavoriteButton();
  } catch (err) {
    console.error(err);
    storyOutput.textContent =
      "Something went wrong while generating the story. Is the backend running on port 8001?";
  }
}

// ======== EVENT HANDLERS ========

addChildBtn.addEventListener("click", () => {
  const name = setupChildInput.value.trim();
  if (!name) return;
  if (!children.includes(name)) {
    children.push(name);
    save(LS_CHILDREN, children);
    renderChildren();
  }
  setupChildInput.value = "";
});

generateBtn.addEventListener("click", () => generateStory("normal"));
surpriseBtn.addEventListener("click", () => generateStory("surprise"));

favoriteBtn.addEventListener("click", () => {
  if (!lastStory) return;
  const idx = favourites.findIndex((f) => f.id === lastStory.id);
  if (idx >= 0) {
    favourites.splice(idx, 1);
  } else {
    favourites.unshift(lastStory);
    if (favourites.length > 30) favourites = favourites.slice(0, 30);
  }
  save(LS_FAVS, favourites);
  renderFavourites();
  updateFavoriteButton();
});

clearHistoryBtn.addEventListener("click", () => {
  history = [];
  save(LS_HISTORY, history);
  renderHistory();
  lastStory = null;
  updateFavoriteButton();
});

clearFavouritesBtn.addEventListener("click", () => {
  favourites = [];
  save(LS_FAVS, favourites);
  renderFavourites();
  updateFavoriteButton();
});

// ======== INITIAL LOAD ========

children = load(LS_CHILDREN, []);
history = load(LS_HISTORY, []);
favourites = load(LS_FAVS, []);

renderChildren();
renderHistory();
renderFavourites();
updateFavoriteButton();
