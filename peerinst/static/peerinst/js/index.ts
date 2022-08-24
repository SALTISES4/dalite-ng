/* eslint-disable camelcase */
declare let bundle: any; // bundle will be available globally at runtime

// MDC
import autoInit from "@material/auto-init/index";
import * as checkbox from "@material/checkbox/index";
import * as chips from "@material/chips/index";
import * as dialog from "@material/dialog/index";
import * as drawer from "@material/drawer/index";
import * as helperText from "@material/textfield/helper-text/index";
import * as iconToggle from "@material/icon-toggle/index";
import * as radio from "@material/radio/index";
import * as ripple from "@material/ripple/index";
import * as selectbox from "@material/select/index";
import * as textField from "@material/textfield/index";
import * as toolbar from "@material/toolbar/index";
import * as snackbar from "@material/snackbar/index";

autoInit.register("MDCCheckbox", checkbox.MDCCheckbox);
autoInit.register("MDCChip", chips.MDCChip);
autoInit.register("MDCChipSet", chips.MDCChipSet);
autoInit.register("MDCDialog", dialog.MDCDialog);
autoInit.register("MDCDrawer", drawer.MDCTemporaryDrawer);
autoInit.register("MDCIconToggle", iconToggle.MDCIconToggle);
autoInit.register("MDCRadio", radio.MDCRadio);
autoInit.register("MDCRipple", ripple.MDCRipple);
autoInit.register("MDCSelect", selectbox.MDCSelect);
autoInit.register("MDCTextField", textField.MDCTextField);
autoInit.register("MDCTextFieldHelperText", helperText.MDCTextFieldHelperText);
autoInit.register("MDCToolbar", toolbar.MDCToolbar);
autoInit.register("MDCSnackbar", snackbar.MDCSnackbar);

export {
  autoInit,
  checkbox,
  chips,
  dialog,
  drawer,
  iconToggle,
  radio,
  ripple,
  selectbox,
  textField,
  toolbar,
  snackbar,
};

// D3
import * as d3 from "d3";

export {
  active,
  area,
  axisBottom,
  axisLeft,
  curveNatural,
  format,
  interrupt,
  line,
  now,
  path,
  range,
  rgb,
  scaleBand,
  scaleLinear,
  scaleOrdinal,
  select,
  selectAll,
  transition,
} from "d3";

// Custom functions (works with custom_elements.scss)
import { addEventListeners } from "./custom_elements.js";

addEventListeners();

// Ajax
/** Define csrf safe HTTP methods
 *   https://docs.djangoproject.com/en/1.8/ref/csrf/
 * @function
 * @param {String} method
 * @return {Boolean}
 */
export function csrfSafeMethod(method) {
  // these HTTP methods do not require CSRF protection
  return /^(GET|HEAD|OPTIONS|TRACE)$/.test(method);
}

// Get csrf token
export { getCsrfToken } from "./ajax.js";

/** Replace element with text input form using Ajax
 * @function
 * @param {String} idToBind
 * @param {String} formToReplace
 * @param {String} createUrl
 * @param {String} formUrl
 * @param {Function} init
 * @param {String} searchUrl
 * @param {Function} completionHook
 */
export function bindAjaxTextInputForm(
  idToBind,
  formToReplace,
  createUrl,
  formUrl,
  init,
  searchUrl,
  completionHook,
) {
  const d = document.getElementById(idToBind);
  if (d) {
    d.onclick = function () {
      /** The callback
       * @function
       * @this Callback
       */
      function callback() {
        bundle.autoInit();
        const input = this.querySelector(".mdc-text-field__input");
        input.focus();
        init(
          idToBind,
          formToReplace,
          createUrl,
          formUrl,
          init,
          searchUrl,
          completionHook,
        );
      }
      $(`#${formToReplace}`).load(createUrl, callback);
    };
  }
}

/** Callback for category creation
 * @function
 * @param {String} idToBind
 * @param {String} formToReplace
 * @param {String} createUrl
 * @param {String} formUrl
 * @param {Function} init
 * @param {String} searchUrl
 * @param {Function} completionHook
 */
export function categoryForm(
  idToBind,
  formToReplace,
  createUrl,
  formUrl,
  init,
  searchUrl,
  completionHook,
) {
  // Define ENTER key
  const form = $("#category_form").find("#id_title");
  if (form.length) {
    $(form).on("keypress", function (event) {
      if (event.which == 13) {
        $("#submit_category_form").trigger("click");
      }
    });
  }

  // Handle clear
  $("#clear_category_form").on("click", function () {
    $("#category_form").load(formUrl, function () {
      bundle.bindAjaxTextInputForm(
        idToBind,
        formToReplace,
        createUrl,
        formUrl,
        init,
        searchUrl,
        completionHook,
      );
      if (completionHook) {
        completionHook();
      }
      bundle.bindCategoryAutofill(searchUrl);
      bundle.autoInit();
    });
  });

  // Setup ajax call and attach a submit handler to the form
  $.ajaxSetup({
    beforeSend(xhr, settings) {
      if (!bundle.csrfSafeMethod(settings.type) && !this.crossDomain) {
        xhr.setRequestHeader("X-CSRFToken", bundle.getCsrfToken());
      }
    },
  });

  $("#submit_category_form").on("click", function () {
    const title = $("#category_form").find("input[name='title']").val();

    // Send the data using post
    const posting = $.post(createUrl, { title });

    // Put the results in a div
    posting.done(function (data, status) {
      $("#category_form").empty().text(data);

      const formType = $("#create_new_category");
      if (formType.length) {
        categoryForm(
          idToBind,
          formToReplace,
          createUrl,
          formUrl,
          init,
          searchUrl,
          completionHook,
        );
        bundle.autoInit();
        $("#category_form").find("input[name='title']")[0].trigger("focus");
      } else {
        bundle.bindAjaxTextInputForm(
          idToBind,
          formToReplace,
          createUrl,
          formUrl,
          init,
          searchUrl,
          completionHook,
        );
        bundle.bindCategoryAutofill(searchUrl);
        bundle.autoInit();
        $("#autofill_categories")
          .val(title)
          .trigger("focus")
          .autocomplete("search");
        if (completionHook) {
          completionHook();
        }
      }
    });
  });
}

/** Callback for category autofill
 * @function
 * @param {String} source
 */
export function bindCategoryAutofill(source) {
  function updateSelect(el, formId) {
    el.remove();
    $(formId)
      .find(`[value=${$(el).attr("v")}]`)
      .remove();
  }

  // Generators for autocomplete
  const response = function (searchClass, spinnerId) {
    return function (event, ui) {
      // NB: Pass by reference.  ui can be modified, but not recreated.
      const currentList = $.map($(searchClass), function (obj, i) {
        return $(obj).attr("d");
      });

      const tmp = ui.content.filter(function (el) {
        return !currentList.includes(el.label);
      });

      let l = ui.content.length;
      while (l > 0) {
        ui.content.pop();
        l = ui.content.length;
      }

      for (let i = 0; i < tmp.length; i++) {
        ui.content.push(tmp[i]);
      }

      if (ui.content.length == 0) {
        // Could add hint that there are no results
      }

      $(spinnerId).css("opacity", 0);
      return;
    };
  };

  const search = function (spinnerId) {
    return function (event, ui) {
      $(spinnerId).css("opacity", 1);
    };
  };

  const focus = function (event, ui) {
    event.preventDefault();
    $(this).val(ui.item.label); // eslint-disable-line no-invalid-this
  };

  const select = function (currentIds, className, formId) {
    return function (event, ui) {
      event.preventDefault();
      $(this).val(""); // eslint-disable-line no-invalid-this

      const newDiv = document.createElement("div");
      newDiv.setAttribute("d", ui.item.label);
      newDiv.setAttribute("v", ui.item.value);
      newDiv.setAttribute("tabindex", "0");
      newDiv.setAttribute("data-mdc-auto-init", "MDCChip");
      newDiv.classList.add("mdc-chip", "mdc-typography--caption", className);
      newDiv.addEventListener("click", function () {
        updateSelect(this, formId); // eslint-disable-line no-invalid-this
      });
      const text = document.createElement("div");
      text.classList.add("mdc-chip__text");
      text.textContent = ui.item.label;
      newDiv.appendChild(text);
      const icon = document.createElement("i");
      icon.classList.add(
        "material-icons",
        "mdc-chip__icon",
        "mdc-chip__icon--trailing",
      );
      icon.setAttribute("tabindex", "0");
      icon.setAttribute("role", "button");
      icon.textContent = "cancel";
      newDiv.appendChild(icon);
      document.getElementById(currentIds).appendChild(newDiv);

      $(formId).append(
        `<option selected='selected' value=${ui.item.value}>${ui.item.label}</option>`,
      );
    };
  };

  $("#autofill_categories").autocomplete({
    delay: 700,
    minLength: 3,
    classes: {
      "ui-autocomplete": "mdc-typography--body1",
    },
    source,
    response: response(".category", "#search_categories"),
    search: search("#search_categories"),
    focus,
    select: select("current_categories", "category", "#id_category"),
    autoFocus: true,
  });
}

export function bindUsernameAutofill(source) {
  function updateSelect(el, formId) {
    el.remove();
    $(formId)
      .find(`[value=${$(el).attr("v")}]`)
      .remove();
  }

  // Generators for autocomplete
  const response = function (searchClass, spinnerId) {
    return function (event, ui) {
      // NB: Pass by reference.  ui can be modified, but not recreated.
      const currentList = $.map($(searchClass), function (obj, i) {
        return $(obj).attr("d");
      });

      const tmp = ui.content.filter(function (el) {
        return !currentList.includes(el.label);
      });

      let l = ui.content.length;
      while (l > 0) {
        ui.content.pop();
        l = ui.content.length;
      }

      for (let i = 0; i < tmp.length; i++) {
        ui.content.push(tmp[i]);
      }

      if (ui.content.length == 0) {
        // Could add hint that there are no results
      }

      $(spinnerId).css("opacity", 0);
      return;
    };
  };

  const search = function (spinnerId) {
    return function (event, ui) {
      $(spinnerId).css("opacity", 1);
    };
  };

  const focus = function (event, ui) {
    event.preventDefault();
    $(this).val(ui.item.label); // eslint-disable-line no-invalid-this
  };

  const select = function (currentIds, className, formId) {
    return function (event, ui) {
      event.preventDefault();
      $(this).val(""); // eslint-disable-line no-invalid-this

      const newDiv = document.createElement("div");
      newDiv.setAttribute("d", ui.item.label);
      newDiv.setAttribute("v", ui.item.value);
      newDiv.setAttribute("tabindex", "0");
      newDiv.setAttribute("data-mdc-auto-init", "MDCChip");
      newDiv.classList.add("mdc-chip", "mdc-typography--caption", className);
      newDiv.addEventListener("click", function () {
        updateSelect(this, formId); // eslint-disable-line no-invalid-this
      });
      const text = document.createElement("div");
      text.classList.add("mdc-chip__text");
      text.textContent = ui.item.label;
      newDiv.appendChild(text);
      const icon = document.createElement("i");
      icon.classList.add(
        "material-icons",
        "mdc-chip__icon",
        "mdc-chip__icon--trailing",
      );
      icon.setAttribute("tabindex", "0");
      icon.setAttribute("role", "button");
      icon.textContent = "cancel";
      newDiv.appendChild(icon);
      document.getElementById(currentIds).appendChild(newDiv);

      $(formId).append(
        `<option selected='selected' value=${ui.item.value}>${ui.item.label}</option>`,
      );
    };
  };

  $("#autofill_usernames").autocomplete({
    delay: 700,
    minLength: 3,
    classes: {
      "ui-autocomplete": "mdc-typography--body1",
    },
    source,
    response: response(".username", "#search_usernames"),
    search: search("#search_usernames"),
    focus,
    select: select("current_usernames", "username", "#id_username"),
    autoFocus: true,
  });
}

export function bindSubjectAutofill(source) {
  function updateSelect(el, formId) {
    el.remove();
    $(formId)
      .find(`[value=${$(el).attr("v")}]`)
      .remove();
  }

  // Generators for autocomplete
  const response = function (searchClass, spinnerId) {
    return function (event, ui) {
      // NB: Pass by reference.  ui can be modified, but not recreated.
      const currentList = $.map($(searchClass), function (obj, i) {
        return $(obj).attr("d");
      });

      const tmp = ui.content.filter(function (el) {
        return !currentList.includes(el.label);
      });

      let l = ui.content.length;
      while (l > 0) {
        ui.content.pop();
        l = ui.content.length;
      }

      for (let i = 0; i < tmp.length; i++) {
        ui.content.push(tmp[i]);
      }

      if (ui.content.length == 0) {
        // Could add hint that there are no results
      }

      $(spinnerId).css("opacity", 0);
      return;
    };
  };

  const search = function (spinnerId) {
    return function (event, ui) {
      $(spinnerId).css("opacity", 1);
    };
  };

  const focus = function (event, ui) {
    event.preventDefault();
    $(this).val(ui.item.label); // eslint-disable-line no-invalid-this
  };

  const select = function (currentIds, className, formId) {
    return function (event, ui) {
      event.preventDefault();
      $(this).val(""); // eslint-disable-line no-invalid-this

      const newDiv = document.createElement("div");
      newDiv.setAttribute("d", ui.item.label);
      newDiv.setAttribute("v", ui.item.value);
      newDiv.setAttribute("tabindex", "0");
      newDiv.setAttribute("data-mdc-auto-init", "MDCChip");
      newDiv.classList.add("mdc-chip", "mdc-typography--caption", className);
      newDiv.addEventListener("click", function () {
        updateSelect(this, formId); // eslint-disable-line no-invalid-this
      });
      const text = document.createElement("div");
      text.classList.add("mdc-chip__text");
      text.textContent = ui.item.label;
      newDiv.appendChild(text);
      const icon = document.createElement("i");
      icon.classList.add(
        "material-icons",
        "mdc-chip__icon",
        "mdc-chip__icon--trailing",
      );
      icon.setAttribute("tabindex", "0");
      icon.setAttribute("role", "button");
      icon.textContent = "cancel";
      newDiv.appendChild(icon);
      document.getElementById(currentIds).appendChild(newDiv);

      $(formId).append(
        `<option selected='selected' value=${ui.item.value}>${ui.item.label}</option>`,
      );
    };
  };

  $("#autofill_subjects").autocomplete({
    delay: 700,
    minLength: 3,
    classes: {
      "ui-autocomplete": "mdc-typography--body1",
    },
    source,
    response: response(".subject", "#search_subjects"),
    search: search("#search_subjects"),
    focus,
    select: select("current_subjects", "subject", "#id_subject"),
    autoFocus: true,
  });
}

export function bindDisciplineAutofill(source) {
  function updateSelect(el, formId) {
    el.remove();
    $(formId)
      .find(`[value=${$(el).attr("v")}]`)
      .remove();
  }

  // Generators for autocomplete
  const response = function (searchClass, spinnerId) {
    return function (event, ui) {
      // NB: Pass by reference.  ui can be modified, but not recreated.
      const currentList = $.map($(searchClass), function (obj, i) {
        return $(obj).attr("d");
      });

      const tmp = ui.content.filter(function (el) {
        return !currentList.includes(el.label);
      });

      let l = ui.content.length;
      while (l > 0) {
        ui.content.pop();
        l = ui.content.length;
      }

      for (let i = 0; i < tmp.length; i++) {
        ui.content.push(tmp[i]);
      }

      if (ui.content.length == 0) {
        // Could add hint that there are no results
      }

      $(spinnerId).css("opacity", 0);
      return;
    };
  };

  const search = function (spinnerId) {
    return function (event, ui) {
      $(spinnerId).css("opacity", 1);
    };
  };

  const focus = function (event, ui) {
    event.preventDefault();
    $(this).val(ui.item.label); // eslint-disable-line no-invalid-this
  };

  const select = function (currentIds, className, formId) {
    return function (event, ui) {
      event.preventDefault();
      $(this).val(""); // eslint-disable-line no-invalid-this

      const newDiv = document.createElement("div");
      newDiv.setAttribute("d", ui.item.label);
      newDiv.setAttribute("v", ui.item.value);
      newDiv.setAttribute("tabindex", "0");
      newDiv.setAttribute("data-mdc-auto-init", "MDCChip");
      newDiv.classList.add("mdc-chip", "mdc-typography--caption", className);
      newDiv.addEventListener("click", function () {
        updateSelect(this, formId); // eslint-disable-line no-invalid-this
      });
      const text = document.createElement("div");
      text.classList.add("mdc-chip__text");
      text.textContent = ui.item.label;
      newDiv.appendChild(text);
      const icon = document.createElement("i");
      icon.classList.add(
        "material-icons",
        "mdc-chip__icon",
        "mdc-chip__icon--trailing",
      );
      icon.setAttribute("tabindex", "0");
      icon.setAttribute("role", "button");
      icon.textContent = "cancel";
      newDiv.appendChild(icon);
      document.getElementById(currentIds).appendChild(newDiv);

      $(formId).append(
        `<option selected='selected' value=${ui.item.value}>${ui.item.label}</option>`,
      );
    };
  };

  $("#autofill_disciplines").autocomplete({
    delay: 700,
    minLength: 3,
    classes: {
      "ui-autocomplete": "mdc-typography--body1",
    },
    source,
    response: response(".discipline", "#search_disciplines"),
    search: search("#search_disciplines"),
    focus,
    select: select("current_disciplines", "discipline", "#id_discipline"),
    autoFocus: true,
  });
}
// Create disciplines
/** Callback for discipline creation
 * @function
 * @param {String} idToBind
 * @param {String} formToReplace
 * @param {String} createUrl
 * @param {String} formUrl
 * @param {Function} init
 * @param {String} searchUrl
 * @param {Function} completionHook
 */
export function disciplineForm(
  idToBind,
  formToReplace,
  createUrl,
  formUrl,
  init,
  searchUrl,
  completionHook,
) {
  // Bind form submit to icon
  $("#submit_discipline_form").on("click", function () {
    $("#discipline_create_form").submit();
  });

  // Handle clear
  $("#clear_discipline_form").on("click", function () {
    $("#discipline_form").load(formUrl, function () {
      bundle.bindAjaxTextInputForm(
        idToBind,
        formToReplace,
        createUrl,
        formUrl,
        init,
        searchUrl,
        completionHook,
      );
      if (completionHook) {
        completionHook();
      }
    });
  });

  // Setup ajax call and attach a submit handler to the form
  $.ajaxSetup({
    beforeSend(xhr, settings) {
      if (!bundle.csrfSafeMethod(settings.type) && !this.crossDomain) {
        xhr.setRequestHeader("X-CSRFToken", bundle.getCsrfToken());
      }
    },
  });

  $("#submit_discipline_form").on("click", function () {
    const title = $("#discipline_form").find("input[name='title']").val();

    // Send the data using post
    const posting = $.post(createUrl, { title });

    // Put the results in a div
    posting.done(function (data, status) {
      $("#discipline_form").empty().text(data);

      const formType = $("#discipline_create_form");
      if (formType.length) {
        disciplineForm(
          idToBind,
          formToReplace,
          createUrl,
          formUrl,
          init,
          searchUrl,
          completionHook,
        );
        bundle.autoInit();
      } else {
        bundle.bindAjaxTextInputForm(
          idToBind,
          formToReplace,
          createUrl,
          formUrl,
          init,
          searchUrl,
          completionHook,
        );
        if (completionHook) {
          completionHook();
        }
      }
    });
  });
}

/** Mike Bostock's svg line wrap function
 *   https://bl.ocks.org/mbostock/7555321
 *   (only slightly modified)
 * @function
 * @param {String} text
 * @param {Int} width
 * @this Wrap
 */
export function wrap(text, width) {
  text.each(
    /* @this */ function () {
      const text = bundle.select(this);
      const words = text.text().split(/\s+/).reverse();
      let word;
      let line = [];
      let lineNumber = 0;
      const lineHeight = 16; // px
      const x = text.attr("x");
      const dx = text.attr("dx");
      const y = text.attr("y");
      const dy = parseFloat(text.attr("dy"));
      let tspan = text
        .text(null)
        .append("tspan")
        .attr("x", x)
        .attr("y", y)
        .attr("dx", dx)
        .attr("dy", `${dy}px`);
      while ((word = words.pop())) {
        line.push(word);
        tspan.text(line.join(" "));
        if (tspan.node().getComputedTextLength() > width) {
          line.pop();
          tspan.text(line.join(" "));
          line = [word];
          tspan = text
            .append("tspan")
            .attr("x", x)
            .attr("y", y)
            .attr("dx", dx)
            .attr("dy", `${++lineNumber * lineHeight + dy}px`)
            .text(word);
        }
      }
    },
  );
}

/** Underline h1 with svg
 *  @function
 */
function underlines() {
  // Decorate h1 headers
  const lines = d3.selectAll(".underline");
  lines.selectAll("g").remove();
  const w = document.querySelector("main").offsetWidth;

  const gradientX = lines
    .append("linearGradient")
    .attr("id", "underlineGradientX")
    .attr("x1", 0)
    .attr("x2", 1)
    .attr("y1", 0)
    .attr("y2", 0);

  gradientX.append("stop").attr("offset", "0%").attr("stop-color", "#54c0db");

  gradientX
    .append("stop")
    .attr("offset", "100%")
    .attr("stop-color", "#004266");

  const gradientY = lines
    .append("linearGradient")
    .attr("id", "underlineGradientY")
    .attr("x1", 0)
    .attr("x2", 0)
    .attr("y1", 0)
    .attr("y2", 1);

  gradientY.append("stop").attr("offset", "0%").attr("stop-color", "#004266");

  gradientY
    .append("stop")
    .attr("offset", "100%")
    .attr("stop-color", "#54c0db");

  const g = lines.append("g");
  g.append("rect")
    .attr("x", -10)
    .attr("y", 0)
    .attr("width", w + 10)
    .attr("height", 1)
    .attr("fill", "url(#underlineGradientX)");

  g.append("rect")
    .attr("x", w)
    .attr("y", 0)
    .attr("width", 1)
    .attr("height", 120)
    .attr("fill", "url(#underlineGradientY)");
}

/** Question difficulty
 *  @function
 *  @param {Object} matrix
 *  @param {string} id
 */
export function difficulty(matrix, id) {
  matrix = JSON.parse(matrix);
  const colour = {
    easy: "rgb(30, 142, 62)",
    hard: "rgb(237, 69, 40)",
    tricky: "rgb(237, 170, 30)",
    peer: "rgb(25, 118, 188)",
  };
  let max = -0;
  let label = "";
  Object.entries(matrix).map((entry) => {
    if (entry[1] > max) {
      max = entry[1];
      label = entry[0];
    }
  });

  const stats = document.getElementById(`stats-${id}`);
  if (max > 0) {
    const rating = document.getElementById(`rating-${id}`);
    rating.innerHTML =
      label.substring(0, 1).toUpperCase() + label.substring(1);
    stats.style.color = colour[label];
  } else {
    stats.style.display = "none";
  }
}

/** Question analytics
 *  @function
 *  @param {Object} matrix
 *  @param {Object} freq
 *  @param {string} id
 */
export function plot(matrix, freq, id) {
  if (!matrix["easy"]) {
    matrix["easy"] = 0;
  }
  if (!matrix["hard"]) {
    matrix["hard"] = 0;
  }
  if (!matrix["tricky"]) {
    matrix["tricky"] = 0;
  }
  if (!matrix["peer"]) {
    matrix["peer"] = 0;
  }
  const colour = {
    easy: "rgb(30, 142, 62)",
    hard: "rgb(237, 69, 40)",
    tricky: "rgb(237, 170, 30)",
    peer: "rgb(25, 118, 188)",
  };
  let max = -0;
  let label = "";
  Object.entries(matrix).map((entry) => {
    if (entry[1] > max) {
      max = entry[1];
      label = entry[0];
    }
  });
  if (max > 0) {
    const rating = document.getElementById(`rating-${id}`);
    if (rating) {
      rating.innerHTML =
        label.substring(0, 1).toUpperCase() + label.substring(1);
    }
    const stats = document.getElementById(`stats-${id}`);
    if (stats) {
      stats.style.color = colour[label];
    }
  }

  const matrixSvg = bundle.select(`#matrix-${id}`);
  matrixSvg.style("overflow", "visible");
  let size = +matrixSvg.attr("width");
  const g = matrixSvg.append("g");
  g.append("text")
    .attr("class", "legend")
    .attr("x", size / 2)
    .attr("y", -6)
    .style("font-size", "7pt")
    .attr("text-anchor", "middle")
    .style("opacity", 0)
    .text();

  const easy = g
    .append("rect")
    .attr("x", 0)
    .attr("y", 0)
    .attr("width", size / 2)
    .attr("height", size / 2)
    .attr("fill", colour["easy"])
    .style("opacity", 0.5 + 0.5 * matrix["easy"]);

  easy.on("mousemove", () => {
    g.select(".legend")
      .style("opacity", 1)
      .style("fill", colour["easy"])
      .text("Right > Right");
  });
  easy.on("mouseout", () => {
    g.select(".legend").transition().duration(100).style("opacity", 0);
  });

  g.append("text")
    .attr("x", size / 4)
    .attr("y", size / 4)
    .attr("dy", 4)
    .style("font-size", "8pt")
    .style("fill", "white")
    .style("text-anchor", "middle")
    .attr("pointer-events", "none")
    .text(`${parseInt(100 * matrix["easy"])}%`);

  const hard = g
    .append("rect")
    .attr("x", size / 2)
    .attr("y", size / 2)
    .attr("width", size / 2)
    .attr("height", size / 2)
    .attr("fill", colour["hard"])
    .style("opacity", 0.5 + 0.5 * matrix["hard"]);

  hard.on("mousemove", () => {
    g.select(".legend")
      .style("opacity", 1)
      .style("fill", colour["hard"])
      .text("Wrong > Wrong");
  });
  hard.on("mouseout", () => {
    g.select(".legend").transition().duration(100).style("opacity", 0);
  });

  g.append("text")
    .attr("x", (3 * size) / 4)
    .attr("y", (3 * size) / 4)
    .attr("dy", 4)
    .style("font-size", "8pt")
    .style("fill", "white")
    .style("text-anchor", "middle")
    .attr("pointer-events", "none")
    .text(`${parseInt(100 * matrix["hard"])}%`);

  const peer = g
    .append("rect")
    .attr("x", 0)
    .attr("y", size / 2)
    .attr("width", size / 2)
    .attr("height", size / 2)
    .attr("fill", colour["peer"])
    .style("opacity", 0.5 + 0.5 * matrix["peer"]);

  peer.on("mousemove", () => {
    g.select(".legend")
      .style("opacity", 1)
      .style("fill", colour["peer"])
      .text("Wrong > Right");
  });
  peer.on("mouseout", () => {
    g.select(".legend").transition().duration(100).style("opacity", 0);
  });

  g.append("text")
    .attr("x", size / 4)
    .attr("y", (3 * size) / 4)
    .attr("dy", 4)
    .style("font-size", "8pt")
    .style("fill", "white")
    .style("text-anchor", "middle")
    .attr("pointer-events", "none")
    .text(`${parseInt(100 * matrix["peer"])}%`);

  const tricky = g
    .append("rect")
    .attr("x", size / 2)
    .attr("y", 0)
    .attr("width", size / 2)
    .attr("height", size / 2)
    .attr("fill", colour["tricky"])
    .style("opacity", 0.5 + 0.5 * matrix["tricky"]);

  tricky.on("mousemove", () => {
    g.select(".legend")
      .style("opacity", 1)
      .style("fill", colour["tricky"])
      .text("Right > Wrong");
  });
  tricky.on("mouseout", () => {
    g.select(".legend").transition().duration(100).style("opacity", 0);
  });

  g.append("text")
    .attr("x", (3 * size) / 4)
    .attr("y", size / 4)
    .attr("dy", 4)
    .style("font-size", "8pt")
    .style("fill", "white")
    .style("text-anchor", "middle")
    .attr("pointer-events", "none")
    .text(`${parseInt(100 * matrix["tricky"])}%`);

  const firstFreqSvg = bundle.select(`#first-frequency-${id}`);
  const secondFreqSvg = bundle.select(`#second-frequency-${id}`);
  const margin = { left: 30, right: 30 };

  let sum = 0;
  for (const entry in freq["first_choice"]) {
    if ({}.hasOwnProperty.call(freq["first_choice"], entry)) {
      sum += freq["first_choice"][entry];
    }
  }
  for (const entry in freq["first_choice"]) {
    if ({}.hasOwnProperty.call(freq["first_choice"], entry)) {
      freq["first_choice"][entry] /= sum;
      freq["second_choice"][entry] /= sum;
    }
  }

  size = +secondFreqSvg.attr("width") - margin.left;

  const x = bundle.scaleLinear().domain([0, 1]).rangeRound([0, size]);
  const y = bundle
    .scaleBand()
    .domain(Object.keys(freq["first_choice"]).sort())
    .rangeRound([0, firstFreqSvg.attr("height")]);

  const gg = secondFreqSvg
    .append("g")
    .attr("transform", `translate(${margin.left},0)`);

  const ggg = firstFreqSvg.append("g");

  gg.append("g")
    .attr("class", "axis axis--x")
    .style("opacity", 0)
    .call(bundle.axisBottom(x));

  ggg
    .append("g")
    .attr("class", "axis axis--x")
    .style("opacity", 0)
    .call(bundle.axisBottom(x));

  gg.append("g")
    .attr("class", "axis axis--y")
    .style("opacity", 0)
    .call(bundle.axisLeft(y).ticks);

  gg.append("g")
    .selectAll("rect")
    .data(
      Object.entries(freq["second_choice"]).map((entry) => ({
        key: entry[0],
        value: entry[1],
      })),
    )
    .enter()
    .append("rect")
    .attr("id", `second_choice-${id}`)
    .attr("finalwidth", function (d) {
      return x(d.value);
    })
    .attr("x", x(0))
    .attr("y", function (d) {
      return y(d.key);
    })
    .attr("width", 0)
    .attr(
      "height",
      firstFreqSvg.attr("height") /
        Object.values(freq["second_choice"]).length,
    )
    .attr("fill", "gray")
    .style("stroke", "white")
    .style("opacity", 0.2);

  ggg
    .append("g")
    .selectAll("rect")
    .data(
      Object.entries(freq["first_choice"]).map((entry) => ({
        key: entry[0],
        value: entry[1],
      })),
    )
    .enter()
    .append("rect")
    .attr("id", `first_choice-${id}`)
    .attr("finalwidth", function (d) {
      return x(d.value);
    })
    .attr("finalx", function (d) {
      return x(1 - d.value);
    })
    .attr("x", x(1))
    .attr("y", function (d) {
      return y(d.key);
    })
    .attr("width", 0)
    .attr(
      "height",
      firstFreqSvg.attr("height") / Object.values(freq["first_choice"]).length,
    )
    .attr("fill", "gray")
    .style("stroke", "white")
    .style("opacity", 0.2);

  gg.append("g")
    .selectAll("text")
    .data(
      Object.entries(freq["second_choice"]).map((entry) => ({
        key: entry[0],
        value: entry[1],
      })),
    )
    .enter()
    .append("text")
    .attr("x", x(0))
    .attr("dx", -2)
    .attr("y", function (d) {
      return y(d.key);
    })
    .attr("dy", y.bandwidth() / 2 + 4)
    .style("font-size", "8pt")
    .style("text-anchor", "end")
    .text(function (d) {
      return `${parseInt(100 * d.value)}%`;
    });

  ggg
    .append("g")
    .selectAll("text")
    .data(
      Object.entries(freq["first_choice"]).map((entry) => ({
        key: entry[0],
        value: entry[1],
      })),
    )
    .enter()
    .append("text")
    .attr("x", x(1))
    .attr("dx", 2)
    .attr("y", function (d) {
      return y(d.key);
    })
    .attr("dy", y.bandwidth() / 2 + 4)
    .style("font-size", "8pt")
    .style("text-anchor", "start")
    .text(function (d) {
      return `${parseInt(100 * d.value)}%`;
    });

  gg.append("g")
    .selectAll("text")
    .data(
      Object.entries(freq["second_choice"]).map((entry) => ({
        key: entry[0],
        value: entry[1],
      })),
    )
    .enter()
    .append("text")
    .attr("x", x(0))
    .attr("dx", 2)
    .attr("y", function (d) {
      return y(d.key);
    })
    .attr("dy", y.bandwidth() / 2 + 4)
    .style("font-size", "8pt")
    .text(function (d) {
      return d.key;
    });

  return;
}

/** Search function
 *  @param {String} className
 *  @param {Object} searchBar
 *  @function
 */
export function search(className, searchBar) {
  const items = document.querySelectorAll(className);
  for (let i = 0; i < items.length; i++) {
    if (
      items[i].innerText.toLowerCase().indexOf(searchBar.value.toLowerCase()) <
      0
    ) {
      items[i].style.display = "none";
    } else {
      items[i].style.display = "block";
    }
  }
  return;
}

/** Add dialog box to ids containing string dialog using #activate-id
 *  @function
 */
export function addDialog() {
  [].forEach.call(document.querySelectorAll("[id^=dialog]"), (el) => {
    const dialog = bundle.dialog.MDCDialog.attachTo(el);
    document.querySelector(`#activate-${el.id}`).onclick = () => {
      dialog.show();
    };
  });
}

/** Toggle image visibility
 *  @function
 */
export function toggleImages() {
  [].forEach.call(document.querySelectorAll(".toggle-images"), (el) => {
    const toggle = bundle.iconToggle.MDCIconToggle.attachTo(el);
    if (sessionStorage.images !== undefined) {
      if (sessionStorage.images == "block") {
        toggle.on = true;
      } else {
        toggle.on = false;
      }
      [].forEach.call(document.querySelectorAll(".question-image"), (el) => {
        if (sessionStorage.images == "block") {
          el.style.display = "block";
        } else {
          el.style.display = "none";
        }
      });
    }
    el.addEventListener("MDCIconToggle:change", ({ detail }) => {
      [].forEach.call(document.querySelectorAll(".question-image"), (el) => {
        if (detail.isOn) {
          el.style.display = "block";
        } else {
          el.style.display = "none";
        }
        sessionStorage.images = el.style.display;
      });
    });
  });
}

/** Toggle answer visibility
 *  @function
 */
export function toggleAnswers() {
  [].forEach.call(document.querySelectorAll(".toggle-answers"), (el) => {
    const toggle = bundle.iconToggle.MDCIconToggle.attachTo(el);
    if (sessionStorage.answers) {
      if (sessionStorage.answers == "block") {
        toggle.on = true;
      } else {
        toggle.on = false;
      }
      [].forEach.call(document.querySelectorAll(".question-answers"), (el) => {
        el.style.display = sessionStorage.answers;
      });
    }
    el.addEventListener("MDCIconToggle:change", ({ detail }) => {
      [].forEach.call(document.querySelectorAll(".question-answers"), (el) => {
        if (detail.isOn) {
          el.style.display = "block";
        } else {
          el.style.display = "none";
        }
        sessionStorage.answers = el.style.display;
      });
    });
  });
}

/** Bind mdc-checkbox
 *  @function
 */
export function bindCheckbox() {
  [].forEach.call(document.querySelectorAll(".mdc-checkbox"), (el) => {
    bundle.checkbox.MDCCheckbox.attachTo(el);
  });
}

/* Plot student activity */
export function plotTimeSeries(
  el: string,
  d: {
    answers: [string];
    distribution_date: string;
    due_date: string;
    last_login: string;
    now: string;
    total: number;
  },
): void {
  console.debug(el, d);
  const svg = d3.select(el);

  const width = 0.8 * d3.select("main").node().getBoundingClientRect().width;
  svg.attr("width", width);
  const height = +svg.attr("height");

  svg.selectAll("g").remove();

  const x = d3
    .scaleTime()
    .domain([
      new Date(d3.timeParse(d.distribution_date)),
      new Date(d3.timeParse(d.due_date)),
    ])
    .range([0, width]);
  const y = d3.scaleLinear().domain([0, d.total]).range([height, 0]);

  const xAxis = d3.axisBottom(x);
  const xAxisTop = d3.axisTop(x).ticks("");

  const g = svg.append("g");

  g.append("rect")
    .attr("fill", "white")
    .attr("x", 0)
    .attr("y", 0)
    .attr("width", width)
    .attr("height", height);

  g.append("g").attr("transform", `translate(0,${height})`).call(xAxis);
  g.append("g").call(xAxisTop);

  const format = d3.timeFormat("%c");

  const f = d3
    .line()
    .x(function (d) {
      return x(new Date(d3.timeParse(d)));
    })
    .y(function (d, i) {
      return y(i + 1);
    })
    .curve(d3.curveStepAfter);

  g.append("g")
    .selectAll("path")
    .data([d.answers])
    .enter()
    .append("path")
    .attr("stroke", "#004266")
    .attr("stroke-width", "2px")
    .attr("stroke-linecap", "round")
    .attr("fill", "none")
    .attr("d", f);

  if (d.due_date > d.last_login) {
    const endDate = Math.min(
      new Date(d3.timeParse(d.now)),
      new Date(d3.timeParse(d.due_date)),
    );
    g.append("rect")
      .attr("stroke", "black")
      .attr("stroke-width", "1px")
      .attr("fill", "gray")
      .style("opacity", 0.2)
      .attr("x", function () {
        return x(new Date(d3.timeParse(d.last_login)));
      })
      .attr("y", function () {
        return 0;
      })
      .attr("width", function () {
        return x(endDate) - x(new Date(d3.timeParse(d.last_login)));
      })
      .attr("height", height);
  }

  g.append("path")
    .attr("class", "slider")
    .attr("stroke", "gray")
    .attr("stroke-width", "0.5px")
    .attr("d", function () {
      const path = d3.path();
      path.moveTo(0, height + 30);
      path.lineTo(0, -6);
      return path;
    });

  g.append("text")
    .attr("x", width)
    .attr("dx", -5)
    .attr("y", -25)
    .attr("text-anchor", "end")
    .style("font-size", "10px")
    .style("font-family", "sans-serif")
    .text(format(new Date(d3.timeParse(d.due_date))));

  g.append("text")
    .attr("x", 0)
    .attr("dx", 5)
    .attr("y", -25)
    .attr("text-anchor", "start")
    .style("font-size", "10px")
    .style("font-family", "sans-serif")
    .text(format(new Date(d3.timeParse(d.distribution_date))));

  g.append("path")
    .attr("class", "limit")
    .attr("stroke", "gray")
    .attr("stroke-dasharray", 4)
    .attr("stroke-width", "0.5px")
    .attr("d", function () {
      const path = d3.path();
      path.moveTo(0, height);
      path.lineTo(0, -30);
      return path;
    });

  g.append("path")
    .attr("class", "limit")
    .attr("stroke", "gray")
    .attr("stroke-dasharray", 4)
    .attr("stroke-width", "0.5px")
    .attr("d", function () {
      const path = d3.path();
      path.moveTo(width, height);
      path.lineTo(width, -30);
      return path;
    });

  g.append("text")
    .attr("class", "slider-label-bottom")
    .attr("x", 0)
    .attr("dx", 5)
    .attr("y", height + 25)
    .attr("dy", 5)
    .attr("text-anchor", "start")
    .style("font-size", "10px")
    .style("font-family", "sans-serif")
    .text();

  g.append("text")
    .attr("class", "slider-label-top")
    .attr("x", 0)
    .attr("y", -6)
    .attr("dy", -5)
    .attr("text-anchor", "middle")
    .style("font-size", "10px")
    .style("font-family", "sans-serif")
    .text();

  const area = d3
    .area()
    .x0(f.x())
    .y0(height)
    .x1(f.x())
    .y1(f.y())
    .curve(d3.curveStepAfter);

  svg.on("mousemove", function (event) {
    const xValue = Math.min(
      d3.pointer(event)[0],
      1 + x(d3.max(d.answers.map((x) => new Date(d3.timeParse(x))))),
    );

    g.select(".slider").attr("d", function () {
      const path = d3.path();
      path.moveTo(xValue, height + 30);
      path.lineTo(xValue, -6);
      return path;
    });

    g.select(".slider-label-bottom")
      .attr("text-anchor", function () {
        if (xValue < width / 2) {
          return "start";
        }
        return "end";
      })
      .attr("dx", function () {
        if (xValue < width / 2) {
          return 5;
        }
        return -5;
      })
      .attr("x", xValue)
      .text(format(x.invert(xValue)));

    g.select(".slider-label-top")
      .attr("x", xValue)
      .text(
        `${
          (100 *
            d3.bisectLeft(
              d.answers.map((x) => new Date(d3.timeParse(x))),
              x.invert(xValue),
            )) /
          d.total
        }%`,
      );

    let data = d.answers.map((x) => new Date(d3.timeParse(x)));
    const index = d3.bisectLeft(data, x.invert(xValue));

    data = data.slice(0, index);

    if (data.length < d.answers.length) {
      data.push(x.invert(xValue));
    }

    g.select(".area").remove();
    g.append("path").datum(data).attr("class", "area").attr("d", area);
  });
}

// Commands
underlines();

// Listeners
window.addEventListener("resize", underlines);

// MDC
autoInit();
