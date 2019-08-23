export class ReputationHeader extends HTMLElement {
  static get observedAttributes() {
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
  get open() {
    return this.hasAttribute("open");
  }
  get stale() {
    const stale = this.getAttribute("stale");
    if (!stale) {
      stale = "false";
      this.setAttribute("stale", stale);
    }
    return stale;
  }
  set hidden(val: boolean) {
    if (val) {
      this.setAttribute("hidden", "");
    } else {
      this.removeAttribute("hidden");
    }
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

    const shadow = this.attachShadow({ mode: "open" });

    this.hidden = true;

    this.init(shadow);
  }
  attributeChangedCallback(attrName, oldVal, newVal) {
    if (attrName === "stale") {
      // Update reputation score from server if element is stale
    }
  }
}
