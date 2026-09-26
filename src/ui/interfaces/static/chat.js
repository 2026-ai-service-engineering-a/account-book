// 채팅 화면의 JS. 이 화면만 HTMX로 모자라서 둔다(ui-design 5장) — 한 파일에서 끝낸다.
// 서버가 SSE로 보내는 조각을 이어 붙이기만 한다. 무엇을 그릴지는 서버가 정한다.
(() => {
  const log = document.getElementById("chat-log");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const send = form.querySelector("button[type=submit]");

  const follow = () => log.lastElementChild?.scrollIntoView({ block: "end", behavior: "smooth" });
  const append = (html) => { log.insertAdjacentHTML("beforeend", html); follow(); };
  const lock = (on) => { input.disabled = on; send.disabled = on; if (!on) input.focus(); };

  // 진행 줄은 말풍선이 아니다. 답이 오면 사라진다(chat.md 7장).
  function progress(text) {
    let line = document.getElementById("chat-progress");
    if (!line) {
      append('<div class="thinking" id="chat-progress"></div>');
      line = document.getElementById("chat-progress");
    }
    line.textContent = text;
  }
  const clearProgress = () => document.getElementById("chat-progress")?.remove();

  function handle(name, data, live) {
    if (name === "tool") {
      progress(data);
    } else if (name === "token") {
      if (!live) {
        clearProgress();
        append('<div class="bubble bot"></div>');
        live = log.lastElementChild;
      }
      live.textContent += data;
      follow();
    } else if (name === "message") {
      clearProgress();
      live?.remove();
      append(data);
      return null;
    } else if (name === "proposal" || name === "error") {
      clearProgress();
      append(data);
    } else if (name === "done") {
      clearProgress();
    }
    return live;
  }

  async function stream(url, body) {
    lock(true);
    progress("생각하는 중…");
    let live = null;
    try {
      const response = await fetch(url, { method: "POST", body });
      if (!response.ok || !response.body) throw new Error(String(response.status));
      const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
      let buffer = "";
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += value;
        let cut;
        while ((cut = buffer.indexOf("\n\n")) >= 0) {
          const block = buffer.slice(0, cut);
          buffer = buffer.slice(cut + 2);
          let name = "message";
          const data = [];
          for (const line of block.split("\n")) {
            if (line.startsWith("event: ")) name = line.slice(7);
            else if (line.startsWith("data: ")) data.push(line.slice(6));
          }
          live = handle(name, data.join("\n"), live);
        }
      }
    } catch {
      // 자동으로 영원히 재시도하지 않는다. 사람이 다시 보낸다(chat.md 4.2).
      clearProgress();
      const line = document.createElement("div");
      line.className = "error-line";
      line.setAttribute("role", "alert");
      line.textContent = "연결이 끊겼어요. 다시 보내 주세요.";
      log.append(line);
      follow();
    } finally {
      lock(false);
    }
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    document.getElementById("chat-empty")?.remove();
    // 서버를 기다리지 않고 내 말풍선부터 그린다(chat.md 6장)
    const bubble = document.createElement("div");
    bubble.className = "bubble me";
    bubble.textContent = text;
    log.append(bubble);
    input.value = "";
    stream("/chat", new URLSearchParams({ text }));
  });

  input.addEventListener("keydown", (event) => {
    // 한글 조합 중의 Enter는 글자를 확정하는 키다. 보내지 않는다.
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  log.addEventListener("click", (event) => {
    const example = event.target.closest("[data-example]");
    if (example) {
      input.value = example.dataset.example;
      form.requestSubmit();
      return;
    }
    const button = event.target.closest("[data-decision]");
    if (!button) return;
    const card = button.closest(".card-confirm");
    const decision = button.dataset.decision;
    // 누른 뒤에 잠근다 — 두 번 눌러 같은 제안이 두 번 가지 않게(chat.md 5.2)
    card.querySelector(".actions").innerHTML =
      `<span class="done">${decision === "confirm" ? "확인했어요" : "취소했어요"}</span>`;
    stream(`/chat/proposals/${encodeURIComponent(card.dataset.proposalId)}/${decision}`, new URLSearchParams());
  });

  if (input.value) input.focus();
})();
