import { buildReq } from "../../../../../peerinst/static/peerinst/js/ajax.js";
import { clear } from "../../../../../peerinst/static/peerinst/js/utils";
import * as d3 from "d3";
import { ReputationHeader } from "./header";

class StudentReputationHeader extends ReputationHeader {
  async init(shadow: ShadowRoot) {
    /** *******/

    /* model */

    /** *******/
    type Reputation = {
      name: string;
      description: string;
      reputation: number;
      badgeThresholds: Array<number>;
      badgeColour: string;
    };
    type Model = {
      id: number;
      element: StudentReputationHeader;
      reputationType: string;
      reputationUrl: string;
      reputations: Array<Reputation>;
      shadow: ShadowRoot;
    };
    const model: Model = {
      id: parseInt(this.reputationId),
      element: this,
      reputationStyleUrl: this.reputationStyleUrl,
      reputationType: "student",
      reputationUrl: this.reputationUrl,
      reputations: [],
      shadow,
    };

    /** ********/

    /* update */

    /** ********/
    async function update() {
      await getReputation();

      if (model.reputations.length) {
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
      model.reputations = data.reputations.map((reputation) => ({
        name: reputation.full_name,
        description: reputation.description,
        reputation: reputation.reputation,
        badgeThresholds: reputation.badge_thresholds,
        badgeColour: reputation.badge_colour,
      }));
      iconView();
      listView();
    }

    function toggleReputationList() {
      const header = model.element;
      document
        .querySelectorAll(".header--togglable > *")
        .forEach((header_) => {
          console.log(header_);

          if (header_ != header && header_.hasAttribute("open")) {
            if (header_.shadowRoot) {
              header_.shadowRoot
                .querySelector(".header__icon")
                .dispatchEvent(new Event("click"));
            } else {
              console.log(header_.querySelector("header__icon"));
              header_
                .querySelector(".header__icon")
                .dispatchEvent(new Event("click"));
            }
          }
        });
      model.element.open = !model.element.open;
      iconView();
      listView();
      toggleReputationView();
    }

    /** ******/

    /* view */

    /** ******/
    function view() {
      model.shadow.appendChild(styleView());
      const container = document.createElement("div");
      container.id = "container";
      model.shadow.appendChild(container);
      container.appendChild(iconView());
      container.appendChild(listView());
    }

    function iconView() {
      let icon = model.shadow.querySelector("#icon");

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
        // $FlowFixMe
        document.body?.addEventListener("click", (event: MouseEvent) => {
          if (model.element.open) {
            toggleReputationList();
          }
        });
      }

      return icon;
    }

    function listView() {
      let list = model.shadow.querySelector("#list");

      if (!list) {
        list = document.createElement("div");
        list.id = "list";
        list.addEventListener("click", (event: MouseEvent) => {
          event.stopPropagation();
        });
      }

      clear(list);
      model.reputations.forEach((reputation) => {
        // $FlowFixMe
        reputationView(list, reputation);
      });
      return list;
    }

    function reputationView(list: HTMLElement, reputation: Reputation) {
      const name = document.createElement("div");
      name.classList.add("list__name");
      name.textContent = `${reputation.name}`;
      name.title = reputation.description;
      list.appendChild(name);
      list.appendChild(progressView(reputation));
    }

    function progressView(reputation: Reputation): HTMLElement {
      if (window.innerWidth <= 500) {
        return mobileProgressView(reputation);
      }

      return desktopProgressView(reputation);
    }

    function desktopProgressView(reputation: Reputation): HTMLElement {
      const container = document.createElement("div");
      container.classList.add("badge");
      const width = Math.max(...reputation.badgeThresholds);
      const svg = d3
        .select(container)
        .append("svg")
        .attr("viewBox", "0 0 200 40")
        .append("g");
      svg
        .append("text")
        .attr("data-val", reputation.reputation)
        .attr("dominant-baseline", "central")
        .attr("x", 10)
        .attr("y", 20)
        .attr("class", "fill-primary badge__reputation")
        .attr("font-size", 16)
        .text(0);
      svg
        .append("rect")
        .attr("x", 40)
        .attr("y", 12)
        .attr("height", 16)
        .attr("width", 150)
        .attr("rx", 8)
        .attr("ry", 8)
        .attr("stroke", "var(--reputation-colour)")
        .attr("stroke-width", 1)
        .attr("fill", "none");
      svg
        .append("rect")
        .attr("class", "badge__bar")
        .attr("x", 40)
        .attr(
          "y",
          12 +
            Math.max(
              0,
              8 - Math.sqrt(16 * ((150 * reputation.reputation) / width)) / 2,
            ),
        )
        .attr(
          "height",
          Math.min(
            Math.sqrt(16 * ((150 * reputation.reputation) / width)),
            16,
          ),
        )
        .attr("rx", 8)
        .attr("ry", 8)
        .attr("stroke", "var(--reputation-colour)")
        .attr("stroke-width", 1)
        .attr("fill", "var(--reputation-colour)");
      reputation.badgeThresholds.forEach((threshold) => {
        const badge = svg.append("g");
        badge
          .append("path")
          .attr(
            "d",
            "M11 9.16V2c-5 .5-9 4.79-9 10s4 9.5 9 " +
              "10v-7.16c-1-.41-2-1.52-2-2.84s1-2.43 " +
              "2-2.84zM14.86 11H22c-.48-4.75-4-8.53-9-9v7.16c1 " +
              ".3 1.52.98 1.86 1.84zM13 14.84V22c5-.47 8.52-4.25 " +
              "9-9h-7.14c-.34.86-.86 1.54-1.86 1.84z",
          )
          .attr("height", 10)
          .attr("width", 10)
          .attr("fill", reputation.badgeColour)
          .attr("fill-opacity", reputation.reputation < threshold ? 0.5 : 1)
          .attr(
            "transform",
            "translate(" +
              `${Math.min(
                172.5,
                Math.max(38.5, 30 + (150 * threshold) / width),
              )}, ` +
              `${10.65}` +
              ")" +
              ` scale(${19.5 / 25})`,
          );

        if (reputation.reputation < threshold) {
          badge.append("title").text(`Next badge at ${threshold}`);
        } else {
          badge.append("title").text(`Obtained at ${threshold}`);
        }
      });
      return container;
    }

    function mobileProgressView(reputation: Reputation): HTMLElement {
      const container = document.createElement("div");
      container.classList.add("badge");
      const svg = d3
        .select(container)
        .append("svg")
        .attr("viewBox", "0 0 200 40")
        .append("g");
      svg
        .append("text")
        .attr("data-val", reputation.reputation)
        .attr("dominant-baseline", "central")
        .attr("x", 10)
        .attr("y", 20)
        .attr("class", "fill-primary badge__reputation")
        .attr("font-size", 16)
        .text(0);

      if (
        reputation.badgeThresholds[reputation.badgeThresholds.length - 1] <=
        reputation.reputation
      ) {
        const badge = svg.append("g");
        badge
          .append("path")
          .attr(
            "d",
            "M11 9.16V2c-5 .5-9 4.79-9 10s4 9.5 9 " +
              "10v-7.16c-1-.41-2-1.52-2-2.84s1-2.43 " +
              "2-2.84zM14.86 11H22c-.48-4.75-4-8.53-9-9v7.16c1 " +
              ".3 1.52.98 1.86 1.84zM13 14.84V22c5-.47 8.52-4.25 " +
              "9-9h-7.14c-.34.86-.86 1.54-1.86 1.84z",
          )
          .attr("height", 10)
          .attr("width", 10)
          .attr("fill", reputation.badgeColour)
          .attr("fill-opacity", 1)
          .attr(
            "transform",
            "translate(" +
              `${Math.min(172.5, Math.max(38.5, 30))}, ` +
              "10.65" +
              ")" +
              ` scale(${19.5 / 25})`,
          );
        badge
          .append("title")
          .text(`Obtained at ${reputation.badgeThresholds[0]}`);
      } else {
        const idx = reputation.badgeThresholds
          .map((t, i) => [t, i])
          .filter(([t, i]) => t > reputation.reputation)
          .map(([t, i]) => i)[0];
        let width;
        const thresholds = [];

        if (idx == 0) {
          width = reputation.badgeThresholds[0];
        } else {
          width =
            reputation.badgeThresholds[idx] -
            reputation.badgeThresholds[idx - 1];
          thresholds.push(reputation.badgeThresholds[idx - 1]);
        }

        thresholds.push(reputation.badgeThresholds[idx]);
        svg
          .append("rect")
          .attr("x", 40)
          .attr("y", 5)
          .attr("height", 32)
          .attr("width", 150)
          .attr("rx", 16)
          .attr("ry", 16)
          .attr("stroke", "var(--reputation-colour)")
          .attr("stroke-width", 1)
          .attr("fill", "none");
        svg
          .append("rect")
          .attr("class", "badge__bar")
          .attr("x", 40)
          .attr(
            "y",
            5 +
              Math.max(
                0,
                16 -
                  Math.sqrt(
                    72 *
                      Math.max(
                        thresholds.length == 1 ? 0 : 32,
                        (150 *
                          (reputation.reputation -
                            (thresholds.length == 1 ? 0 : thresholds[0]))) /
                          width,
                      ),
                  ) /
                    2,
              ),
          )
          .attr(
            "height",
            Math.min(
              Math.sqrt(
                72 *
                  Math.max(
                    thresholds.length == 1 ? 0 : 32,
                    (150 *
                      (reputation.reputation -
                        (thresholds.length == 1 ? 0 : thresholds[0]))) /
                      width,
                  ),
              ),
              32,
            ),
          )
          .attr("rx", 16)
          .attr("ry", 16)
          .attr("stroke", "var(--reputation-colour)")
          .attr("stroke-width", 2)
          .attr("fill", "var(--reputation-colour)");
        thresholds.forEach((threshold, i) => {
          const badge = svg.append("g");
          badge
            .append("path")
            .attr(
              "d",
              "M11 9.16V2c-5 .5-9 4.79-9 10s4 9.5 9 " +
                "10v-7.16c-1-.41-2-1.52-2-2.84s1-2.43 " +
                "2-2.84zM14.86 11H22c-.48-4.75-4-8.53-9-9v7.16c1 " +
                ".3 1.52.98 1.86 1.84zM13 14.84V22c5-.47 8.52-4.25 " +
                "9-9h-7.14c-.34.86-.86 1.54-1.86 1.84z",
            )
            .attr("height", 10)
            .attr("width", 10)
            .attr("fill", reputation.badgeColour)
            .attr("fill-opacity", reputation.reputation < threshold ? 0.5 : 1)
            .attr(
              "transform",
              "translate(" +
                `${Math.min(
                  155,
                  Math.max(
                    35,
                    30 +
                      (150 *
                        (i == 0 && thresholds.length > 1 ? 0 : threshold)) /
                        width,
                  ),
                )}, ` +
                "2.5" +
                ")" +
                ` scale(${40 / 25})`,
            );

          if (reputation.reputation < reputation.badgeThresholds[0]) {
            badge
              .append("title")
              .text(`Next badge at ${reputation.badgeThresholds[0]}`);
          } else {
            badge
              .append("title")
              .text(`Obtained at ${reputation.badgeThresholds[0]}`);
          }
        });
      }

      return container;
    }

    function toggleReputationView() {
      if (window.innerWidth <= 500) {
        return toggleMobileReputationView();
      }

      return toggleDesktopReputationView();
    }

    function toggleDesktopReputationView() {
      const duration = 500;
      const counts = model.shadow.querySelectorAll(".badge__reputation");
      const bars = model.shadow.querySelectorAll(".badge__bar");

      for (let i = 0; i < model.reputations.length; i++) {
        const reputation = model.reputations[i];
        const count = d3.select(counts[i]);
        const bar = d3.select(bars[i]);
        const width = Math.max(...reputation.badgeThresholds);

        if (model.element.open) {
          count
            .transition()
            .duration(duration)
            .ease(d3.easeCubicInOut)
            .tween("text", function () {
              const interpolate = d3.interpolate(
                this.textContent, // eslint-disable-line
                reputation.reputation,
              );
              return function (t) {
                this.textContent = Math.round(interpolate(t)); // eslint-disable-line
              };
            });
          bar
            .transition()
            .duration(duration)
            .ease(d3.easeCubicInOut)
            .attr(
              "width",
              Math.min((150 * reputation.reputation) / width, 150),
            );
        } else {
          count
            .transition()
            .duration(duration)
            .ease(d3.easeCubicInOut)
            .tween("text", function () {
              const interpolate = d3.interpolate(this.textContent, 0); // eslint-disable-line

              return function (t) {
                this.textContent = Math.round(interpolate(t)); // eslint-disable-line
              };
            });
          bar
            .transition()
            .duration(duration)
            .ease(d3.easeCubicInOut)
            .attr("width", 0);
        }
      }
    }

    function toggleMobileReputationView() {
      const duration = 500;
      const counts = model.shadow.querySelectorAll(".badge__reputation");
      const bars = model.shadow.querySelectorAll(".badge__bar");

      for (let i = 0; i < model.reputations.length; i++) {
        const reputation = model.reputations[i];
        const count = d3.select(counts[i]);
        const bar = d3.select(bars[i]);
        const idx = reputation.badgeThresholds
          .map((t, i) => [t, i])
          .filter(([t, i]) => t > reputation.reputation)
          .map(([t, i]) => i)[0];
        let width: number;
        const thresholds: Array<number> = [];

        if (idx == 0) {
          width = reputation.badgeThresholds[0];
        } else {
          width =
            reputation.badgeThresholds[idx] -
            reputation.badgeThresholds[idx - 1];
          thresholds.push(reputation.badgeThresholds[idx - 1]);
        }

        thresholds.push(reputation.badgeThresholds[idx]);

        if (model.element.open) {
          count
            .transition()
            .duration(duration)
            .ease(d3.easeCubicInOut)
            .tween("text", function () {
              const interpolate = d3.interpolate(
                this.textContent, // eslint-disable-line
                reputation.reputation,
              );
              return function (t) {
                this.textContent = Math.round(interpolate(t)); // eslint-disable-line
              };
            });
          bar
            .transition()
            .duration(duration)
            .ease(d3.easeCubicInOut)
            .attr(
              "width",
              Math.min(
                Math.max(
                  thresholds.length == 1 ? 0 : 32,
                  (150 *
                    (reputation.reputation -
                      (thresholds.length == 1 ? 0 : thresholds[0]))) /
                    width,
                ),
                150,
              ),
            );
        } else {
          count
            .transition()
            .duration(duration)
            .ease(d3.easeCubicInOut)
            .tween("text", function () {
              const interpolate = d3.interpolate(this.textContent, 0); // eslint-disable-line

              return function (t) {
                this.textContent = Math.round(interpolate(t)); // eslint-disable-line
              };
            });
          bar
            .transition()
            .duration(duration)
            .ease(d3.easeCubicInOut)
            .attr("width", 0);
        }
      }
    }

    function styleView() {
      const style = document.createElement("link");
      style.setAttribute("href", model.reputationStyleUrl);
      style.setAttribute("rel", "stylesheet");
      style.setAttribute("nonce", model.element.nonce_);
      return style;
    }

    /** ******/

    /* init */

    /** ******/
    view();
    await update();
  }
}

if (!customElements.get("student-reputation-header")) {
  customElements.define("student-reputation-header", StudentReputationHeader);
}
