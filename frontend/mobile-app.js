const API_BASE = "http://127.0.0.1:8001";

// Simple localStorage helpers
function load(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function save(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {}
}

// State
let children = load("bb_mobile_children_v1", ["Milo", "Luna"]);
let favourites = load("bb_mobile_favourites_v1", []); // {id,title,story,meta}
let currentStory = null;
let currentCategory = null;

// Screen elements
const screenHome = document.getElementById("screen-home");
const screenBuilder = document.getElementById("screen-builder");
const screenStory = document.getElementById("screen-story");
const screenFavourites = document.getElementById("screen-favourites");

// Builder fields
const childSelect = document.getElementById("builder-child-select");
const childNameInput = document.getElementById("builder-child-name");
const siblingsChips = document.getElementById("builder-siblings-chips");
const siblingsExtraInput = document.getElementById("builder-siblings-extra");
const favouriteInput = document.getElementById("builder-favourite");

const stylePills = document.querySelectorAll(".pill[data-style]");
const lengthPills = document.querySelectorAll(".pill[data-length]");
const categoryChips = document.querySelectorAll(".category-chip");

// Buttons
const btnSurprise = document.getElementById("btn-surprise");
const btnBuilder = document.getElementById("btn-builder");
const btnFavourites = document.getElementById("btn-favourites");
const btnGenerate = document.getElementById("btn-generate");

const backFromBuilder = document.getElementById("back-from-builder");
const backFromStory = document.getElementById("back-from-story");
const backFromFavourites = document.getElementById("back-from-favourites");

const storyTitleEl = document.getElementById("story-title");
const storyTextEl = document.getElementById("story-text");
const btnFavToggle = document.getElementById("btn-fav-toggle");
const favouritesList = document.getElementById("favourites-list");

const btnReadMyself = document.getElementById("btn-read-myself");
const btnAutoNarrate = document.getElementById("btn-auto-narrate");
const btnBedtimeMode = document.getElementById("btn-bedtime-mode");

// Bottom nav
const navItems = document.querySelectorAll(".nav-item");

// Screen helpers
function showScreen(targetId) {
  const allScreens = [screenHome, screenBuilder, screenStory, screenFavourites];
  allScreens.forEach((s) => s.classList.remove("active"));

  const map = {
    "screen-home": screenHome,
    "screen-builder": screenBuilder,
    "screen-story": screenStory,
    "screen-favourites": screenFavourites,
  };

  const el = map[targetId];
  if (el) el.classList.add("active");
}

// Nav helpers
navItems.forEach((btn) => {
  btn.addEventListener("click", () => {
    navItems.forEach((b) => b.classList.remove("nav-active"));
    btn.classList.add("nav-active");

    const target = btn.getAttribute("data-nav-target");
    showScreen(target);
  });
});

// Children render
function renderChildren() {
  childSelect.innerHTML = "";
  const none = document.createElement("option");
  none.value = "";
  none.textContent = "No one in particular";
  childSelect.appendChild(none);

  siblingsChips.innerHTML = "";

  children.forEach((name) => {
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = name;
    childSelect.appendChild(opt);

    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "chip";
    chip.textContent = name;
    chip.addEventListener("click", () => {
      chip.classList.toggle("pill-selected");
    });
    siblingsChips.appendChild(chip);
  });
}

// Favourites render
function renderFavourites() {
  favouritesList.innerHTML = "";
  if (favourites.length === 0) {
    const p = document.createElement("p");
    p.textContent =
      "No favourites yet. ⭐ Tap the star on a story to save it here.";
    p.className = "hint-text";
    favouritesList.appendChild(p);
    return;
  }

  favourites.forEach((f) => {
    const div = document.createElement("div");
    div.className = "fav-item";
    const title = document.createElement("div");
    title.className = "fav-title";
    title.textContent = f.title;
    const preview = document.createElement("div");
    preview.className = "fav-preview";
    preview.textContent =
      f.story.length > 120 ? f.story.slice(0, 120) + "…" : f.story;

    div.appendChild(title);
    div.appendChild(preview);

    div.addEventListener("click", () => {
      currentStory = f;
      showStory(f);
    });

    favouritesList.appendChild(div);
  });
}

// Pills
function setupPills(pills) {
  pills.forEach((pill) => {
    pill.addEventListener("click", () => {
      pills.forEach((p) => p.classList.remove("pill-selected"));
      pill.classList.add("pill-selected");
    });
  });
}

setupPills(stylePills);
setupPills(lengthPills);

// Category chips
categoryChips.forEach((chip) => {
  chip.addEventListener("click", () => {
    categoryChips.forEach((c) => c.classList.remove("selected"));
    chip.classList.add("selected");
    currentCategory = chip.getAttribute("data-category");
  });
});

// Theme quick chips -> favourite thing field
document.querySelectorAll(".chip.pill[data-theme]").forEach((chip) => {
  chip.addEventListener("click", () => {
    favouriteInput.value = chip.getAttribute("data-theme");
  });
});

// Random helper
function randomName() {
  const pool = ["Milo", "Luna", "Rory", "Nova", "Harper", "Ezra", "Zara"];
  return pool[Math.floor(Math.random() * pool.length)];
}

// Generate story
async function generateStory(mode = "normal") {
  let name;
  if (mode === "surprise") {
    name = randomName();
  } else {
    const selected = childSelect.value;
    const custom = childNameInput.value.trim();
    name = custom || selected || randomName();
  }

  // Siblings
  const siblingNames = Array.from(
    siblingsChips.querySelectorAll(".pill-selected")
  ).map((chip) => chip.textContent);

  const extra = siblingsExtraInput.value
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  const allSiblings = [...siblingNames, ...extra];
  const siblingsString = allSiblings.length ? allSiblings.join(", ") : null;

  // Favourite thing / theme
  const theme = favouriteInput.value.trim() || "";

  const style =
    Array.from(stylePills).find((p) =>
      p.classList.contains("pill-selected")
    )?.dataset.style || "gentle";

  const length =
    Array.from(lengthPills).find((p) =>
      p.classList.contains("pill-selected")
    )?.dataset.length || "short";

  storyTextEl.textContent = "BuddyBug is weaving your story...";

  const payload = {
    child_name: name,
    siblings: siblingsString,
    favourite_thing: theme,
    style,
    length,
    category: currentCategory || null,
  };

  try {
    const res = await fetch(`${API_BASE}/story`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) throw new Error(`Server error ${res.status}`);
    const data = await res.json();

    const entry = {
      id: Date.now(),
      title: name || "Someone special",
      story: data.story,
      meta: {
        style,
        length,
        category: currentCategory,
      },
    };

    currentStory = entry;
    showStory(entry);
  } catch (err) {
    console.error(err);
    storyTextEl.textContent =
      "Something went wrong while creating your story. Is the BuddyBug server running?";
  }
}

function showStory(entry) {
  storyTitleEl.textContent = `A story for ${entry.title}`;
  storyTextEl.textContent = entry.story;
  showScreen("screen-story");
  navItems.forEach((b) => b.classList.remove("nav-active"));
  updateFavButton();
}

// Favourite toggle
function updateFavButton() {
  if (!currentStory) {
    btnFavToggle.textContent = "☆";
    return;
  }
  const inFavs = favourites.some((f) => f.id === currentStory.id);
  btnFavToggle.textContent = inFavs ? "★" : "☆";
}

btnFavToggle.addEventListener("click", () => {
  if (!currentStory) return;
  const idx = favourites.findIndex((f) => f.id === currentStory.id);
  if (idx >= 0) {
    favourites.splice(idx, 1);
  } else {
    favourites.unshift(currentStory);
    if (favourites.length > 50) favourites = favourites.slice(0, 50);
  }
  save("bb_mobile_favourites_v1", favourites);
  updateFavButton();
  renderFavourites();
});

// Bedtime mode toggle
let bedtimeOn = false;
btnBedtimeMode.addEventListener("click", () => {
  bedtimeOn = !bedtimeOn;
  document.body.classList.toggle("bedtime-mode", bedtimeOn);
  btnBedtimeMode.textContent = bedtimeOn
    ? "🌙 Bedtime mode on"
    : "🌙 Bedtime mode";
});

// Read myself / auto-narrate (stub)
btnReadMyself.addEventListener("click", () => {
  storyTextEl.scrollTo({ top: 0, behavior: "smooth" });
});

btnAutoNarrate.addEventListener("click", () => {
  alert(
    "Auto-narration will be added later in the build. For now, read together!"
  );
});

// Main navigation
btnSurprise.addEventListener("click", () => {
  generateStory("surprise");
  showScreen("screen-story");
});

btnBuilder.addEventListener("click", () => {
  showScreen("screen-builder");
  navItems.forEach((b) => b.classList.remove("nav-active"));
  document
    .querySelector('.nav-item[data-nav-target="screen-builder"]')
    ?.classList.add("nav-active");
});

btnFavourites.addEventListener("click", () => {
  renderFavourites();
  showScreen("screen-favourites");
  navItems.forEach((b) => b.classList.remove("nav-active"));
  document
    .querySelector('.nav-item[data-nav-target="screen-favourites"]')
    ?.classList.add("nav-active");
});

btnGenerate.addEventListener("click", () => {
  generateStory("normal");
  showScreen("screen-story");
});

// Back buttons
backFromBuilder.addEventListener("click", () => {
  showScreen("screen-home");
  navItems.forEach((b) => b.classList.remove("nav-active"));
  document
    .querySelector('.nav-item[data-nav-target="screen-home"]')
    ?.classList.add("nav-active");
});

backFromStory.addEventListener("click", () => {
  showScreen("screen-home");
  navItems.forEach((b) => b.classList.remove("nav-active"));
  document
    .querySelector('.nav-item[data-nav-target="screen-home"]')
    ?.classList.add("nav-active");
});

backFromFavourites.addEventListener("click", () => {
  showScreen("screen-home");
  navItems.forEach((b) => b.classList.remove("nav-active"));
  document
    .querySelector('.nav-item[data-nav-target="screen-home"]')
    ?.classList.add("nav-active");
});

// Init
renderChildren();
renderFavourites();
showScreen("screen-home");
