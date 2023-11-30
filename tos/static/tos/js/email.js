// @ts-nocheck
const switches = document.querySelectorAll("md-switch:not(#notification-all)");
if (switches) {
  switches.forEach((s) => s.addEventListener("change", toggleAll));
}
const acceptAll = document.getElementById("notification-all");
if (acceptAll) {
  acceptAll.addEventListener("change", (e) => toggleOthers(e));
}

function toggleOthers(event) {
  console.info("Updating OTHER toggles", event.currentTarget.selected);
  if (event.currentTarget.selected) {
    switches.forEach((s) => (s.selected = true));
  } else {
    switches.forEach((s) => (s.selected = false));
  }
}

function toggleAll() {
  console.info("Updating ALL toggle");
  if (Array.from(switches).every((s) => s.selected == true)) {
    acceptAll.selected = true;
  } else {
    acceptAll.selected = false;
  }
}
