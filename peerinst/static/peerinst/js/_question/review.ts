/*********/

/* model */

/*********/
let model: {
  submitAllowed: boolean;
};

function initModel() {
  model = {
    submitAllowed: false
  };
}

/**********/

/* update */

/**********/
function allowSubmit() {
  model.submitAllowed = true;
  submitButtonView();
}

/********/

/* view */

/********/
function view() {
  submitButtonView();
  showMeMore();
}

function submitButtonView() {
  if (model.submitAllowed) {
    // $FlowFixMe
    document.getElementById("answer-form").disabled = false;
  } else {
    // $FlowFixMe
    document.getElementById("answer-form").disabled = true;
  }
}

function showMeMore() {
  [].forEach.call(document.querySelectorAll(".expand-button"), function (el, i) {
    el.addEventListener("click", function () {
      const els = document.getElementsByClassName(`hidden-${el.getAttribute("data-rationale-iterator")}`);
      const showCounter = document.getElementById(`show-counter-${el.getAttribute("data-rationale-iterator")}`);
      let shownCounter = 0;

      for (let i = 0; i < els.length; i++) {
        if (els[i].hidden == true && shownCounter < 2) {
          els[i].hidden = false;
          shownCounter++;

          if (i == els.length - 1) {
            el.hidden = true;
            break;
          }

          showCounter.setAttribute("value", +showCounter.getAttribute("value") + 1);
        }
      }
    });
  });
}

/*************/

/* listeners */

/*************/
function listeners() {
  [].forEach.call(document.querySelectorAll("#submit-answer-form input[type=radio]"), el => el.addEventListener("click", allowSubmit));
}

/********/

/* init */

/********/
export function init() {
  initModel();
  view();
  listeners();
}