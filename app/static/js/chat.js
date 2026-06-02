// Czat realtime — Lab 8.
// Korzystamy z globalnego appSocket (z main.js); dołączamy do pokoju konwersacji
// i nasłuchujemy nowych wiadomości.

(() => {
  const messagesEl = document.getElementById("messages");
  const composer = document.getElementById("composer");
  if (!messagesEl || !composer || !window.appSocket) return;

  const conversationId = parseInt(messagesEl.dataset.conversationId, 10);
  const currentUserId = parseInt(messagesEl.dataset.currentUserId, 10);

  const socket = window.appSocket;

  socket.emit("join_conversation", { conversation_id: conversationId });

  // Auto-scroll na koniec po załadowaniu.
  messagesEl.scrollTop = messagesEl.scrollHeight;

  function appendMessage(msg) {
    const wasAtBottom = messagesEl.scrollHeight - messagesEl.scrollTop - messagesEl.clientHeight < 50;
    const div = document.createElement("div");
    div.className = "msg" + (msg.sender_id === currentUserId ? " mine" : "");
    div.textContent = msg.body;
    const time = document.createElement("span");
    time.className = "time";
    time.textContent = new Date(msg.sent_at).toLocaleTimeString("pl-PL", { hour: "2-digit", minute: "2-digit" });
    div.appendChild(time);
    messagesEl.appendChild(div);
    // Usuwamy ewentualny empty-state.
    const empty = messagesEl.querySelector(".empty-state");
    if (empty) empty.remove();
    if (wasAtBottom) messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  socket.on("new_message", (msg) => {
    if (msg.conversation_id !== conversationId) return;
    appendMessage(msg);
  });

  socket.on("error", (err) => {
    console.error("Socket error:", err);
  });

  const input = document.getElementById("msg-input");
  composer.addEventListener("submit", (e) => {
    e.preventDefault();
    const body = input.value.trim();
    if (!body) return;
    socket.emit("send_message", { conversation_id: conversationId, body });
    input.value = "";
    input.focus();
  });
})();
