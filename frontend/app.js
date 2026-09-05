const API_URL = "https://rag-giao-thong-vietnam.onrender.com/ask";
const SESSION_ID_KEY = "rag_giaothong_session_id";

const messagesEl = document.querySelector("#messages");
const citationListEl = document.querySelector("#citationList");
const formEl = document.querySelector("#questionForm");
const inputEl = document.querySelector("#questionInput");
const sendButtonEl = document.querySelector("#sendButton");
const clearButtonEl = document.querySelector("#clearButton");
const apiStatusEl = document.querySelector("#apiStatus");
const quickPromptEls = document.querySelectorAll("[data-question]");

function getSessionId() {
  let sessionId = localStorage.getItem(SESSION_ID_KEY);
  if (!sessionId) {
    sessionId = `web-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    localStorage.setItem(SESSION_ID_KEY, sessionId);
  }
  return sessionId;
}

function setStatus(text, state = "idle") {
  apiStatusEl.className = `status-pill ${state}`;
  apiStatusEl.innerHTML = `<span></span>${escapeHtml(text)}`;
}

function addMessage(role, text) {
  const messageEl = document.createElement("div");
  messageEl.className = `message ${role}`;

  const avatarEl = document.createElement("div");
  avatarEl.className = "message-avatar";
  avatarEl.textContent = role === "user" ? "B" : role === "error" ? "!" : "AI";

  const bubbleEl = document.createElement("div");
  bubbleEl.className = "message-bubble";

  const labelEl = document.createElement("span");
  labelEl.className = "message-label";
  labelEl.textContent = role === "user" ? "B\u1ea1n" : role === "error" ? "L\u1ed7i" : "Tr\u1ee3 l\u00fd";

  const textEl = document.createElement("div");
  textEl.className = "message-text";
  textEl.textContent = text;

  bubbleEl.append(labelEl, textEl);
  messageEl.append(avatarEl, bubbleEl);
  messagesEl.appendChild(messageEl);
  messagesEl.scrollTop = messagesEl.scrollHeight;

  return messageEl;
}

function removeMessage(messageEl) {
  if (messageEl && messageEl.parentNode) {
    messageEl.parentNode.removeChild(messageEl);
  }
}

function shortText(value, maxLength = 520) {
  const text = String(value || "").replace(/\s+/g, " ").trim();
  if (text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, maxLength)}...`;
}

function renderCitations(citations) {
  citationListEl.innerHTML = "";

  if (!citations || citations.length === 0) {
    citationListEl.innerHTML =
      '<div class="empty-state"><strong>Ch\u01b0a t\u00ecm th\u1ea5y citation</strong><span>Backend ch\u01b0a tr\u1ea3 v\u1ec1 ngu\u1ed3n ph\u00f9 h\u1ee3p cho c\u00e2u h\u1ecfi n\u00e0y.</span></div>';
    return;
  }

  citations.forEach((citation, index) => {
    const cardEl = document.createElement("article");
    cardEl.className = "citation-card";

    const score = typeof citation.score === "number" ? citation.score.toFixed(3) : "--";
    const source = citation.source || "";

    cardEl.innerHTML = `
      <div class="citation-topline">
        <span class="citation-index">Ngu\u1ed3n ${index + 1}</span>
        <span class="score-badge">${escapeHtml(score)}</span>
      </div>
      <h3>${escapeHtml(citation.so_hieu || "Kh\u00f4ng r\u00f5 s\u1ed1 hi\u1ec7u")}</h3>
      <div class="citation-meta">
        <span>${escapeHtml(citation.ten_van_ban || "Kh\u00f4ng r\u00f5 t\u00ean v\u0103n b\u1ea3n")}</span>
        <span>${escapeHtml(citation.dieu || "Kh\u00f4ng r\u00f5 \u0111i\u1ec1u")} &middot; ${escapeHtml(citation.khoan || "Kh\u00f4ng r\u00f5 kho\u1ea3n")}</span>
      </div>
      <p class="citation-text">${escapeHtml(shortText(citation.text))}</p>
      <div class="citation-actions"></div>
    `;

    const actionsEl = cardEl.querySelector(".citation-actions");

    const useButtonEl = document.createElement("button");
    useButtonEl.type = "button";
    useButtonEl.className = "citation-button";
    useButtonEl.textContent = "Xem chi ti\u1ebft";
    useButtonEl.addEventListener("click", () => {
      addMessage("bot", `Ngu\u1ed3n: ${citation.citation || citation.so_hieu || "kh\u00f4ng r\u00f5"}\n\n${citation.text || ""}`);
    });
    actionsEl.appendChild(useButtonEl);

    if (source) {
      const linkEl = document.createElement("a");
      linkEl.className = "source-link";
      linkEl.href = source;
      linkEl.target = "_blank";
      linkEl.rel = "noreferrer";
      linkEl.textContent = "M\u1edf ngu\u1ed3n";
      actionsEl.appendChild(linkEl);
    }

    citationListEl.appendChild(cardEl);
  });
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

async function askBackend(question) {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
      top_k: 5,
      session_id: getSessionId(),
    }),
  });

  if (!response.ok) {
    throw new Error(`Backend returned ${response.status}`);
  }

  return response.json();
}

async function handleSubmit(event) {
  event.preventDefault();

  const question = inputEl.value.trim();
  if (!question) {
    return;
  }

  addMessage("user", question);
  inputEl.value = "";
  sendButtonEl.disabled = true;
  sendButtonEl.textContent = "\u0110ang g\u1eedi";
  setStatus("\u0110ang truy v\u1ea5n", "loading");
  const loadingEl = addMessage("bot", "\u0110ang t\u00ecm c\u0103n c\u1ee9 ph\u00e1p l\u00fd v\u00e0 t\u1ea1o c\u00e2u tr\u1ea3 l\u1eddi...");

  try {
    const result = await askBackend(question);
    removeMessage(loadingEl);
    setStatus("K\u1ebft n\u1ed1i backend", "online");
    if (result.was_rewritten && result.rewritten_question) {
      addMessage("bot", `M\u00ecnh hi\u1ec3u c\u00e2u h\u1ecfi n\u00e0y l\u00e0: ${result.rewritten_question}`);
    }
    addMessage("bot", result.answer || "Backend kh\u00f4ng tr\u1ea3 v\u1ec1 c\u00e2u tr\u1ea3 l\u1eddi.");
    renderCitations(result.citations || []);
  } catch (error) {
    removeMessage(loadingEl);
    setStatus("M\u1ea5t k\u1ebft n\u1ed1i", "offline");
    addMessage(
      "error",
      "Ch\u01b0a g\u1ecdi \u0111\u01b0\u1ee3c backend Render. D\u1ecbch v\u1ee5 c\u00f3 th\u1ec3 \u0111ang kh\u1edfi \u0111\u1ed9ng l\u1ea1i, h\u00e3y ch\u1edd kho\u1ea3ng 30-60 gi\u00e2y r\u1ed3i th\u1eed l\u1ea1i."
    );
    renderCitations([]);
  } finally {
    sendButtonEl.disabled = false;
    sendButtonEl.textContent = "G\u1eedi";
    inputEl.focus();
  }
}

formEl.addEventListener("submit", handleSubmit);

inputEl.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    formEl.requestSubmit();
  }
});

quickPromptEls.forEach((buttonEl) => {
  buttonEl.addEventListener("click", () => {
    inputEl.value = buttonEl.dataset.question || "";
    inputEl.focus();
  });
});

clearButtonEl.addEventListener("click", () => {
  messagesEl.innerHTML = "";
  renderCitations([]);
  localStorage.removeItem(SESSION_ID_KEY);
  addMessage(
    "bot",
    "M\u00ecnh \u0111\u00e3 t\u1ea1o phi\u00ean h\u1ed9i tho\u1ea1i m\u1edbi. B\u1ea1n h\u1ecfi c\u00e2u ti\u1ebfp theo nha."
  );
  inputEl.focus();
});

addMessage(
  "bot",
  "Ch\u00e0o b\u1ea1n. H\u00e3y nh\u1eadp c\u00e2u h\u1ecfi v\u1ec1 lu\u1eadt giao th\u00f4ng, m\u00ecnh s\u1ebd tr\u1ea3 l\u1eddi d\u1ef1a tr\u00ean d\u1eef li\u1ec7u RAG v\u00e0 hi\u1ec3n th\u1ecb ngu\u1ed3n tr\u00edch d\u1eabn \u1edf b\u00ean ph\u1ea3i."
);
