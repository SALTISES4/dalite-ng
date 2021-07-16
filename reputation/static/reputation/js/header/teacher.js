// @flow
"use strict";
import { buildReq } from "../../../../../peerinst/static/peerinst/js/ajax.js";
import { clear } from "../../../../../peerinst/static/peerinst/js/utils.js";
import { ReputationHeader } from "./header.js";

class TeacherReputationHeader extends ReputationHeader {
  async init(shadow: ShadowRoot) {
    /*********/
    /* model */
    /*********/

    type Reputation = {
      name: string,
      description: string,
      reputation: number,
    };

    type Model = {
      id: number,
      element: TeacherReputationHeader,
      reputation: ?number,
      reputationType: string,
      reputationUrl: string,
      reputations: Array<Reputation>,
      shadow: ShadowRoot,
    };

    const model: Model = {
      id: parseInt(this.reputationId),
      element: this,
      reputation: null,
      reputationStyleUrl: this.reputationStyleUrl,
      reputationType: "teacher",
      reputationUrl: this.reputationUrl,
      reputations: [],
      shadow,
    };

    /**********/
    /* update */
    /**********/
    this.update = update;

    async function update() {
      await getReputation();
      if (model.reputation !== null) {
        model.element.hidden = false;
      }
    }

    async function getReputation() {
      const postData = {
        reputation_type: model.reputationType,
        id: model.id,
      };
      const req = buildReq(postData, "post");
      const resp = await fetch(model.reputationUrl, req);
      const data = await resp.json();
      model.reputation = data.reputation;
      model.reputations = data.reputations.map((reputation) => ({
        name: reputation.full_name,
        description: reputation.description,
        reputation: reputation.reputation,
      }));
      iconView();
      listView();
    }

    function toggleReputationList() {
      const header = model.element;
      document
        .querySelectorAll(".header--togglable > *")
        .forEach((header_) => {
          if (header_ != header && header_.hasAttribute("open")) {
            if (header_.shadowRoot) {
              header_.shadowRoot
                .querySelector(".header__icon")
                .dispatchEvent(new Event("click"));
            } else {
              header_
                .querySelector(".header__icon")
                .dispatchEvent(new Event("click"));
            }
          }
        });
      model.element.open = !model.element.open;
      iconView();
      listView();
    }

    /********/
    /* view */
    /********/

    function view() {
      shadow.appendChild(styleView());

      const container = document.createElement("div");
      container.id = "container";
      shadow.appendChild(container);

      container.appendChild(iconView());
      container.appendChild(listView());
    }

    function iconView() {
      // $FlowFixMe
      let icon = shadow.getElementById("icon");

      if (!icon) {
        icon = document.createElement("div");
        icon.id = "icon";
        icon.classList.add("header__icon");
        icon.title = "Reputation";
        icon.addEventListener("click", (event: MouseEvent) => {
          event.stopPropagation();
          toggleReputationList();
        });

        const star = document.createElement("i");
        star.id = "icon__icon";
        star.textContent = "star";
        icon.appendChild(star);

        const span = document.createElement("span");
        span.id = "icon__reputation";
        if (model.reputation !== null && model.reputation !== undefined) {
          span.textContent = model.reputation.toString();
        }
        icon.appendChild(span);

        // $FlowFixMe
        document.body?.addEventListener("click", (event: MouseEvent) => {
          if (model.element.open) {
            toggleReputationList();
          }
        });
      } else if (model.reputation !== null && model.reputation !== undefined) {
        // $FlowFixMe
        shadow.getElementById("icon__reputation").textContent =
          model.reputation.toString();
      }

      return icon;
    }

    function listView() {
      // $FlowFixMe
      let list = shadow.getElementById("list");
      if (!list) {
        list = document.createElement("div");
        list.id = "list";
        list.addEventListener("click", (event: MouseEvent) => {
          event.stopPropagation();
        });
      }

      clear(list);

      headerView(list);

      model.reputations.forEach((reputation) => {
        reputationView(list, reputation);
      });

      return list;
    }

    function headerView(list: HTMLElement) {
      const name = document.createElement("div");
      name.classList.add("list__header");
      name.textContent = "Name";
      list.appendChild(name);

      const rep = document.createElement("div");
      rep.classList.add("list__header");
      rep.textContent = "Reputation";
      list.appendChild(rep);
    }

    function reputationView(list: HTMLElement, reputation: Reputation) {
      const name = document.createElement("div");
      name.classList.add("list__name");
      name.textContent = `${reputation.name}`;
      name.title = reputation.description;
      list.appendChild(name);

      const rep = document.createElement("div");
      rep.classList.add("list__reputation");
      rep.textContent = (
        Math.round(reputation.reputation * 100) / 100
      ).toString();
      list.appendChild(rep);
    }

    function styleView() {
      const style = document.createElement("link");
      style.setAttribute("href", model.reputationStyleUrl);
      style.setAttribute("rel", "stylesheet");
      style.setAttribute("nonce", model.element.nonce_);
      return style;
    }

    /********/
    /* init */
    /********/

    view();
    await update();
  }
}

if (!customElements.get("teacher-reputation-header")) {
  customElements.define("teacher-reputation-header", TeacherReputationHeader);
}
