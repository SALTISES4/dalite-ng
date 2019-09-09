import { initStudentProgress } from "./student_progress.js";
import { formatDatetime } from "../utils.js";
import { buildReq } from "../ajax.js";
import { editField } from "./common.js";

/*********/
/* model */
/*********/

let model;

function initModel(data) {
  model = {
    assignment: {
      hash: data.assignment.hash,
      distributionDate: data.assignment.distribution_date
        ? new Date(data.assignment.distribution_date)
        : null,
    },
    urls: {
      getAssignmentStudentProgress: data.urls.get_assignment_student_progress,
      sendStudentAssignment: data.urls.send_student_assignment,
      groupAssignmentUpdate: data.urls.group_assignment_update,
      distributeAssignment: data.urls.distribute_assignment,
    },
    translations: {
      distribute: data.translations.distribute,
      distributed: data.translations.distributed,
      distributionWarning: data.translations.distribution_warning,
    },
  };
}

/**********/
/* update */
/**********/

function distributeAssignment() {
  const button = document.querySelector("#assignment-distribution button");
  button.disabled = true;
  const req = buildReq({}, "post");
  fetch(model.urls.distributeAssignment, req)
    .then(resp => resp.json())
    .then(function(assignment) {
      model.assignment = {
        hash: assignment.hash,
        distributionDate: assignment.distribution_date
          ? new Date(assignment.distribution_date)
          : null,
      };
      distributedView();
      initStudentProgress(model.urls.getAssignmentStudentProgress);
    })
    .catch(function(err) {
      console.log(err);
      button.disabled = null;
    });
}

function onQuestionListModified() {
  const btn = document.querySelector("#question-list-save");
  btn.disabled = false;
}

function saveQuestionList() {
  const questions = Array.from(
    document.querySelectorAll("#question-list .draggable"),
  ).map(x => x.getAttribute("data-draggable-name"));

  const data = { name: "question_list", value: questions };

  const req = buildReq(data, "post");
  fetch(model.urls.groupAssignmentUpdate, req)
    .then(function() {
      const btn = document.querySelector("#question-list-save");
      btn.disabled = true;
    })
    .catch(function(err) {
      console.log(err);
    });
}

function sendAssignmentEmail(event) {
  const icon = event.currentTarget;
  const email = icon.parentNode.parentNode
    .querySelector(".student-list--email")
    .getAttribute("data-email");
  const data = { email: email };
  const req = buildReq(data, "post");
  fetch(model.urls.sendStudentAssignment, req)
    .then(function(resp) {
      if (resp.ok) {
        icon.style.color = "#00cc66";
        setTimeout(function() {
          icon.style["transition-duration"] = "3s";
        }, 300);
        setTimeout(function() {
          icon.style.color = "#a9a9a9";
          icon.style["transition-duration"] = "none";
        }, 700);
      } else {
        icon.style.color = "#b30000";
        setTimeout(function() {
          icon.style["transition-duration"] = "3s";
        }, 300);
        setTimeout(function() {
          icon.style.color = "#a9a9a9";
          icon.style["transition-duration"] = "none";
        }, 700);
      }
    })
    .catch(function(err) {
      console.log(err);
    });
}

/********/
/* view */
/********/

function view() {
  distributedView();
}

function distributedView() {
  const span = document.querySelector("#assignment-distribution");
  clear(span);
  if (model.assignment.distributionDate) {
    span.textContent = model.translations.distributed;
    const datetimeSpan = document.createElement("span");
    datetimeSpan.classList.add("mdc-list-item__secondary-text");
    datetimeSpan.textContent = formatDatetime(
      model.assignment.distributionDate,
    );
    span.append(datetimeSpan);
  } else {
    const button = document.createElement("button");
    button.classList.add("mdc-button", "mdc-button--raised");
    button.textContent = model.translations.distribute;
    span.append(button);
    const warning = document.createElement("span");
    warning.classList.add("assignment-distribution__warning");
    warning.textContent = model.translations.distributionWarning;
    span.append(warning);
  }
}

/*************/
/* listeners */
/*************/

function initListeners() {
  addQuestionListDragListeners();
  addSendAssignmentEmailListeners();
  addDistributeListener();
  addEditBtnsListeners();
}

function addDistributeListener() {
  if (!model.assignment.distributionDate) {
    document
      .querySelector("#assignment-distribution button")
      .addEventListener("click", distributeAssignment);
  }
}

function addQuestionListDragListeners() {
  Array.from(document.querySelectorAll(".draggable")).map(x =>
    x.addEventListener("dragenter", () => onQuestionListModified()),
  );
  document
    .querySelector("#question-list-save")
    .addEventListener("click", saveQuestionList);
}

function addSendAssignmentEmailListeners() {
  Array.from(document.querySelectorAll(".email-btn")).map(x =>
    x.addEventListener("click", event => sendAssignmentEmail(event)),
  );
}

function addEditBtnsListeners() {
  [...document.getElementsByClassName("edit-btn")].forEach(btn => {
    btn.addEventListener("click", event => {
      editField(event, "datetime", "mdc-list-item__secondary-text");
    });
  });
}

/********/
/* init */
/********/

export function initAssignment(data) {
  initModel(data);
  view();
  initListeners();
  if (model.assignment.distributionDate) {
    initStudentProgress(model.urls.getAssignmentStudentProgress);
  }
}
