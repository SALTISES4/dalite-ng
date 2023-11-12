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

const toggleAll = document.getElementById("btn-toggle-all");
if (toggleAll) {
  toggleAll.addEventListener("click", (e) => toggleButtonAll(e));
}
