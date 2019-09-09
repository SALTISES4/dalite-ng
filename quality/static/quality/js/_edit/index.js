import { buildReq } from "../../../../../peerinst/static/peerinst/js/ajax.js";
import { clear } from "../../../../../peerinst/static/peerinst/js/utils.js";

/*********/
/* model */
/*********/

let model;

function initModel(data) {
  model = {
    quality: {
      pk: data.quality.pk,
      qualityType: data.quality.quality_type,
    },
    next: data.next,
    available: data.available.map(c => ({
      name: c.name,
      fullName: c.full_name,
      description: c.description,
    })),
    criterions: data.criterions,
    urls: {
      addCriterion: data.urls.add_criterion,
      updateCriterion: data.urls.update_criterion,
      removeCriterion: data.urls.remove_criterion,
    },
  };
}

/**********/
/* update */
/**********/

function updateCriterionOption(event, option, criterion) {
  const type = option.getAttribute("data-type");
  const name = option.getAttribute("name");
  let value;

  if (type === "CommaSepField" || type === "ManyToManyField") {
    option.querySelector(".comma-sep-input--input").setCustomValidity("");
    if (event.key === "Enter" || event.key === "," || event.key === " ") {
      if (value === " " || value === ",") {
        value = "";
      }
      value = option.querySelector(".comma-sep-input--input").value;
      if (!value) {
        event.preventDefault();
        return;
      }
      if (criterion[name].allowed) {
        if (!criterion[name].allowed.includes(value)) {
          toggleCriterionOptionError(
            option.querySelector(".comma-sep-input--input"),
            `${value} isn't an accepted language. Options are ${criterion[
              name
            ].allowed
              .slice(0, criterion[name].allowed.length - 1)
              .join(", ")} and ${
              criterion[name].allowed[criterion[name].allowed.length - 1]
            }.`,
          );
          option.querySelector(".comma-sep-input--input").value = "";
          event.preventDefault();
          return;
        }
      }
    } else if (event.key === "Backspace") {
      value = option.querySelector(".comma-sep-input--input").value;
      if (value) {
        return;
      }
    } else {
      return;
    }
  } else if (
    type === "PositiveIntegerField" ||
    type === "ProbabilityField" ||
    type === "FloatField" ||
    type === "IntegerField"
  ) {
    option.setCustomValidity("");
    value = option.value;
    if (value === "") {
      if (event.inputType === "insertText" && event.data === "-") {
        value = 0;
        option.value = 0;
      } else {
        return;
      }
    }
    if (type === "ProbabilityField") {
      if (value < 0) {
        value = 0;
        option.value = value;
      } else if (value > 1) {
        value = parseFloat("0." + value);
        option.value = value;
      } else if (value.toString().length > 4) {
        option.value = model.criterions.filter(
          c => c.name === criterion.name,
        )[0][name].value;
        return;
      } else if (
        model.criterions.filter(c => c.name === criterion.name)[0][name]
          .value == value
      ) {
        if (value === "00") {
          option.value = "0";
        }
        return;
      }
    }
  } else if (type === "BooleanField") {
    option.setCustomValidity("");
    value = option.value === "false";
  } else {
    option.setCustomValidity("");
    value = option.value;
  }

  const data = {
    quality: model.quality.pk,
    criterion: criterion.name,
    field: name,
    value: value,
  };

  const req = buildReq(data, "post");
  fetch(model.urls.updateCriterion, req)
    .then(resp => (resp.ok ? resp.json() : resp.text()))
    .then(data => {
      if (typeof data === "string") {
        toggleCriterionOptionError(err);
      } else {
        model.criterions = model.criterions.map(c =>
          c.name === data.name ? data : c,
        );
        if (name === "weight") {
          criterionOptionView(type, data.weight, criterion, option);
        } else {
          criterionOptionView(type, data[name].value, criterion, option);
        }
      }
    })
    .catch(err => console.log(err));
}

function addCriterion(criterion) {
  const data = {
    quality: model.quality.pk,
    criterion: criterion.name,
  };

  const req = buildReq(data, "post");
  fetch(model.urls.addCriterion, req)
    .then(resp => resp.json())
    .then(json => {
      model.criterions.push(json);
      criterionsView();
      newCriterionsView();
      toggleShowAddCriterion();
    })
    .catch(err => console.log(err));
}

function removeCriterion(criterion) {
  const data = {
    quality: model.quality.pk,
    criterion: criterion.name,
  };
  const req = buildReq(data, "post");
  fetch(model.urls.removeCriterion, req)
    .then(resp => {
      if (resp.ok) {
        model.criterions = model.criterions.filter(
          c => c.name != criterion.name,
        );
        criterionsView();
        newCriterionsView();
      }
    })
    .catch(err => console.log(err));
}

/********/
/* view */
/********/

function view() {
  returnLinkView();
  criterionsView();
  newCriterionsView();
}

function returnLinkView() {
  const link = document.querySelector("#back-link");
  if (model.next) {
    link.href = model.next;
    if (model.quality.qualityType === "teacher") {
      link.textContent = "Back to account";
    } else {
      link.textContent = `Back to ${model.quality.qualityType}`;
    }
  } else {
    link.parentNode.removeChild(link);
  }
}

function criterionsView() {
  const div = document.querySelector("#criterions");
  clear(div);
  model.criterions.forEach(criterion => {
    div.appendChild(criterionView(criterion));
  });
}

function criterionView(criterion) {
  const div = document.createElement("div");
  div.classList.add("criterion");
  div.classList.add("criterion__showing");
  div.name = criterion.name;

  const name = document.createElement("div");
  name.classList.add("criterion--name");
  name.textContent = criterion.full_name;
  name.title = criterion.description;
  name.addEventListener("click", () => toggleCriterionOptions(div));
  div.appendChild(name);

  const remove = document.createElement("button");
  remove.classList.add("criterion--remove");
  remove.addEventListener("click", event => {
    removeCriterion(criterion);
    event.stopPropagation();
  });
  name.appendChild(remove);
  const icon = document.createElement("i");
  icon.classList.add("material-icons");
  icon.textContent = "close";
  remove.appendChild(icon);

  const options = document.createElement("div");
  options.classList.add("criterion--options");
  div.appendChild(options);

  const binaryThreshold =
    criterion.versions[criterion.version - 1].binary_threshold;

  // const versionLabel = document.createElement("label");
  // versionLabel.textContent = "Version:";
  // const version = document.createElement("select");
  // const versions = [document.createElement("option")];
  // versions[0].value = 0;
  // versions[0].textContent = "0 (latest)";
  // versions.forEach(v => {
  // version.appendChild(v);
  // });
  // options.appendChild(versionLabel);
  // options.appendChild(version);
  //
  const weightLabel = document.createElement("label");
  weightLabel.textContent = "Weight:";
  const weight = criterionOptionView(
    "PositiveIntegerField",
    criterion.weight,
    criterion,
  );
  weight.name = "weight";
  options.appendChild(weightLabel);
  options.appendChild(weight);

  const otherOptions = Object.keys(criterion).filter(
    o =>
      ![
        "description",
        "full_name",
        "is_beta",
        "name",
        "version",
        "versions",
        "weight",
      ].includes(o),
  );
  otherOptions.forEach(o => {
    if (!binaryThreshold || o !== "threshold") {
      const option = criterion[o];
      const label = document.createElement("label");
      label.textContent = `${option.full_name}:`;
      label.title = option.description;
      const input = criterionOptionView(
        option.type,
        option.value,
        criterion,
        null,
      );
      input.setAttribute("name", option.name);
      options.appendChild(label);
      options.appendChild(input);
    }
  });

  return div;
}

function criterionOptionView(type, value, criterion, input = null) {
  const focus = !!input;
  if (type === "PositiveIntegerField") {
    if (!input) {
      input = document.createElement("input");
      input.setAttribute("data-type", type);
      input.type = "number";
      input.min = 0;
      input.addEventListener("input", event =>
        updateCriterionOption(event, input, criterion),
      );
    }
    input.value = value;
    return input;
  } else if (type === "ProbabilityField") {
    if (!input) {
      input = document.createElement("input");
      input.setAttribute("data-type", type);
      input.type = "number";
      input.min = 0;
      input.max = 1;
      input.step = 0.01;
      input.addEventListener("input", event =>
        updateCriterionOption(event, input, criterion),
      );
      if (focus) {
        input.focus();
      }
    }
    input.value = value;
    return input;
  } else if (type === "CommaSepField" || type === "ManyToManyField") {
    if (!input) {
      input = document.createElement("div");
      input.setAttribute("data-type", type);
      input.classList.add("comma-sep-input");
      input.type = "comma-sep";
    }
    clear(input);
    value.forEach(word => {
      const span = document.createElement("span");
      span.classList.add("comma-sep-input--word");
      span.textContent = word;
      input.appendChild(span);
    });
    const input_ = document.createElement("input");
    input_.classList.add("comma-sep-input--input");
    input_.type = "text";
    input_.addEventListener("keydown", event =>
      updateCriterionOption(event, input, criterion),
    );
    input.appendChild(input_);
    if (focus) {
      input_.focus();
    }
    return input;
  } else if (type === "BooleanField") {
    if (!input) {
      input = document.createElement("div");
      input.setAttribute("data-type", type);
      input.classList.add("boolean-input");
      clear(input);
      const input_ = document.createElement("input");
      input_.classList.add("boolean-input--input");
      input_.type = "checkbox";
      input_.addEventListener("click", event =>
        updateCriterionOption(event, input, criterion),
      );
      input.appendChild(input_);
      const background = document.createElement("span");
      background.classList.add("boolean-input--background");
      input.appendChild(background);
      const mark = document.createElement("span");
      mark.classList.add("boolean-input--mark");
      input.appendChild(mark);
      if (focus) {
        input_.focus();
      }
    }
    input.value = value;
    return input;
  }
}

function toggleCriterionOptions(criterion) {
  if (criterion.classList.contains("criterion__showing")) {
    criterion.classList.remove("criterion__showing");
  } else {
    criterion.classList.add("criterion__showing");
  }
}

function toggleCriterionOptionError(option, msg) {
  option.setCustomValidity(msg);
}

function newCriterionsView() {
  const button = document.querySelector(".add-criterion button");
  const available = model.available.filter(
    c => !model.criterions.map(cc => cc.name).includes(c.name),
  );
  if (available.length) {
    const ul = document.querySelector(".available-criterions ul");
    clear(ul);
    available.forEach(criterion => {
      ul.appendChild(newCriterionView(criterion));
    });
    button.disabled = false;
    button.title = "Add a new criterion";
  } else {
    button.disabled = true;
    button.title = "There are no new criterions to add";
  }
}

function newCriterionView(criterion) {
  const li = document.createElement("li");
  li.title = criterion.description;
  li.textContent = criterion.fullName;
  li.addEventListener("click", () => addCriterion(criterion));
  return li;
}

function toggleShowAddCriterion() {
  const div = document.querySelector(".add-criterion");
  if (div.classList.contains("add-criterion__showing")) {
    div.classList.remove("add-criterion__showing");
  } else {
    if (model.available.length) {
      div.classList.add("add-criterion__showing");
    }
  }
}

/*************/
/* listeners */
/*************/

function initEventListeners() {
  initAddCriterionListeners();
}

function initAddCriterionListeners() {
  document
    .querySelector(".add-criterion button")
    .addEventListener("click", toggleShowAddCriterion);
}

/********/
/* init */
/********/

export function init(data) {
  initModel(data);
  view();
  initEventListeners();
}
