import { buildReq } from "../../ajax";
import { clear } from "../../utils";

/*********/

/* model */

/*********/
type Thread = {
  id: number;
  title: string;
  lastReply: {
    author: string;
    content: string;
  };
  nNew: number;
  link: string;
};
type Message = Thread;
let model: {
  open: boolean;
  messages: Array<Message>;
  urls: {
    markReadUrl: string;
    messagesUrl: string;
  };
};

function initModel(urls: {
  markReadUrl: string;
  messagesUrl: string;
}): void {
  model = {
    open: false,
    messages: [],
    urls
  };
}

/**********/

/* update */

/**********/
function update(): void {
  getMessages();
}

function toggleMessages(): void {
  const header = document.querySelector(".messages");
  document.querySelectorAll(".header--togglable > *").forEach(header_ => {
    if (header_ != header && header_.hasAttribute("open")) {
      if (header_.shadowRoot) {
        header_.shadowRoot.querySelector(".header__icon").dispatchEvent(new Event("click"));
      } else {
        header_.querySelector(".header__icon").dispatchEvent(new Event("click"));
      }
    }
  });
  model.open = !model.open;
  messagesView();
}

function getMessages(): void {
  const url = model.urls.messagesUrl;
  const req = buildReq({}, "get");
  fetch(url, req).then(resp => resp.json()).then(data => {
    model.messages = data.threads.map(message => ({
      id: message.id,
      title: message.title,
      lastReply: {
        author: message.last_reply.author,
        content: message.last_reply.content,
        date: message.last_reply.date
      },
      nNew: message.n_new,
      link: message.link
    }));
    messagesView();
  });
}

async function markAllRead(): Promise<void> {
  const req = buildReq({}, "post");
  const resp = await fetch(model.urls.markReadUrl, req);

  if (resp.ok) {
    model.messages.forEach(message => {
      message.nNew = 0;
    });
  }

  messagesView();
}

async function markRead(event: MouseEvent, message: Message, div: HTMLDivElement): Promise<void> {
  event.stopPropagation();
  const req = buildReq({
    id: message.id
  }, "post");
  const resp = await fetch(model.urls.markReadUrl, req);

  if (resp.ok) {
    message.nNew = 0;
  }

  messageView(message, div);
  badgeView();
}

/********/

/* view */

/********/
function view(): void {
  messagesView();
}

function messagesView(): void {
  const messages = document.querySelector(".messages");
  const badge = messages?.querySelector(".messages__icon__badge");
  const messagesList = messages?.querySelector(".messages__messages");

  if (!messages || !badge || !messagesList) {
    return;
  }

  badgeView();
  clear(messagesList);
  document.querySelector(".messages__read-all-btn").classList.add("hidden");
  const nNew = model.messages.filter(message => message.nNew > 0).length;

  if (nNew) {
    document.querySelector(".messages__read-all-btn").classList.remove("hidden");
  }

  if (model.messages.length) {
    model.messages.map(function (message) {
      messagesList.appendChild(messageView(message));
    });
  } else {
    messagesList.appendChild(noMessageView());
  }

  if (model.open) {
    messages.setAttribute("open", "");
    messages.classList.add("messages--open");
  } else {
    messages.removeAttribute("open");
    messages.classList.remove("messages--open");
  }
}

function badgeView(): void {
  const badge = document.querySelector(".messages__icon__badge");
  const nNew = model.messages.filter(message => message.nNew > 0).length;

  if (nNew) {
    badge.textContent = nNew.toString();
    badge.style.display = "flex";
  } else {
    badge.textContent = "";
    badge.style.display = "none";
  }
}

function messageView(message: Message, div: HTMLDivElement | null | undefined = null): HTMLDivElement {
  if (div) {
    clear(div);
  } else {
    div = document.createElement("div");
    div.classList.add("message");
    div.addEventListener("click", () => {
      window.location.href = message.link;
    });
  }

  const title = document.createElement("div");
  title.classList.add("message__title");
  title.textContent = message.title;
  div.appendChild(title);

  if (message.nNew) {
    div.classList.add("message--new");
  } else {
    div.classList.remove("message--new");
  }

  if (message.nNew) {
    const new_ = document.createElement("div");
    new_.classList.add("message__new");
    new_.textContent = "New!";
    div.appendChild(new_);
  }

  if (message.lastReply.author) {
    const lastReply = document.createElement("div");
    lastReply.classList.add("message__last-reply");
    div.appendChild(lastReply);
    const content = document.createElement("span");
    content.classList.add("message__last-reply__content");
    content.textContent = message.lastReply.content;
    lastReply.appendChild(content);
    const author = document.createElement("div");
    author.classList.add("message__last-reply__author");
    author.innerHTML = `${message.lastReply.author} &middot; ${message.lastReply.date}`;

    if (message.nNew) {
      const markReadBtn = document.createElement("span");
      markReadBtn.classList.add("message__mark-read");
      markReadBtn.textContent = "clear";
      markReadBtn.title = "Mark read";
      markReadBtn.addEventListener("click", (event: MouseEvent) => markRead(event, message, div));
      author.appendChild(markReadBtn);
    }

    lastReply.appendChild(author);
  }

  return div;
}

function noMessageView(): HTMLDivElement {
  const div = document.createElement("div");
  div.textContent = "No messages";
  return div;
}

/*************/

/* listeners */

/*************/
function initEventListeners(): void {
  addMessagesOpenListener();
  addMarkAllReadListener();
}

function addMessagesOpenListener(): void {
  document.querySelector(".messages")?.addEventListener("click", function (event: MouseEvent) {
    event.stopPropagation();
  });
  document.querySelector(".messages__icon")?.addEventListener("click", function (event: MouseEvent) {
    toggleMessages();
  });
  document.body?.addEventListener("click", function (event: MouseEvent) {
    if (model.open) {
      event.stopPropagation();
      toggleMessages();
    }
  });
}

function addMarkAllReadListener(): void {
  document.querySelector(".messages__read-all-btn")?.addEventListener("click", () => markAllRead());
}

/********/

/* init */

/********/
export function init(urls: {
  markReadUrl: string;
  messagesUrl: string;
}): void {
  initModel(urls);
  update();
  view();
  initEventListeners();
}