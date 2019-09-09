"use strict";

export function getCsrfToken() {
  return document
    .getElementsByName("csrfmiddlewaretoken")[0]
    .getAttribute("value");
}

export function buildReq(data, method) {
  if (method.toLowerCase() === "get") {
    return {
      method: method.toUpperCase(),
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
    };
  } else if (method.toLowerCase() === "post") {
    const body = data ? JSON.stringify(data) : "";
    return {
      method: method.toUpperCase(),
      body: body,
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
    };
  } else {
    throw Error(`Method ${method} not implemented yet.`);
  }
}

export function updateAssignmentQuestionList(
  url,
  questionId,
  assignmentIdentifier,
) {
  const token = getCsrfToken();
  const data = {
    question_id: questionId,
    assignment_identifier: assignmentIdentifier,
  };
  const req = {
    method: "POST",
    body: JSON.stringify(data),
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": token,
    },
  };
  fetch(url, req)
    .then(function(resp) {
      if (!resp.ok) {
        console.log(resp);
      } else {
        // Manipulate DOM
        const list = document.getElementById("question-list");
        const card = document.getElementById(questionId);
        if ($.contains(list, card)) {
          $("#" + questionId).remove();
        } else {
          $("#" + questionId)
            .find($(".update-questions-btn"))
            .html("delete");
          const q = $("#" + questionId).detach();
          q.appendTo($("#question-list"));
          $("#empty-assignment-list").remove();
          $(".search-set").each(function() {
            $(this) // eslint-disable-line no-invalid-this
              .find(".filter-count")
              .empty()
              .append($(this).find(".mdc-card:visible").length); // eslint-disable-line no-invalid-this,max-len
          });
          $(".search-set").each(function() {
            $(this) // eslint-disable-line no-invalid-this
              .find(".filter-count-total")
              .empty()
              .append($(this).find(".mdc-card").length); // eslint-disable-line no-invalid-this,max-len
          });
        }
      }
    })
    .catch(function(err) {
      console.log(err);
    });
}
