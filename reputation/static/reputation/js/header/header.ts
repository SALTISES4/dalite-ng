export class ReputationHeader extends HTMLElement {
  static get observedAttributes() {
    // Any change to stale attribute should fire a refresh event
    return ["stale"];
  }

  get reputationUrl(): string {
    const url = this.getAttribute("reputation-url");

    if (!url) {
      throw new Error(
        "The reputation-header needs a `reputation-url` attribute",
      );
    }

    return url;
  }

  get reputationStyleUrl(): string {
    const style = this.getAttribute("reputation-style-url");

    if (!style) {
      throw new Error(
        "The reputation-header needs a `reputation-style-url` attribute",
      );
    }

    return style;
  }

  get reputationId(): string {
    const id = this.getAttribute("reputation-id");

    if (!id) {
      throw new Error(
        "The reputation-header needs a `reputation-id` attribute",
      );
    }

    return id;
  }

  get nonce_(): string {
    const nonce = this.getAttribute("nonce") || this.nonce;

    if (!nonce) {
      throw new Error(
        "The teacher-reputation-header needs a `nonce` attribute",
      );
    }

    return nonce;
  }

  get hidden() {
    return this.hasAttribute("hidden");
  }

  set hidden(val: boolean) {
    if (val) {
      this.setAttribute("hidden", "");
    } else {
      this.removeAttribute("hidden");
    }
  }

  get open() {
    return this.hasAttribute("open");
  }

  set open(val: boolean) {
    if (val) {
      this.setAttribute("open", "");
    } else {
      this.removeAttribute("open");
    }
  }

  constructor() {
    super();
    const shadow = this.attachShadow({
      mode: "open",
    });
    this.hidden = true;
    this.init(shadow);
  }

  attributeChangedCallback(attrName, oldVal, newVal) {
    if (attrName === "stale") {
      this.update();
    }
  }
}
