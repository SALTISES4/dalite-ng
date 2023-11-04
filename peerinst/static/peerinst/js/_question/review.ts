/** *******/

/* model */

/** *******/
let model: {
  submitAllowed: boolean;
};

function initModel() {
  model = {
    submitAllowed: false,
  };
}

/** ********/

/* update */

/** ********/
function allowSubmit() {
  model.submitAllowed = true;
  submitButtonView();
}

/** ******/

/* view */

/** ******/
function view() {
  submitButtonView();
  showMeMore();
}

function submitButtonView() {
  // Toggle disabled
  const form = document.getElementById("answer-form") as HTMLFormElement;
  if (form && model.submitAllowed) {
    form.disabled = false;
  } else {
    form.disabled = true;
  }
}

function showMeMore() {
  [].forEach.call(
    document.querySelectorAll(".expand-button"),
    function (el: HTMLElement, i: number) {
      el.addEventListener("click", function () {
        const els = document.getElementsByClassName(
          `hidden-${el.getAttribute("data-rationale-iterator")}`,
        );
        const showCounter = document.getElementById(
          `show-counter-${el.getAttribute("data-rationale-iterator")}`,
        );
        let shownCounter = 0;

        for (let i = 0; i < els.length; i++) {
          if ((els[i] as HTMLElement).hidden == true && shownCounter < 2) {
            (els[i] as HTMLElement).hidden = false;
            shownCounter++;

            if (i == els.length - 1) {
              el.hidden = true;
              break;
            }

            if (showCounter) {
              showCounter.setAttribute(
                "value",
                `${+(showCounter.getAttribute("value") || 0) + 1}`,
              );
            }
          }
        }

        if (
          el.parentNode?.querySelectorAll("[class^=hidden][hidden]").length ==
          0
        ) {
          (el as HTMLElement).style.display = "none";
        }
      });
    },
  );
}

/** ***********/

/* listeners */

/** ***********/
function listeners() {
  [].forEach.call(
    document.querySelectorAll("#submit-answer-form input[type=radio]"),
    (el) => (el as HTMLInputElement).addEventListener("change", allowSubmit),
  );
}

/** ******/

/* init */

/** ******/
export function init() {
  initModel();
  view();
  listeners();
}
