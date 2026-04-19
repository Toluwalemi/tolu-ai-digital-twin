(function () {
  "use strict";

  // --- DOM elements ---
  var form = document.getElementById("chat-form");
  var input = document.getElementById("chat-input");
  var log = document.getElementById("chat-log");
  var suggestions = document.getElementById("suggestions");
  if (!form || !input || !log) return;

  // --- State ---
  var sessionId = sessionStorage.getItem("dt_session_id");
  if (!sessionId) {
    sessionId = crypto.randomUUID ? crypto.randomUUID() : _fallbackUUID();
    sessionStorage.setItem("dt_session_id", sessionId);
  }

  var history = [];
  var maxHistoryMessages = 20;
  var cooldownMs = 3000;
  var lastSentAt = 0;
  var isStreaming = false;

  // --- Helpers ---
  function _fallbackUUID() {
    return "xxxx-xxxx-xxxx-xxxx".replace(/x/g, function () {
      return ((Math.random() * 16) | 0).toString(16);
    });
  }

  function appendMessage(role, text) {
    var row = document.createElement("div");
    row.className = "chat-line chat-line--" + role;

    var prompt = document.createElement("span");
    prompt.className = "line-prompt";
    prompt.textContent = role === "assistant" ? "twin>" : "you>";

    var content = document.createElement("span");
    content.className = "line-content";
    content.textContent = text;

    row.appendChild(prompt);
    row.appendChild(content);
    log.appendChild(row);
    log.scrollTop = log.scrollHeight;
    return content;
  }

  function appendSeparator() {
    var sep = document.createElement("div");
    sep.className = "chat-separator";
    sep.setAttribute("aria-hidden", "true");
    log.appendChild(sep);
    log.scrollTop = log.scrollHeight;
  }

  function appendError(text) {
    var row = document.createElement("p");
    row.className = "chat-error";
    row.textContent = text;
    log.appendChild(row);
    log.scrollTop = log.scrollHeight;
  }

  function setFormDisabled(disabled) {
    input.disabled = disabled;
    var btn = form.querySelector("button");
    if (btn) btn.disabled = disabled;
  }

  function appendLoadingState() {
    var row = document.createElement("div");
    row.className = "chat-line chat-line--assistant chat-line--loading";

    var prompt = document.createElement("span");
    prompt.className = "line-prompt";
    prompt.textContent = "twin>";

    var content = document.createElement("span");
    content.className = "line-content";

    var spinner = document.createElement("span");
    spinner.className = "loading-spinner";
    spinner.setAttribute("aria-hidden", "true");
    spinner.textContent = "[~]";

    var label = document.createElement("span");
    label.textContent = " compiling answer";

    var dots = document.createElement("span");
    dots.className = "loading-dots";
    dots.setAttribute("aria-hidden", "true");

    var srText = document.createElement("span");
    srText.className = "sr-only";
    srText.textContent = "Assistant is generating a response";

    content.appendChild(spinner);
    content.appendChild(label);
    content.appendChild(dots);
    content.appendChild(srText);
    row.appendChild(prompt);
    row.appendChild(content);
    log.appendChild(row);
    log.scrollTop = log.scrollHeight;
    return row;
  }

  // --- Streaming ---

  async function streamAssistantResponse(userMessage, loadingRow) {
    var response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: userMessage,
        session_id: sessionId,
      }),
    });

    if (!response.ok) {
      var errText = await response.text();
      try {
        var errJson = JSON.parse(errText);
        throw new Error(errJson.error || errText || "Chat request failed.");
      } catch (e) {
        if (e.message) throw e;
        throw new Error(errText || "Chat request failed.");
      }
    }

    if (!response.body) {
      var text = await response.text();
      return text;
    }

    var reader = response.body.getReader();
    var decoder = new TextDecoder();
    var assistantText = "";
    var assistantNode = null;
    var nodeReady = false;

    function ensureNode() {
      if (nodeReady) return;
      if (loadingRow) {
        loadingRow.classList.remove("chat-line--loading");
        assistantNode = loadingRow.querySelector(".line-content");
        assistantNode.textContent = "";
      } else {
        assistantNode = appendMessage("assistant", "");
      }
      nodeReady = true;
    }

    while (true) {
      var chunkResult = await reader.read();
      if (chunkResult.done) break;
      ensureNode();
      assistantText += decoder.decode(chunkResult.value, { stream: true });
      assistantNode.textContent = assistantText;
      log.scrollTop = log.scrollHeight;
    }

    // Flush remaining bytes.
    assistantText += decoder.decode();
    ensureNode();
    assistantNode.textContent = assistantText;

    return assistantText;
  }

  // --- Suggestion chips ---

  if (suggestions) {
    suggestions.addEventListener("click", function (event) {
      var chip = event.target.closest(".chip");
      if (!chip) return;
      var question = chip.dataset.q;
      if (!question) return;
      input.value = question;
      chip.remove();
      if (!suggestions.querySelector(".chip")) {
        suggestions.style.display = "none";
      }
      form.dispatchEvent(
        new Event("submit", { bubbles: true, cancelable: true })
      );
    });
  }

  // --- Form submit ---

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    if (isStreaming) return;

    var now = Date.now();
    if (now - lastSentAt < cooldownMs) {
      var secondsLeft = Math.ceil((cooldownMs - (now - lastSentAt)) / 1000);
      appendError(
        "Cooldown active. Please wait " + secondsLeft + "s before sending again."
      );
      return;
    }

    var userText = input.value.trim();
    if (!userText) return;

    isStreaming = true;
    setFormDisabled(true);
    appendMessage("user", userText);
    input.value = "";

    history.push({ role: "user", content: userText });
    if (history.length > maxHistoryMessages) {
      history = history.slice(-maxHistoryMessages);
    }

    var loadingRow = null;

    try {
      lastSentAt = now;
      loadingRow = appendLoadingState();
      var assistantText = await streamAssistantResponse(userText, loadingRow);
      history.push({ role: "assistant", content: assistantText });
      if (history.length > maxHistoryMessages) {
        history = history.slice(-maxHistoryMessages);
      }
      appendSeparator();
    } catch (error) {
      if (
        loadingRow &&
        loadingRow.classList.contains("chat-line--loading")
      ) {
        loadingRow.remove();
      }
      appendError(
        "Error: unable to reach digital twin right now. Please try again."
      );
      console.error(error);
    } finally {
      isStreaming = false;
      setFormDisabled(false);
      input.focus();
    }
  });
})();
