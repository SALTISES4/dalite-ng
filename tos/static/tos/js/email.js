"use strict";

function toggleButton(event) {
  const container = event.currentTarget;
  if (!container.classList.contains("btn-toggle--disabled")) {
    const buttons = container.getElementsByTagName("div");
    const checkbox = container.getElementsByTagName("input")[0];
    if (checkbox.checked) {
      checkbox.checked = false;
      buttons[0].classList.remove("btn-toggle--selected");
      buttons[1].classList.add("btn-toggle--selected");
    } else {
      checkbox.checked = true;
      buttons[0].classList.add("btn-toggle--selected");
      buttons[1].classList.remove("btn-toggle--selected");
    }
  }
}

function toggleButtonAll(event) {
  const container = event.currentTarget;
  const checkbox = container.getElementsByTagName("input")[0];
  if (checkbox.checked) {
    const toggleButtons = document.getElementsByClassName("btn-toggle");
    for (let i = 0; i < toggleButtons.length; i++) {
      toggleButtons[i].classList.remove("btn-toggle--disabled");
    }
  } else {
    const toggleButtons = document.getElementsByClassName("btn-toggle");
    for (let i = 0; i < toggleButtons.length; i++) {
      if (toggleButtons[i] != container) {
        toggleButtons[i].classList.add("btn-toggle--disabled");
      }
    }
  }
}

Array.from(document.getElementsByClassName("btn-toggle")).map(x =>
  x.addEventListener("click", e => toggleButton(e)),
);

const toggleAll = document.getElementById("btn-toggle-all");
if (toggleAll) {
  toggleAll.addEventListener("click", e => toggleButtonAll(e));
}
