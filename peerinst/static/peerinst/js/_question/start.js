import { buildReq } from "../ajax.js";
import { clear } from "../utils.ts";

/*********/
/* model */
/*********/

let model;

function initModel(submitUrl, quality, questionType) {
  model = {
    urls: {
      submitUrl,
    },
    quality,
    questionType,
  };
}

/**********/
/* update */
/**********/

function validateFormSubmit(event) {
  if (!document.getElementById("your-rationale")) {
    event.preventDefault();

    // Validate form
    const rationale = document.querySelector("#id_rationale");
    const choices = document.querySelectorAll(
      "#submit-answer-form input[type=radio]",
    );
    const choicesSet = new Set(
      Array.from(choices).map((choice) => choice.checked),
    );
    if (
      rationale.validity.valid &&
      (choicesSet.has(true) || model.questionType == "RO")
    ) {
      // If form is valid, check quality
      const data = {
        quality: model.quality,
        rationale: rationale.value,
      };

      const req = buildReq(data, "post");
      fetch(model.urls.submitUrl, req)
        .then((resp) => resp.json())
        .then((failed) => {
          if (failed.failed.length) {
            toggleQualityError(failed.failed, failed.error_msg);
            document.querySelector("#answer-form").disabled = false;
          } else {
            toggleQualityError();
            document.querySelector("#answer-form").disabled = true;
            document.querySelector("#submit-answer-form").submit();
          }
        })
        .catch((err) => console.log(err));
    } else {
      let errorMsg;
      if (!choicesSet.has(true)) {
        errorMsg = gettext("An answer choice is required.");
      } else {
        errorMsg = gettext("A rationale is required.");
      }
      addError(errorMsg);
    }
  }
}

/********/
/* view */
/********/

function addError(errorMsg) {
  const form = document.querySelector("#submit-answer-form");

  let div = document.querySelector(".errorlist");
  if (!div) {
    div = document.createElement("div");
  }
  clear(div);

  div.classList.add("errorlist");
  div.textContent = errorMsg;

  form.parentNode.insertBefore(div, form);

  return div;
}

function toggleQualityError(data, errorMsg) {
  if (data) {
    const div = addError(errorMsg);
    const ul = document.createElement("ul");
    div.append(ul);
    data.forEach((criterion) => {
      const li = document.createElement("li");
      li.textContent = criterion.name;
      li.title = criterion.description;
      ul.append(li);
    });
  } else {
    const err = document.querySelector("errorlist");
    if (err) {
      err.parentNode.removeChild(err);
    }
  }
}

/*************/
/* listeners */
/*************/

function initListeners() {
  addSubmitListener();
}

function addSubmitListener() {
  const input = document.getElementById("answer-form");
  if (input) {
    input.addEventListener("click", (event) => {
      validateFormSubmit(event);
    });
  }
}

/********/
/* init */
/********/

export function init(submitUrl, quality, questionType) {
  initModel(submitUrl, quality, questionType);
  initListeners();
}
