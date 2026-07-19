// ---------------------------------------------------------
// Companion frontend — v1 scaffold
// Chat responses are simulated for now. Once Avcore's local
// inference layer exists, replace `getAvcoreResponse()` below
// with a real call into core/model/avcore.
// ---------------------------------------------------------

const chatWindow = document.getElementById("chatWindow");
const composerForm = document.getElementById("composerForm");
const messageInput = document.getElementById("messageInput");
const coreOrb = document.getElementById("coreOrb");
const coreStatus = document.getElementById("coreStatus");
const statusText = coreStatus.querySelector(".status-text");

let greetingRemoved = false;
let lastUserMessage = "";

function scrollToBottom() {
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function addMessage(text, from) {
  if (!greetingRemoved) {
    const greeting = chatWindow.querySelector(".greeting");
    if (greeting) greeting.remove();
    greetingRemoved = true;
  }

  const msg = document.createElement("div");
  msg.className = `msg from-${from}`;

  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  if (from === "user") avatar.textContent = "🙂";

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";

  const textEl = document.createElement("div");
  textEl.className = "msg-text";
  textEl.textContent = text;
  bubble.appendChild(textEl);

  if (from === "user") {
    lastUserMessage = text;
  }

  if (from === "avcore") {
    const correctBtn = document.createElement("button");
    correctBtn.className = "correct-btn";
    correctBtn.title = "Correct this answer (training)";
    correctBtn.innerHTML =
      '<svg viewBox="0 0 24 24" width="13" height="13"><path fill="currentColor" d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg>';
    correctBtn.addEventListener("click", () => openCorrectionBox(bubble, text, lastUserMessage));
    bubble.appendChild(correctBtn);
  }

  msg.appendChild(avatar);
  msg.appendChild(bubble);
  chatWindow.appendChild(msg);
  scrollToBottom();
}

function openCorrectionBox(bubble, originalAnswer, question) {
  if (bubble.querySelector(".correction-box")) return; // already open

  const box = document.createElement("div");
  box.className = "correction-box";
  box.innerHTML = `
    <textarea placeholder="Write the correct answer...">${originalAnswer}</textarea>
    <div class="correction-actions">
      <button class="correction-cancel" type="button">Cancel</button>
      <button class="correction-save" type="button">Save correction</button>
    </div>
  `;
  bubble.appendChild(box);

  const textarea = box.querySelector("textarea");
  textarea.focus();
  textarea.setSelectionRange(textarea.value.length, textarea.value.length);

  box.querySelector(".correction-cancel").addEventListener("click", () => box.remove());

  box.querySelector(".correction-save").addEventListener("click", async () => {
    const corrected = textarea.value.trim();
    if (!corrected) return;
    await saveCorrection(question, originalAnswer, corrected);
    box.innerHTML = `<span class="correction-saved-tag">✓ Saved for training</span>`;
    setTimeout(() => box.remove(), 1800);
  });
}

async function saveCorrection(question, originalAnswer, correctedAnswer) {
  try {
    await fetch("http://localhost:8000/train/correction", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        original_answer: originalAnswer,
        corrected_answer: correctedAnswer,
      }),
    });
  } catch (err) {
    console.error("Could not save correction:", err);
  }
}

function addLoadingMessage() {
  if (!greetingRemoved) {
    const greeting = chatWindow.querySelector(".greeting");
    if (greeting) greeting.remove();
    greetingRemoved = true;
  }

  const msg = document.createElement("div");
  msg.className = "msg from-avcore";
  msg.id = "loadingMsg";

  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble is-loading";
  bubble.innerHTML = '<div class="loading-bar"></div>';

  msg.appendChild(avatar);
  msg.appendChild(bubble);
  chatWindow.appendChild(msg);
  scrollToBottom();
}

function removeLoadingMessage() {
  const loading = document.getElementById("loadingMsg");
  if (loading) loading.remove();
}

function setThinking(isThinking) {
  coreOrb.classList.toggle("is-thinking", isThinking);
  coreStatus.classList.toggle("is-thinking", isThinking);
  statusText.textContent = isThinking ? "thinking…" : "idle";
}

const AVCORE_API_URL = "http://localhost:8000/chat";
const SESSION_ID = "default"; // will become per-user/session once accounts exist

async function getAvcoreResponse(userText) {
  try {
    const res = await fetch(AVCORE_API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userText, session_id: SESSION_ID }),
    });
    if (!res.ok) throw new Error(`Server responded ${res.status}`);
    const data = await res.json();
    return data.reply;
  } catch (err) {
    console.error("Avcore request failed:", err);
    return "Couldn't reach Avcore's core server. Make sure it's running (`uvicorn core.server:app --reload --port 8000`) and that Ollama is up.";
  }
}

composerForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = messageInput.value.trim();
  if (!text) return;

  addMessage(text, "user");
  messageInput.value = "";
  setThinking(true);
  addLoadingMessage();

  const reply = await getAvcoreResponse(text);

  removeLoadingMessage();
  setThinking(false);
  addMessage(reply, "avcore");
});

// ---------------------------------------------------------
// Model selector
// ---------------------------------------------------------

const modelSelect = document.getElementById("modelSelect");
const modelSelectBtn = document.getElementById("modelSelectBtn");
const modelSelectLabel = document.getElementById("modelSelectLabel");
const modelMenu = document.getElementById("modelMenu");

modelSelectBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  const isOpen = modelSelect.classList.toggle("is-open");
  modelSelectBtn.setAttribute("aria-expanded", isOpen);
});

modelMenu.querySelectorAll("li:not(.is-disabled)").forEach((item) => {
  item.addEventListener("click", () => {
    modelMenu.querySelectorAll("li").forEach((li) => li.classList.remove("is-selected"));
    item.classList.add("is-selected");
    modelSelectLabel.textContent = item.dataset.model;
    modelSelect.classList.remove("is-open");
  });
});

document.addEventListener("click", (e) => {
  if (!modelSelect.contains(e.target)) {
    modelSelect.classList.remove("is-open");
  }
});

// ---------------------------------------------------------
// Settings modal + accent color
// ---------------------------------------------------------

const settingsBtn = document.getElementById("settingsBtn");
const modalOverlay = document.getElementById("modalOverlay");
const modalClose = document.getElementById("modalClose");
const colorPicker = document.getElementById("colorPicker");
const swatches = document.querySelectorAll(".swatch");

const STORAGE_KEY = "companion.accentColor";

function applyAccentColor(hex) {
  document.documentElement.style.setProperty("--accent-core", hex);
  colorPicker.value = hex;
  swatches.forEach((sw) =>
    sw.classList.toggle("is-selected", sw.dataset.color.toLowerCase() === hex.toLowerCase())
  );
}

function saveAccentColor(hex) {
  try {
    localStorage.setItem(STORAGE_KEY, hex);
  } catch (err) {
    console.warn("Could not persist color preference:", err);
  }
}

// Restore saved color on load
(function initColor() {
  let saved = null;
  try {
    saved = localStorage.getItem(STORAGE_KEY);
  } catch (err) {
    console.warn("Could not read stored color preference:", err);
  }
  if (saved) applyAccentColor(saved);
})();

settingsBtn.addEventListener("click", () => modalOverlay.classList.add("is-open"));
modalClose.addEventListener("click", () => modalOverlay.classList.remove("is-open"));
modalOverlay.addEventListener("click", (e) => {
  if (e.target === modalOverlay) modalOverlay.classList.remove("is-open");
});

colorPicker.addEventListener("input", (e) => {
  applyAccentColor(e.target.value);
  saveAccentColor(e.target.value);
});

swatches.forEach((sw) => {
  sw.addEventListener("click", () => {
    const hex = sw.dataset.color;
    applyAccentColor(hex);
    saveAccentColor(hex);
  });
});