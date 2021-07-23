import { buildReq } from "../ajax.js";
import { clear } from "../utils.ts";

/*********/
/* model */
/*********/

let model;

function initModel(flagQuestionUrl, getFlagQuestionReasonsUrl) {
  model = {
    flagQuestionReasons: [],
    urls: {
      flagQuestion: flagQuestionUrl,
      getFlagQuestionReasons: getFlagQuestionReasonsUrl,
    },
  };
  getFlagQuestionReasons();
}

function toggleFlagQuestion(question) {
  const open = question.getAttribute("open");
  const id = question.getAttribute("data-id");
  const form = question.querySelector(".flag-question__form");
  const icon = question.querySelector(".flag-question__btn");

  if (id === null) {
    console.log(
      "The flag question div needs a `data-id` attribute representing the " +
        "question pk.",
    );
  }

  if (open === null) {
    question.setAttribute("open", "");
    form.removeAttribute("hidden");
    icon.textContent = "flag";
  } else {
    question.removeAttribute("open");
    form.setAttribute("hidden", "");
    icon.textContent = "outlined_flag";
  }
}

async function getFlagQuestionReasons() {
  const req = buildReq({}, "get");
  const resp = await fetch(model.urls.getFlagQuestionReasons, req);
  if (!resp.ok) {
    console.log(resp);
  }
  const data = await resp.json();
  model.flagQuestionReasons = data.reasons;
  flagQuestionView();
}

async function flagQuestion(question) {
  const id = question.getAttribute("data-id");
  const select = question.querySelector(".flag-question__form__select");
  const reason = select.options[select.selectedIndex].value;

  const data = {
    id,
    reason,
  };
  const req = buildReq(data, "post");
  const resp = await fetch(model.urls.flagQuestion, req);
  if (!resp.ok) {
    console.log(resp);
  }
  toggleFlagQuestion(question);
}

function flagQuestionView() {
  [...document.getElementsByClassName("flag-question")].forEach((question) => {
    const select = question.querySelector(".flag-question__form select");
    clear(select);
    model.flagQuestionReasons.forEach((reason) => {
      const option = document.createElement("option");
      option.classList.add("flag-question__form__option");
      option.value = reason;
      option.textContent = reason;
      select.appendChild(option);
    });
  });
}

function addFlagQuestionListeners() {
  [...document.getElementsByClassName("flag-question")].forEach((question) => {
    question
      .querySelector(".flag-question__close")
      .addEventListener("click", (event) => {
        event.stopPropagation();
        toggleFlagQuestion(question);
      });
    question
      .querySelector(".flag-question__btn")
      .addEventListener("click", (event) => {
        event.stopPropagation();
        toggleFlagQuestion(question);
      });
    question
      .querySelector(".flag-question__form")
      .addEventListener("click", (event) => {
        event.stopPropagation();
      });
    question
      .querySelector(".flag-question__form")
      .addEventListener("submit", (event) => {
        event.preventDefault();
        flagQuestion(question);
      });
    document.body.addEventListener("click", () => {
      if (question.hasAttribute("open")) {
        toggleFlagQuestion(question);
      }
    });
  });
}

export async function init(getFlagQuestionReasonsUrl, flagQuestionUrl) {
  await initModel(flagQuestionUrl, getFlagQuestionReasonsUrl);
  addFlagQuestionListeners();
}
