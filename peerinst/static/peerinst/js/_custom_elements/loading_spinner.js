export class LoadingSpinner extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: "open" });

    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.classList.add("spinner");
    svg.setAttribute("viewBox", "0 0 100 100");
    shadow.appendChild(svg);

    const ring = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "circle",
    );
    ring.classList.add("spinner__ring");
    ring.setAttribute("cx", "50");
    ring.setAttribute("cy", "50");
    ring.setAttribute("r", "47");
    ring.setAttribute("fill", "transparent");
    ring.setAttribute("stroke-width", "6");
    svg.appendChild(ring);

    const segment = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "circle",
    );
    segment.classList.add("spinner__segment");
    segment.setAttribute("cx", "50");
    segment.setAttribute("cy", "50");
    segment.setAttribute("r", "47");
    segment.setAttribute("fill", "transparent");
    segment.setAttribute("stroke-width", "6");
    segment.setAttribute("stroke-dasharray", "200");
    segment.setAttribute("stroke-dashoffset", "0");
    svg.appendChild(segment);

    const style = document.createElement("style");
    style.textContent = `
.spinner {
  animation: 1.75s spin linear infinite;
}

.spinner__ring {
  stroke: var(--spinner-ring-stroke, #d3d3d3);
}

.spinner__segment {
  stroke: var(--spinner-segment-stroke, #f2f2f2);
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}`;
    const nonce = this.getAttribute("nonce") || this.nonce;
    if (nonce) {
      style.setAttribute("nonce", nonce);
    }
    shadow.appendChild(style);
  }
}
