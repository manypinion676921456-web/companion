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
    bubble.textContent = text;

    msg.appendChild(avatar);
    msg.appendChild(bubble);
    chatWindow.appendChild(msg);
    scrollToBottom();
}

function setThinking(isThinking) {
    coreOrb.classList.toggle("is-thinking", isThinking);
    coreStatus.classList.toggle("is-thinking", isThinking);
    statusText.textContent = isThinking ? "thinking…" : "idle";
}

// Placeholder — swap this out for the real Avcore call later.
function getAvcoreResponse(userText) {
    return new Promise((resolve) => {
        const delay = 500 + Math.random() * 700;
        setTimeout(() => {
            resolve(
                `(placeholder) Avcore isn't wired up yet, so I can't actually answer "${userText}" — this is just confirming the message pipeline works.`
            );
        }, delay);
    });
}

composerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = messageInput.value.trim();
    if (!text) return;

    addMessage(text, "user");
    messageInput.value = "";
    setThinking(true);

    const reply = await getAvcoreResponse(text);

    setThinking(false);
    addMessage(reply, "avcore");
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