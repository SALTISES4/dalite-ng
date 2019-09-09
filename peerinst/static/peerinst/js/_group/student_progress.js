import * as d3 from "d3";
import { buildReq } from "../ajax.js";
import { clear, createSvg } from "../utils.js";

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
    results: data.map(question => ({
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
  model.results.map(function(question) {
    progress.append(questionView(question));
  });
}

function legendView() {
  const li = document.createElement("li");
  li.classList.add("mdc-list-item");

  const legend = document.createElement("span");
  legend.id = "student-progress-legend";
  legend.classList.add("mdc-list-item__meta");
  li.appendChild(legend);

  const done = document.createElement("span");
  done.textContent = "Question done";
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
  li.classList.add("mdc-list-item");

  const image = document.createElement("span");
  image.classList.add("mdc-list-item__graphic", "mdc-theme--primary");
  const i = document.createElement("i");
  i.classList.add("mdc-theme--primary", "material-icons", "md-48");
  i.textContent = "question_answer";
  image.append(i);
  li.append(image);

  const title = document.createElement("span");
  title.classList.add("mdc-list-item__text", "mdc-theme--secondary", "bold");
  title.textContent = question.questionTitle;
  const nStudents = document.createElement("span");
  nStudents.classList.add("mdc-list-item__secondary-text");
  nStudents.textContent = question.nStudents + " students";
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
  correctView(progress, question.nFirstCorrect, total, height, width);
  correctView(progress, question.nCorrect, total, height, width);

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
    .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

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
    .append("path")
    .attr("d", arcBackground)
    .attr("class", "fill-primary")
    .style("opacity", "0.10");

  svg
    .append("path")
    .datum({ endAngle: 0 })
    .attr("d", arcData)
    .attr("class", "fill-primary student-progress__path");

  svg
    .append("text")
    .attr("data-count", data)
    .attr("data-total", total)
    .text(0)
    .attr("text-anchor", "middle")
    .attr("dy", 8)
    .attr("class", "fill-primary student-progress__count")
    .attr("font-size", "20px");

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
    .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

  const colourScale = d3
    .scaleQuantile()
    .domain([0, 1])
    .range(["#b30000", "#f17f4d", "#339966"]);

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
    .append("path")
    .attr("d", arcBackground)
    .attr("class", "fill-primary")
    .style("opacity", "0.10");

  svg
    .append("path")
    .datum({ endAngle: 0 })
    .attr("d", arcData)
    .style("fill", colourScale(0))
    .attr("class", "student-progress__path");

  svg
    .append("text")
    .attr("data-count", data)
    .attr("data-total", total)
    .text(0)
    .attr("text-anchor", "middle")
    .attr("dy", 8)
    .style("fill", colourScale(0))
    .attr("font-size", "24px")
    .attr("class", "student-progress__count");

  return svg;
}

function toggleStudentProgressView() {
  const progress = document.querySelector("#student-progress");
  const complete = progress.querySelectorAll(".student-progress-complete");
  const correct = progress.querySelectorAll(".student-progress-correct");

  Array.from(complete).map(function(svg) {
    animateComplete(svg, !model.showing);
  });
  Array.from(correct).map(function(svg) {
    animateCorrect(svg, !model.showing);
  });
}

function animateComplete(svg, reverse = false) {
  const path_ = svg.querySelector(".student-progress__path");
  const count_ = svg.querySelector(".student-progress__count");
  const data = count_.getAttribute("data-count");
  const total = count_.getAttribute("data-total");

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

  const count = d3.select(count_);

  function animation(transition, newAngle) {
    transition.attrTween("d", function(d) {
      const interpolate = d3.interpolate(d.endAngle, newAngle);
      const interpolateCount = d3.interpolate(start, end);
      return function(t) {
        d.endAngle = interpolate(t);
        count.text(Math.floor(interpolateCount(t)));
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
  const data = count_.getAttribute("data-count");
  const total = count_.getAttribute("data-total");

  const colourScale = d3
    .scaleQuantile()
    .domain([0, 1])
    .range(["#b30000", "#f17f4d", "#339966"]);

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

  const count = d3.select(count_);

  function animation(transition, newAngle) {
    transition.attrTween("d", function(d) {
      const interpolate = d3.interpolate(d.endAngle, newAngle);
      const interpolateCount = d3.interpolate(start, end);
      return function(t) {
        d.endAngle = interpolate(t);
        const newCount = interpolateCount(t);
        path.style("fill", colourScale((newCount / total) | 0));
        count.text(Math.floor(newCount));
        count.style("fill", colourScale((newCount / total) | 0));
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

export function initStudentProgress(url) {
  view();
  initListeners();
  const req = buildReq(null, "get");
  fetch(url, req)
    .then(resp => resp.json())
    .then(function(data) {
      initModel(data.progress);
    })
    .catch(err => console.log(err));
}
