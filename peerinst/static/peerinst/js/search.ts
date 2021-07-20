/* global pageNav */
declare let bundle: any; // bundle will be available globally at runtime

import { updateAssignmentQuestionList } from "./ajax.js";

/** Recount search results
 *  @function
 */
export function recountResults() {
  $(".search-set").each(function () {
    $(this) // eslint-disable-line
      .find(".filter-count")
      .empty()
      .append($(this).find(".mdc-card:visible").length); // eslint-disable-line
  });
}

/** Filter search results
 *  @function
 *  @param {String} el
 */
export function filter(el) {
  if ($(el).hasClass("mdc-chip--selected")) {
    $(el).removeClass("mdc-chip--selected");
  } else {
    $(el).addClass("mdc-chip--selected");
  }

  if ($(".mdc-chip--selected").length == 0) {
    $("#reset-filters").prop("disabled", true);
  }

  $("#search_results .mdc-card").css("display", "block");

  $("#search_results .mdc-card").each(function () {
    const card = this; // eslint-disable-line
    $("#filter-on-category")
      .find(".mdc-chip--selected")
      .each(function () {
        if (
          card
            .getAttribute("category")
            .toLowerCase()
            .indexOf(this.getAttribute("c").toLowerCase()) < 0 // eslint-disable-line
        ) {
          $(card).css("display", "none");
          $("#reset-filters").prop("disabled", false);
        }
      });

    $("#filter-on-discipline")
      .find(".mdc-chip--selected")
      .each(function () {
        if (
          card.getAttribute("discipline").slice(1, -1).toLowerCase() !=
          this.getAttribute("d").toLowerCase() // eslint-disable-line
        ) {
          $(card).css("display", "none");
          $("#reset-filters").prop("disabled", false);
        }
      });
  });

  recountResults();
}

/** Reset filters
 *  @function
 */
export function reset() {
  $("#search_results .mdc-card").each(function () {
    $(this).css("display", "block"); // eslint-disable-line
    $(".mdc-chip").removeClass("mdc-chip--selected");
    $("#reset-filters").prop("disabled", true);
  });

  recountResults();
}

/** Process response for required filters
 *  @function
 */
export function processResponse() {
  bundle.toggleImages();
  bundle.toggleAnswers();

  $("#search-bar").prop("disabled", false);
  $("#progressbar").addClass("mdc-linear-progress--closed");

  // Update template response
  $(".search-nav").each(function (i, el) {
    el.addEventListener("click", function () {
      pageNav(el.getAttribute("data-page"));
    });
  });

  $(".update-questions-btn").each(function (i, el) {
    el.addEventListener("click", function () {
      updateAssignmentQuestionList(
        el.getAttribute("data-url"),
        el.getAttribute("data-id"),
        el.getAttribute("data-assignment-id"),
      );
    });
  });

  // Add filters based on search results
  $("#filter-on-discipline").empty();
  $("#filter-on-category").empty();

  const disciplineList = [];
  $("#filter-on-discipline").append(
    "<div class='mdc-chip-set mdc-chip-set--filter' " +
      "data-mdc-auto-init='MDCChipSet'></div>",
  );
  $("#search_results .mdc-card").each(function (index) {
    const d = this.getAttribute("discipline"); // eslint-disable-line
    if (!disciplineList.includes(d) & (d.slice(1, -1) != "None")) {
      disciplineList.push(d);
    }
  });
  disciplineList.sort();
  for (let i = 0; i < disciplineList.length; i++) {
    $("#filter-on-discipline .mdc-chip-set").append(
      `<div d=${disciplineList[i]} class='mdc-chip' ` +
        "tabindex='0' data-mdc-auto-init='MDCChip'>" +
        "<div class='mdc-chip__checkmark' >" +
        "<svg class='mdc-chip__checkmark-svg' viewBox='-2 -3 30 30'>" +
        "<path class='mdc-chip__checkmark-path' fill='none' stroke='black'" +
        "d='M1.73,12.91 8.1,19.28 22.79,4.59'/>" +
        "</svg>" +
        "</div>" +
        `<div class='mdc-chip__text'>${disciplineList[i].slice(1, -1)}</div>` +
        "</div>",
    );
  }

  $("#filter-on-discipline .mdc-chip").each(function (i, el) {
    el.addEventListener("click", function () {
      filter(el);
    });
  });

  const categoryList = [];
  $("#filter-on-category").append(
    "<div class='mdc-chip-set mdc-chip-set--filter' " +
      "data-mdc-auto-init='MDCChipSet'></div>",
  );
  $("#search_results .mdc-card").each(function () {
    const c = this.getAttribute("category"); // eslint-disable-line
    const list = c.split(",");
    $(list).each(function (i) {
      if (!categoryList.includes(list[i].toLowerCase()) & (list[i] != "")) {
        categoryList.push(list[i].toLowerCase());
      }
    });
  });
  categoryList.sort();
  for (let i = 0; i < categoryList.length; i++) {
    $("#filter-on-category .mdc-chip-set").append(
      `<div c=${categoryList[i]} class='mdc-chip' tabindex='0' ` +
        "data-mdc-auto-init='MDCChip'>" +
        "<div class='mdc-chip__checkmark' >" +
        "<svg class='mdc-chip__checkmark-svg' viewBox='-2 -3 30 30'>" +
        "<path class='mdc-chip__checkmark-path' fill='none' " +
        "stroke='black'" +
        "d='M1.73,12.91 8.1,19.28 22.79,4.59'/>" +
        "</svg>" +
        "</div>" +
        `<div class='mdc-chip__text'>${categoryList[i]}</div>` +
        "</div>",
    );
  }
  $("#filter-on-category .mdc-chip").each(function (i, el) {
    el.addEventListener("click", function () {
      filter(el);
    });
  });

  if (
    (disciplineList.length > 1 || categoryList.length > 1) &&
    $("#search_results .mdc-card").length > 1
  ) {
    $("#filters").css("display", "block");
    window.location.href = "#filters";
  } else {
    window.location.href = "#search_results";
  }
  if (disciplineList.length > 1) {
    $("#discipline-filters").css("display", "block");
  }
  if (categoryList.length > 1) {
    $("#category-filters").css("display", "block");
  }

  [].forEach.call(document.querySelectorAll(".mdc-chip"), (el) => {
    bundle.chips.MDCChip.attachTo(el);
  });

  [].forEach.call(document.querySelectorAll(".mdc-chip-set"), (el) => {
    bundle.chips.MDCChipSet.attachTo(el);
  });

  [].forEach.call(document.querySelectorAll(".mdc-icon-toggle"), (el) => {
    bundle.iconToggle.MDCIconToggle.attachTo(el);
  });

  [].forEach.call(
    document.querySelectorAll("#search_results .mdc-card"),
    (el) => {
      bundle.difficulty(el.getAttribute("matrix").replace(/'/g, '"'), el.id); // eslint-disable-line
    },
  );
}

/** Set up search
 *  @function
 */
export function setupSearch() {
  $("#search_results").empty();
  $("#filters").css("display", "none");
  $("#show-discipline-filters").css("display", "none");
  $("#show-category-filters").css("display", "none");
  $("#search-bar").prop("disabled", true);
  $("#progressbar").removeClass("mdc-linear-progress--closed");
  window.location.href = "#progressbar";
}

/** Initialize likes
 *  @function
 */
export function initFavourites() {
  [].forEach.call(document.querySelectorAll(".mdc-icon-toggle"), (el) => {
    bundle.iconToggle.MDCIconToggle.attachTo(el);
  });
}
