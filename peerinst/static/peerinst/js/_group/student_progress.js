import * as d3 from "d3";
import { buildReq } from "../ajax.js";
import { clear, createSvg } from "../utils.ts";
import { quintileScale } from "../_theming/colours.js";

/*********/
/* model */
/*********/

let model = {
  dataLoaded: false,
  showing: false,
};

function initModel(data) {
  model = {
    dataLoaded: true,
    showing: document
      .querySelector("#student-progress")
      .parentNode.parentNode.classList.contains("foldable__unfolded"),
    results: data.map((question) => ({
      questionId: question.question_id,
      questionTitle: question.question_title,
      nStudents: question.n_students,
      nCompleted: question.n_completed,
      nFirstCorrect: question.n_first_correct,
      nCorrect: question.n_correct,
      timeSpent: question.time_spent,
    })),
  };
  progressView();
  if (model.showing) {
    toggleStudentProgressView();
  }
}

/**********/
/* update */
/**********/

function toggleStudentProgress() {
  model.showing = !model.showing;
  if (model.dataLoaded) {
    toggleStudentProgressView();
  }
}

/********/
/* view */
/********/

function view() {
  document
    .querySelector("#student-progress")
    .parentNode.parentNode.classList.remove("hidden");
  if (model.dataLoaded) {
    progressView();
  } else {
    loadingView();
  }
}

function loadingView() {
  const svg = createSvg("loader");
  svg.classList.add("loading-icon");
  document.querySelector("#student-progress").appendChild(svg);
}

function progressView() {
  const progress = document.querySelector("#student-progress");
  clear(progress);
  progress.appendChild(legendView());
  model.results.map(function (question) {
    progress.append(questionView(question));
  });
}

function legendView() {
  const li = document.createElement("li");
  li.classList.add("mdc-list-item");
  li.classList.add("no-pointer");

  const legend = document.createElement("span");
  legend.id = "student-progress-legend";
  legend.classList.add("mdc-list-item__meta");
  li.appendChild(legend);

  const done = document.createElement("span");
  done.textContent = "Questions completed";
  legend.appendChild(done);

  const first = document.createElement("span");
  first.textContent = "First answer correct";
  legend.appendChild(first);

  const second = document.createElement("span");
  second.textContent = "Second answer correct";
  legend.appendChild(second);

  return li;
}

function questionView(question) {
  const li = document.createElement("li");
  li.setAttribute("data-id", question.questionId);
  li.classList.add("mdc-list-item");
  li.classList.add("link-feedback-dialog");

  const image = document.createElement("span");
  image.classList.add("mdc-list-item__graphic", "mdc-theme--primary");
  const i = document.createElement("i");
  i.classList.add("mdc-theme--primary", "material-icons", "md-48");
  i.textContent = "fact_check";
  image.append(i);
  li.append(image);

  const title = document.createElement("span");
  title.classList.add("mdc-list-item__text", "mdc-theme--secondary", "bold");
  title.textContent = question.questionTitle;
  const nStudents = document.createElement("span");
  nStudents.classList.add("mdc-list-item__secondary-text");
  nStudents.textContent = "Click to give feedback";
  const timeSpent = document.createElement("span");
  timeSpent.classList.add(
    "mdc-list-item__secondary-text",
    "student-progress__time_taken",
  );
  if (question.timeSpent) {
    timeSpent.textContent = question.timeSpent;
  }
  title.append(nStudents);
  title.append(timeSpent);
  li.append(title);

  const progress = document.createElement("span");
  progress.classList.add("mdc-list-item__meta");
  li.append(progress);

  const width = 62;
  const height = 48;
  const total = question.nStudents;

  completeView(progress, question.nCompleted, total, height, width);
  correctView(
    progress,
    question.nFirstCorrect,
    question.nCompleted,
    height,
    width,
  );
  correctView(progress, question.nCorrect, question.nCompleted, height, width);

  return li;
}

function completeView(container, data, total, height, width) {
  const radius = Math.min(width, height) / 2;

  const svg = d3
    .select(container)
    .append("svg")
    .attr("class", "student-progress-complete")
    .attr("width", width)
    .attr("height", height)
    .append("g")
    .attr("transform", `translate(${width / 2},${height / 2})`);

  const colourScale = d3
    .scaleThreshold(quintileScale)
    .domain([0.2, 0.4, 0.6, 0.8]);

  const arcBackground = d3
    .arc()
    .innerRadius(radius - 5)
    .outerRadius(radius)
    .startAngle(0)
    .endAngle(2 * Math.PI);

  const arcData = d3
    .arc()
    .innerRadius(radius - 5)
    .outerRadius(radius)
    .startAngle(0);

  svg
    .append("circle")
    .attr("class", "background")
    .attr("cx", 0)
    .attr("cy", 0)
    .attr("r", radius);

  svg.append("path").attr("d", arcBackground).attr("class", "arc gray");

  svg
    .append("path")
    .datum({ endAngle: 0 })
    .attr("d", arcData)
    .attr("fill", colourScale(0))
    .attr("class", "student-progress__path");

  svg
    .append("circle")
    .attr("cx", 0)
    .attr("cy", 0)
    .attr("r", radius - 5)
    .attr("class", "student-progress__background")
    .attr("fill", colourScale(0));

  svg
    .append("text")
    .attr("data-count", data)
    .attr("data-total", total)
    .text(0)
    .attr("text-anchor", "middle")
    .attr("dy", 7)
    .attr("fill", colourScale(0))
    .attr("class", "student-progress__count")
    .attr("font-size", "20px")
    .attr("font-weight", "bold");

  svg
    .append("text")
    .text("%")
    .attr("text-anchor", "middle")
    .attr("dy", 15)
    .attr("fill", colourScale(0))
    .attr("font-size", "8px")
    .attr("font-weight", "bold")
    .attr("class", "student-progress__units");

  return svg;
}

function correctView(container, data, total, height, width) {
  const radius = Math.min(width, height) / 2;

  const svg = d3
    .select(container)
    .append("svg")
    .attr("class", "student-progress-correct")
    .attr("width", width)
    .attr("height", height)
    .append("g")
    .attr("transform", `translate(${width / 2},${height / 2})`);

  const colourScale = d3
    .scaleThreshold(quintileScale)
    .domain([0.2, 0.4, 0.6, 0.8]);

  const arcBackground = d3
    .arc()
    .innerRadius(radius - 5)
    .outerRadius(radius)
    .startAngle(0)
    .endAngle(2 * Math.PI);

  const arcData = d3
    .arc()
    .innerRadius(radius - 5)
    .outerRadius(radius)
    .startAngle(0);

  svg
    .append("circle")
    .attr("class", "background")
    .attr("cx", 0)
    .attr("cy", 0)
    .attr("r", radius);

  svg.append("path").attr("d", arcBackground).attr("class", "arc gray");

  svg
    .append("path")
    .datum({ endAngle: 0 })
    .attr("d", arcData)
    .attr("fill", colourScale(0))
    .attr("class", "student-progress__path");

  svg
    .append("circle")
    .attr("cx", 0)
    .attr("cy", 0)
    .attr("r", radius - 5)
    .attr("class", "student-progress__background")
    .attr("fill", colourScale(0));

  svg
    .append("text")
    .attr("data-count", data)
    .attr("data-total", total)
    .text(0)
    .attr("text-anchor", "middle")
    .attr("dy", 7)
    .attr("font-size", "20px")
    .attr("fill", colourScale(0))
    .attr("font-weight", "bold")
    .attr("class", "student-progress__count");

  svg
    .append("text")
    .text("%")
    .attr("text-anchor", "middle")
    .attr("dy", 15)
    .attr("fill", colourScale(0))
    .attr("font-size", "8px")
    .attr("font-weight", "bold")
    .attr("class", "student-progress__units");

  return svg;
}

function toggleStudentProgressView() {
  const progress = document.querySelector("#student-progress");
  const complete = progress.querySelectorAll(".student-progress-complete");
  const correct = progress.querySelectorAll(".student-progress-correct");

  Array.from(complete).map(function (svg) {
    animateComplete(svg, !model.showing);
  });
  Array.from(correct).map(function (svg) {
    animateCorrect(svg, !model.showing);
  });
}

function animateComplete(svg, reverse = false) {
  const path_ = svg.querySelector(".student-progress__path");
  const count_ = svg.querySelector(".student-progress__count");
  const background_ = svg.querySelector(".student-progress__background");
  const units_ = svg.querySelector(".student-progress__units");
  const data = count_.getAttribute("data-count");
  const total = count_.getAttribute("data-total");

  const colourScale = d3
    .scaleThreshold(quintileScale)
    .domain([0.2, 0.4, 0.6, 0.8]);

  let start;
  let end;
  let delay;
  let duration;
  if (reverse) {
    start = data;
    end = 0;
    delay = 0;
    duration = 0;
  } else {
    start = 0;
    end = data;
    delay = 500;
    duration = 1500;
  }

  const width = svg.getAttribute("width");
  const height = svg.getAttribute("height");
  const radius = Math.min(width, height) / 2;

  const arcData = d3
    .arc()
    .innerRadius(radius - 5)
    .outerRadius(radius)
    .startAngle(0);

  const path = d3.select(path_).attr("d", arcData);
  const background = d3.select(background_);
  const units = d3.select(units_);
  const count = d3.select(count_);

  function animation(transition, newAngle) {
    transition.attrTween("d", function (d) {
      const interpolate = d3.interpolate(d.endAngle, newAngle);
      const interpolateCount = d3.interpolate(start, end);
      return function (t) {
        d.endAngle = interpolate(t);
        const newCount = interpolateCount(t);
        count.text(total > 0 ? Math.floor((newCount / total) * 100) : 0);
        count.style("fill", colourScale(newCount / total));
        units.style("fill", colourScale(newCount / total));
        path.style("fill", colourScale(newCount / total));
        background.style("fill", colourScale(newCount / total));
        return arcData(d);
      };
    });
  }

  function animate() {
    path
      .transition()
      .delay(delay * Math.random())
      .duration(duration)
      .ease(d3.easeCubicInOut)
      .call(animation, (2 * Math.PI * end) / total);
  }

  setTimeout(animate, 0);
}

function animateCorrect(svg, reverse = false) {
  const path_ = svg.querySelector(".student-progress__path");
  const count_ = svg.querySelector(".student-progress__count");
  const background_ = svg.querySelector(".student-progress__background");
  const units_ = svg.querySelector(".student-progress__units");
  const data = count_.getAttribute("data-count");
  const total = count_.getAttribute("data-total");

  const colourScale = d3
    .scaleThreshold(quintileScale)
    .domain([0.2, 0.4, 0.6, 0.8]);

  let start;
  let end;
  let delay;
  let duration;
  if (reverse) {
    start = data;
    end = 0;
    delay = 0;
    duration = 0;
  } else {
    start = 0;
    end = data;
    delay = 500;
    duration = 1500;
  }

  const width = svg.getAttribute("width");
  const height = svg.getAttribute("height");
  const radius = Math.min(width, height) / 2;

  const arcData = d3
    .arc()
    .innerRadius(radius - 5)
    .outerRadius(radius)
    .startAngle(0);

  const path = d3.select(path_).attr("d", arcData);
  const background = d3.select(background_);
  const units = d3.select(units_);
  const count = d3.select(count_);

  function animation(transition, newAngle) {
    transition.attrTween("d", function (d) {
      const interpolate = d3.interpolate(d.endAngle, newAngle);
      const interpolateCount = d3.interpolate(start, end);
      return function (t) {
        d.endAngle = interpolate(t);
        const newCount = interpolateCount(t);
        count.text(total > 0 ? Math.floor((newCount / total) * 100) : 0);
        count.style("fill", colourScale(newCount / total));
        units.style("fill", colourScale(newCount / total));
        path.style("fill", colourScale(newCount / total));
        background.style("fill", colourScale(newCount / total));
        return arcData(d);
      };
    });
  }

  function animate() {
    path
      .transition()
      .delay(delay * Math.random())
      .duration(duration)
      .ease(d3.easeCubicInOut)
      .call(animation, (2 * Math.PI * end) / total);
  }

  setTimeout(animate, 0);
}

/*************/
/* listeners */
/*************/

function initListeners() {
  addToggleStudentProgressListener();
}

function addToggleStudentProgressListener() {
  document
    .querySelector("#student-progress")
    .parentNode.parentNode.querySelector(".foldable--title")
    .addEventListener("click", toggleStudentProgress);
}

/********/
/* init */
/********/

export function initStudentProgress(url, callback) {
  view();
  initListeners();
  const req = buildReq(null, "get");
  fetch(url, req)
    .then((resp) => resp.json())
    .then(function (data) {
      initModel(data.progress);
    })
    .then(() => {
      callback();
    })
    .catch((err) => console.log(err));
}
