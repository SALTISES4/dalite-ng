"use strict";

export function init(data) {
  function draw() {
    $(".progress-chart").each((i, el) => {
      const dataset =
        data[el.getAttribute("group")][el.getAttribute("assignment")];
      bundle.plotTimeSeries(el, dataset);
    });
  }
  draw();
  window.addEventListener("resize", draw);
}
