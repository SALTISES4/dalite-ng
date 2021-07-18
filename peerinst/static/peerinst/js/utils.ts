export function clear(node: HTMLElement): HTMLElement {
  while (node.hasChildNodes()) {
    node.removeChild(node.lastChild);
  }

  return node;
}
export function formatDatetime(datetime: Date): string {
  return `${datetime.toLocaleString("en-ca", {
    year: "numeric",
  })}-${datetime.toLocaleString("en-ca", {
    month: "2-digit",
  })}-${datetime.toLocaleString("en-ca", {
    day: "2-digit",
  })} ${datetime.toLocaleString("en-ca", {
    hour: "2-digit",
    hour12: false,
  })}:${datetime.toLocaleString("en-ca", {
    minute: "2-digit",
  })}`;
}
export function createSvg(name: string, useSprite = true): Element {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
  use.setAttributeNS(
    "http://www.w3.org/1999/xlink",
    "href",
    svgLink(name, useSprite),
  );
  svg.append(use);
  return svg;
}
export function svgLink(name: string, useSprite = true): string {
  if (useSprite) {
    return `#${name}`;
  }

  return `${window.location.protocol}//${window.location.host}/static/peerinst/icons.svg#${name}`;
}
export function showAlert(msg: string) {
  const fullPageBox = document.createElement("div");
  fullPageBox.classList.add("alert-box__full-page");
  fullPageBox.addEventListener("click", (event: MouseEvent) => {
    event.stopPropagation();
    fullPageBox.parentNode?.removeChild(fullPageBox);
  });
  document.body?.appendChild(fullPageBox);
  const box = document.createElement("div");
  box.classList.add("alert-box__box");
  box.addEventListener("click", (event: MouseEvent) =>
    event.stopPropagation(),
  );
  fullPageBox.appendChild(box);
  const span = document.createElement("span");
  span.classList.add("alert-box__msg");
  span.textContent = msg;
  box.appendChild(span);
  const ok = document.createElement("button");
  ok.classList.add("alert-box__btn", "mdc-button", "mdc-button--unelevated");
  ok.textContent = "Ok";
  box.appendChild(ok);
}
export function createElement(tag, text = "", attributes = {}) {
  const elem = document.createElement(tag);

  if (text) {
    elem.textContent = text;
  }

  Object.entries(attributes).forEach(([key, val]) => {
    elem.setAttribute(key, val);
  });
  return elem;
}
