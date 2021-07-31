import flatpickr from "flatpickr";
import { MDCSnackbar } from "@material/snackbar";

export function getSnack() {
  const snackbar = new MDCSnackbar(document.querySelector(".mdc-snackbar"));
  return snackbar;
}

function editField(event, type, className) {
  const iconContainer = event.currentTarget.parentNode.parentNode;
  const container = event.currentTarget.parentNode.previousElementSibling;
  const field =
    event.currentTarget.parentNode.previousElementSibling.firstElementChild;

  let newField;

  if (type == "text") {
    newField = editTextField(field);
  } else if (type == "textList") {
    newField = editTextListField(field);
  } else if (type == "datetime") {
    newField = editDateTimeField(field);
  } else {
    console.log(
      `The \`editField\` function isn 't implemented for type ${type}.`,
    );
    return;
  }

  container.replaceChild(newField, field);

  const iconsDiv = event.currentTarget.parentNode;
  let newIconsDiv = iconsDiv.cloneNode(false);

  newIconsDiv = toggleIcons(newIconsDiv, type, false, className);

  iconContainer.replaceChild(newIconsDiv, iconsDiv);
}

function saveField(event, type, save, className) {
  const iconContainer = event.currentTarget.parentNode.parentNode;
  const container = event.currentTarget.parentNode.previousElementSibling;
  const field =
    event.currentTarget.parentNode.previousElementSibling.firstElementChild;
  const url =
    container.parentNode.parentNode.parentNode.getAttribute("data-update-url");
  if (type == "text") {
    saveTextField(field, save, className, url).then(function (newField) {
      container.replaceChild(newField, field);
    });
  } else if (type == "textList") {
    saveTextListField(field, save, className, url).then(function (newField) {
      container.replaceChild(newField, field);
    });
  } else if (type == "datetime") {
    saveDateTimeField(field, save, className, url).then(function (newField) {
      container.replaceChild(newField, field);
    });
  } else {
    console.log(
      `The \`saveField\` function isn't implemented for type ${type}.`,
    );
    return;
  }

  const iconsDiv = event.currentTarget.parentNode;
  let newIconsDiv = iconsDiv.cloneNode(false);

  newIconsDiv = toggleIcons(newIconsDiv, type, true, className);

  iconContainer.replaceChild(newIconsDiv, iconsDiv);
}

function editTextField(field) {
  const newField = document.createElement("div");
  const name = field.getAttribute("name");
  newField.setAttribute("name", name);
  const input = document.createElement("input");
  input.type = "text";
  input.value = field.textContent.trim();
  input.setAttribute("data-old-content", field.textContent);
  newField.append(input);
  return newField;
}

function editTextListField(field) {
  const newField = document.createElement("div");
  const name = field.getAttribute("name");
  newField.setAttribute("name", name);
  const ul = field.querySelector("ul").cloneNode(true);
  const li_ = document.createElement("li");
  const input = document.createElement("input");
  input.type = "text";
  input.value = "";
  input.setAttribute("data-old-content", "");
  li_.append(input);
  ul.append(li_);

  newField.append(ul);
  return newField;
}

function editDateTimeField(field) {
  const newField = document.createElement("div");
  const name = field.getAttribute("name");
  newField.setAttribute("name", name);
  const input = document.createElement("input");
  input.type = "text";
  input.setAttribute("data-old-content", field.textContent);
  newField.append(input);
  const datetime = field.textContent
    .match(/(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})/)
    .slice(1)
    .map((x) => parseInt(x));
  datetime[1] -= 1;
  flatpickr(input, {
    enableTime: true,
    defaultDate: new Date(...datetime),
    dateFormat: "Z",
    altInput: true,
    altFormat: "Y-m-d H:i",
    minDate: "today",
  });
  return newField;
}

function toggleIcons(newIconsDiv, type, toEdit, className) {
  if (toEdit) {
    const editIcon = document.createElement("i");
    editIcon.classList.add(
      "material-icons",
      "md-24",
      "mdc-ripple-surface",
      "icon-list",
    );
    if ((type == "text") | (type == "datetime")) {
      editIcon.textContent = "edit";
      editIcon.title = "Edit";
    } else {
      editIcon.textContent = "add";
      editIcon.title = "Add";
    }
    editIcon.addEventListener("click", function (e) {
      editField(e, type, className);
    });
    newIconsDiv.append(editIcon);
  } else {
    const saveIcon = document.createElement("i");
    saveIcon.classList.add(
      "material-icons",
      "md-24",
      "mdc-ripple-surface",
      "icon-list",
    );
    saveIcon.textContent = "check";
    saveIcon.title = "Save";
    saveIcon.addEventListener("click", function (e) {
      saveField(e, type, true, className);
    });
    const cancelIcon = document.createElement("i");
    cancelIcon.classList.add(
      "material-icons",
      "md-24",
      "mdc-ripple-surface",
      "icon-list",
    );
    cancelIcon.textContent = "close";
    cancelIcon.title = "Cancel";
    cancelIcon.addEventListener("click", function (e) {
      saveField(e, type, false, className);
    });
    newIconsDiv.append(saveIcon);
    newIconsDiv.append(cancelIcon);
  }

  return newIconsDiv;
}

async function saveTextField(field, save, className, url) {
  const newField = document.createElement("span");
  const name = field.getAttribute("name");
  newField.setAttribute("name", name);
  newField.setAttribute("class", className);
  if (save) {
    const newValue = field.firstChild.value;
    const err = await updateDetails(name, newValue, url);
    if (err) {
      newField.textContent = field.firstChild.getAttribute("data-old-content");
    } else {
      newField.textContent = newValue;
    }
  } else {
    newField.textContent = field.firstChild.getAttribute("data-old-content");
  }
  return newField;
}

async function saveTextListField(field, save, className, url) {
  const newField = document.createElement("span");
  const name = field.getAttribute("name");
  newField.setAttribute("name", name);
  const ul = field.firstChild.cloneNode(true);
  const li = field.firstChild.lastChild;
  ul.removeChild(ul.lastChild);
  if (save) {
    const newValue = li.firstChild.value;
    const err = await updateDetails(name, newValue, url);
    if (!err) {
      const li_ = document.createElement("li");
      li_.textContent = newValue;
      li_.setAttribute("class", className);
      ul.append(li_);
    }
  }
  newField.append(ul);
  return newField;
}

async function saveDateTimeField(field, save, className, url) {
  const newField = document.createElement("span");
  const name = field.getAttribute("name");
  newField.setAttribute("name", name);
  newField.setAttribute("class", className);
  if (save) {
    const sentValue = field.firstChild.value;
    const newValue = flatpickr.formatDate(new Date(sentValue), "Y-m-d H:i");
    const err = await updateDetails(name, sentValue, url);
    if (err) {
      newField.textContent = field.firstChild.getAttribute("data-old-content");
    } else {
      newField.textContent = newValue;
    }
  } else {
    newField.textContent = field.firstChild.getAttribute("data-old-content");
  }
  return newField;
}

async function updateDetails(name, value, url) {
  const data = { name, value };
  const token = document.getElementsByName("csrfmiddlewaretoken")[0].value;
  const req = {
    method: "POST",
    body: JSON.stringify(data),
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": token,
    },
  };

  const resp = await fetch(url, req);
  const err = await resp.text();

  return err;
}

export { editField, saveField };
