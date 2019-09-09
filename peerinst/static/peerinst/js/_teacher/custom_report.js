import { buildReq } from "../ajax.js";
/*********/
/* model */
/*********/

let model;

function initModel(urls) {
  model = {
    urls: {
      evaluateRationale: urls.evaluateRationale,
    },
  };
}

/**********/
/* update */
/**********/

function update() {
  updateRationalesEvaluationAttributes();
}

function updateRationalesEvaluationAttributes() {
  document.querySelectorAll(".custom-report__rationale").forEach(rationale => {
    updateRationaleEvaluationAttributes(rationale);
  });
}

function updateRationaleEvaluationAttributes(rationale) {
  const evaluation = rationale.getAttribute("data-score");
  if (evaluation != "") {
    const evaluation_ = parseInt(evaluation);
    if (evaluation_ == 0) {
      rationale.querySelector(".flag").setAttribute("data-flagged", "");
      rationale.querySelectorAll(".star").forEach((star, i) => {
        star.removeAttribute("data-starred");
      });
    } else {
      rationale.querySelector(".flag").removeAttribute("data-flagged");
      rationale.querySelectorAll(".star").forEach((star, i) => {
        if (3 - i <= evaluation_) {
          star.setAttribute("data-starred", "");
        } else {
          star.removeAttribute("data-starred");
        }
      });
    }
  }
}

async function flagRationale(flag) {
  const rationale = flag.parentNode.parentNode;
  const data = {
    id: flag.parentNode.parentNode.getAttribute("data-id"),
    score: 0,
    redirect: false,
  };
  const req = buildReq(data, "post");

  const resp = await fetch(model.urls.evaluateRationale, req);
  if (resp.ok) {
    flag.setAttribute("data-flagged", "");
    rationale.setAttribute("data-score", "0");
  }
  updateRationaleEvaluationAttributes(rationale);
  rationaleEvaluationView();
}

async function evaluateRationale(star, score) {
  const rationale = star.parentNode.parentNode;
  const data = {
    id: star.parentNode.parentNode.getAttribute("data-id"),
    score: score,
    redirect: false,
  };
  const req = buildReq(data, "post");

  const resp = await fetch(model.urls.evaluateRationale, req);
  if (resp.ok) {
    flag.setAttribute("data-flagged", "");
    rationale.setAttribute("data-score", `${score}`);
  }
  updateRationaleEvaluationAttributes(rationale);
  rationaleEvaluationView();
}

/********/
/* view */
/********/

function view() {
  rationaleEvaluationView();
}

function rationaleEvaluationView() {
  document
    .querySelectorAll(".custom-report__rationale__evaluation")
    .forEach(rationale => {
      toggleFlagHover(rationale.querySelector(".flag"));
      rationale
        .querySelectorAll(".star")
        .forEach(star => toggleStarHover(star));
    });
}

function toggleFlagHover(flag, hovering = false) {
  if (hovering || flag.hasAttribute("data-flagged")) {
    flag.textContent = "flag";
  } else {
    flag.textContent = "outlined_flag";
  }
}

function toggleStarHover(star, hovering = false) {
  const stars = [...star.parentNode.getElementsByClassName("star")];
  const idx = stars.indexOf(star);
  stars.forEach((star, i) => {
    if (star.hasAttribute("data-starred") || (hovering && i >= idx)) {
      star.textContent = "star";
    } else {
      star.textContent = "star_border";
    }
  });
}

/*************/
/* listeners */
/*************/

function initListeners() {
  addFlagListeners();
  addEvaluateListeners();
}

function addFlagListeners() {
  document
    .querySelectorAll(".custom-report__rationale__evaluation .flag")
    .forEach(flag => {
      flag.addEventListener("mouseenter", () => toggleFlagHover(flag, true));
      flag.addEventListener("mouseleave", () => toggleFlagHover(flag, false));
      flag.addEventListener("click", () => flagRationale(flag));
    });
}

function addEvaluateListeners() {
  document
    .querySelectorAll(".custom-report__rationale__evaluation")
    .forEach(rationale => {
      rationale.querySelectorAll(".star").forEach((star, i) => {
        star.addEventListener("mouseenter", () => toggleStarHover(star, true));
        star.addEventListener("mouseleave", () =>
          toggleStarHover(star, false),
        );
        star.addEventListener("click", () => evaluateRationale(star, 3 - i));
      });
    });
}

/********/
/* init */
/********/

export function init(urls) {
  initModel(urls);
  update();
  view();
  initListeners();
}
