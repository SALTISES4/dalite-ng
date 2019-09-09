import { buildReq } from "../../ajax.js";

/*********/
/* model */
/*********/

let model;

function initModel(data) {
  model = {
    urls: {
      daliteMessages: data.urls.daliteMessages,
      removeDaliteMessage: data.urls.removeDaliteMessage,
      saltiseImage: data.urls.saltiseImage,
    },
    messages: [],
  };
}

/**********/
/* update */
/**********/

async function update() {
  await getMessages();
}

async function getMessages() {
  const req = buildReq({}, "post");

  const resp = await fetch(model.urls.daliteMessages, req);
  const data = await resp.json();
  model.messages = data.messages.map(message => ({
    id: message.id,
    title: message.title,
    text: message.text,
    colour: message.colour,
    removable: message.removable,
    date: message.date,
    link: message.link,
    authors: message.authors.map(author => ({
      name: author.name,
      picture: author.picture,
    })),
  }));
}

async function removeMessage(message, div) {
  const data = {
    id: message.id,
  };
  const req = buildReq(data, "post");

  const resp = await fetch(model.urls.removeDaliteMessage, req);
  if (resp.ok) {
    removeMessageView(div);
  }
}

/********/
/* view */
/********/

function view() {
  messagesView();
}

function messagesView() {
  const messages = document.querySelector("#dalite-messages");
  if (model.messages.length) {
    messages.classList.remove("hidden");
    model.messages.forEach(message => {
      messages.appendChild(messageView(message));
    });
  } else {
    messages.remove();
  }
}

function messageView(message) {
  const container = document.createElement("div");
  container.classList.add("mdc-card");

  const content = document.createElement("div");
  if (message.link) {
    content.addEventListener("click", () => {
      window.location.assign(message.link);
    });
    content.style.setProperty("cursor", "pointer");
    content.title = message.link;
  }

  const title = document.createElement("div");
  title.classList.add("mdc-typography--title", "bold");
  title.textContent = message.title;
  content.appendChild(title);

  const caption = document.createElement("div");
  caption.classList.add("mdc-typography--caption");
  caption.textContent = message.date;
  content.appendChild(caption);

  const text = document.createElement("div");
  text.classList.add("mdc-typography--body1");
  text.innerHTML = message.text;
  content.appendChild(text);

  container.appendChild(content);

  const actions = document.createElement("div");
  actions.classList.add("mdc-card__actions");

  const images = document.createElement("div");
  images.classList.add("mdc-card__action-buttons");
  if (message.authors.length) {
    const authorsContainer = document.createElement("div");
    authorsContainer.classList.add("dalite-message__authors");
    message.authors.forEach(author => {
      const img = document.createElement("img");
      img.classList.add("dalite-message__authors_author");
      img.title = author.name;
      img.setAttribute(
        "src",
        author.picture ? author.picture : model.urls.saltiseImage,
      );
      img.setAttribute("alt", `Picture of ${author.name}`);
      authorsContainer.appendChild(img);
    });
    images.appendChild(authorsContainer);
  }
  actions.appendChild(images);

  if (message.removable) {
    const buttons = document.createElement("div");
    buttons.classList.add("mdc-card__action-icons");
    const remove = document.createElement("i");
    remove.classList.add(
      "mdc-icon-toggle",
      "material-icons",
      "mdc-theme--primary",
    );
    remove.textContent = "clear";
    remove.addEventListener("click", async () => {
      await removeMessage(message, container);
    });
    buttons.appendChild(remove);
    actions.appendChild(buttons);
  }

  container.appendChild(actions);
  container.style.setProperty("background-color", message.colour);

  return container;
}

function removeMessageView(node) {
  if (node.parentNode.childElementCount == 3) {
    node.parentNode.remove();
  } else {
    node.remove();
  }
}

/********/
/* init */
/********/

export async function init(data) {
  initModel(data);
  await update();
  view();
}
