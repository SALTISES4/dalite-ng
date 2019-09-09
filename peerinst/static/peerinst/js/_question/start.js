import { buildReq } from "../ajax.js";
import { clear } from "../utils.js";

/*********/
/* model */
/*********/

let model;

function initModel(submitUrl, quality) {
  model = {
    urls: {
      submitUrl: submitUrl,
    },
    quality: quality,
  };
}

/**********/
/* update */
/**********/

function validateFormSubmit(event) {
  if (!document.getElementById("your-rationale")) {
    event.preventDefault();
    const data = {
      quality: model.quality,
      rationale: document.querySelector("#id_rationale").value,
    };

    const req = buildReq(data, "post");
    fetch(model.urls.submitUrl, req)
      .then(resp => resp.json())
      .then(failed => {
        if (failed.failed.length) {
          toggleQualityError(failed.failed, failed.error_msg);
          document.querySelector("#answer-form").disabled = false;
        } else {
          toggleQualityError();
          document.querySelector("#answer-form").disabled = true;
          document.querySelector("#submit-answer-form").submit();
        }
      })
      .catch(err => console.log(err));
  }
}

/********/
/* view */
/********/

function toggleQualityError(data, errorMsg) {
  if (data) {
    const form = document.querySelector("#submit-answer-form");

    let div = document.querySelector(".errorlist");
    if (!div) {
      div = document.createElement("div");
    }
    clear(div);

    div.classList.add("errorlist");
    div.textContent = errorMsg;

    const ul = document.createElement("ul");
    div.append(ul);
    data.forEach(criterion => {
      const li = document.createElement("li");
      li.textContent = criterion.name;
      li.title = criterion.description;
      ul.append(li);
    });

    form.parentNode.insertBefore(div, form);
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
    input.addEventListener("click", event => {
      validateFormSubmit(event);
    });
  }
}

/********/
/* init */
/********/

export function init(submitUrl, quality) {
  initModel(submitUrl, quality);
  initListeners();
}
