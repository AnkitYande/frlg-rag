// ── Config ────────────────────────────────────────────────────────────────────
// In local dev this points to your Flask server.
// On GitHub Pages it points to your Render URL.
const API_BASE = "http://localhost:5000";

// ── DOM refs ──────────────────────────────────────────────────────────────────
const chatWindow    = document.getElementById("chatWindow");
const questionInput = document.getElementById("questionInput");
const sendBtn       = document.getElementById("sendBtn");
const statusDot     = document.getElementById("statusDot");
const chunkDrawer   = document.getElementById("chunkDrawer");
const chunkList     = document.getElementById("chunkList");
const closeDrawer   = document.getElementById("closeDrawer");

// ── State ─────────────────────────────────────────────────────────────────────
let lastChunks = [];   // chunks from most recent API response

// ── Startup ───────────────────────────────────────────────────────────────────
window.addEventListener("DOMContentLoaded", () => {
  checkHealth();
  showWelcome();
  setupListeners();
});

// ── Health check ──────────────────────────────────────────────────────────────
async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`, { method: "GET" });
    if (res.ok) {
      statusDot.className = "status-dot online";
      statusDot.title = "Professor Oak's Lab is open!";
    } else {
      throw new Error("not ok");
    }
  } catch {
    statusDot.className = "status-dot offline";
    statusDot.title = "Lab is currently closed — API offline";
  }
}

// ── Welcome message ───────────────────────────────────────────────────────────
function showWelcome() {
  appendOakMessage(
    "Ah, there you are! I've been waiting. " +
    "I'm Professor Oak — this lab holds my research notes on the Kanto region. " +
    "Ask me anything about your FireRed or LeafGreen journey: where to find Pokémon, " +
    "how to tackle Gym Leaders, hidden items... I'm here to help you fill that Pokédex!",
    null   // no chunks for welcome message
  );
}

// ── Event listeners ───────────────────────────────────────────────────────────
function setupListeners() {
  sendBtn.addEventListener("click", handleSend);
  questionInput.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  });

  // Hint chips
  document.querySelectorAll(".hint-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      questionInput.value = chip.dataset.q;
      handleSend();
    });
  });

  // Close chunk drawer
  closeDrawer.addEventListener("click", () => {
    chunkDrawer.classList.remove("open");
  });
}

// ── Main send flow ────────────────────────────────────────────────────────────
async function handleSend() {
  const question = questionInput.value.trim();
  if (!question) return;

  questionInput.value = "";
  setInputDisabled(true);

  appendUserMessage(question);
  const typingEl = appendTypingIndicator();

  try {
    const data = await askAPI(question);
    typingEl.remove();
    appendOakMessage(data.answer, data.chunks);
  } catch (err) {
    typingEl.remove();
    appendOakMessage(
      "Hmm, it seems my research notes are temporarily unavailable. " +
      "Try again in a moment, young Trainer.",
      null
    );
    console.error("API error:", err);
  }

  setInputDisabled(false);
  questionInput.focus();
}

// ── API call ──────────────────────────────────────────────────────────────────
async function askAPI(question) {
  const res = await fetch(`${API_BASE}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ── Message renderers ─────────────────────────────────────────────────────────
function appendUserMessage(text) {
  const msg = document.createElement("div");
  msg.className = "msg user";
  msg.innerHTML = `
    <div class="bubble-wrap">
      <div class="sender-label">You</div>
      <div class="bubble">${escapeHtml(text)}</div>
    </div>
    <div class="avatar-wrap">🧢</div>
  `;
  chatWindow.appendChild(msg);
  scrollToBottom();
}

function appendOakMessage(text, chunks) {
  const msg = document.createElement("div");
  msg.className = "msg oak";

  // Format Oak's response — convert line breaks
  const formattedText = escapeHtml(text).replace(/\n/g, "<br/>");

  let chunksButtonHtml = "";
  if (chunks && chunks.length > 0) {
    chunksButtonHtml = `<button class="chunks-btn" data-chunks-id="${Date.now()}">📋 See research notes used (${chunks.length})</button>`;
  }

  msg.innerHTML = `
    <div class="avatar-wrap">🌿</div>
    <div class="bubble-wrap">
      <div class="sender-label">Professor Oak</div>
      <div class="bubble">${formattedText}</div>
      ${chunksButtonHtml}
    </div>
  `;

  // Wire up the chunks button
  if (chunks && chunks.length > 0) {
    const btn = msg.querySelector(".chunks-btn");
    btn.addEventListener("click", () => showChunks(chunks));
  }

  chatWindow.appendChild(msg);
  scrollToBottom();
}

function appendTypingIndicator() {
  const msg = document.createElement("div");
  msg.className = "msg oak";
  msg.innerHTML = `
    <div class="avatar-wrap">🌿</div>
    <div class="bubble-wrap">
      <div class="sender-label">Professor Oak</div>
      <div class="bubble">
        <div class="typing-indicator">
          <span></span><span></span><span></span>
        </div>
      </div>
    </div>
  `;
  chatWindow.appendChild(msg);
  scrollToBottom();
  return msg;
}

// ── Chunk drawer ──────────────────────────────────────────────────────────────
function showChunks(chunks) {
  chunkList.innerHTML = "";

  chunks.forEach((chunk, i) => {
    const card = document.createElement("div");
    card.className = "chunk-card";

    const sourceBadgeClass = chunk.source === "serebii" ? "serebii" : "bulbapedia";
    const sourceLabel      = chunk.source === "serebii" ? "Serebii" : "Bulbapedia";
    const similarityPct    = Math.round((1 - chunk.distance) * 100);

    card.innerHTML = `
      <div class="chunk-card-title">${escapeHtml(chunk.heading)}</div>
      <div class="chunk-card-source">
        <span class="source-badge ${sourceBadgeClass}">${sourceLabel}</span>
        ${escapeHtml(chunk.page_title)}
      </div>
      <div class="chunk-card-preview">${escapeHtml(chunk.preview)}…</div>
      <div class="chunk-card-score">
        Similarity: ${similarityPct}% &nbsp;|&nbsp;
        <a href="${chunk.source_url}" target="_blank" rel="noopener">View source ↗</a>
      </div>
    `;
    chunkList.appendChild(card);
  });

  chunkDrawer.classList.add("open");
}

// ── Utilities ─────────────────────────────────────────────────────────────────
function scrollToBottom() {
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function setInputDisabled(disabled) {
  questionInput.disabled = disabled;
  sendBtn.disabled = disabled;
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
