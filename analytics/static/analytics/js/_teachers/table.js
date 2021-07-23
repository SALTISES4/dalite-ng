import { buildReq } from "../../../../../peerinst/static/peerinst/js/ajax.js";
import { formatDatetime } from "../../../../../peerinst/static/peerinst/js/utils"; // eslint-disable-line

/*********/
/* model */
/*********/

let model;

function initModel(urls) {
  model = {
    criteria: [],
    teachers: [],
    urls: {
      getCriteria: urls.getCriteria,
      getTeachers: urls.getTeachers,
      getTeacherInformation: urls.getTeacherInformation,
    },
  };
}

/**********/
/* update */
/**********/

async function update() {
  await Promise.all([getCriteria(), getTeachers()]);
  getTeachersInformation();
}

async function getCriteria() {
  const req = buildReq({}, "get");

  const resp = await fetch(model.urls.getCriteria, req);
  const data = await resp.json();
  model.criteria = data.criteria.map((criterion) => ({
    name: criterion.name,
    full_name: criterion.full_name,
    description: criterion.description,
  }));
  tableView();
}

async function getTeachers() {
  const req = buildReq({}, "get");

  const resp = await fetch(model.urls.getTeachers, req);
  const data = await resp.json();
  model.teachers = data.teachers.map((teacher) => ({
    id: teacher,
    username: null,
    lastLogin: null,
    reputations: [],
  }));
}

function getTeachersInformation() {
  model.teachers.forEach((teacher) => {
    getTeacherInformation(teacher);
  });
}

async function getTeacherInformation(teacher) {
  const req = buildReq({}, "get");
  const url = `${model.urls.getTeacherInformation}?id=${teacher.id}`;

  const resp = await fetch(url, req);
  const data = await resp.json();
  teacher.username = data.username;
  teacher.lastLogin = data.last_login ? new Date(data.last_login) : null;
  teacher.reputations = data.reputations.map((reputation) => ({
    name: reputation.name,
    reputation: reputation.reputation,
  }));
  tableRowView(teacher);
}

/********/
/* view */
/********/

function tableView() {
  tableHeadersView();

  const table = document.getElementById("teacher-list");

  // prettier-ignore
  $(table).DataTable({ // eslint-disable-line new-cap
    pageLength: 50,
    dom:
      '<"' + // eslint-disable-line quotes
      "fg-toolbar" +
      " ui-toolbar" +
      " ui-widget-header" +
      " ui-helper-clearfix" +
      " ui-corner-tl" +
      ' ui-corner-tr"Bf' + // eslint-disable-line quotes
      ">" +
      "t" +
      '<"' + // eslint-disable-line quotes
      "fg-toolbar" +
      " ui-toolbar" +
      " ui-widget-header" +
      " ui-helper-clearfix" +
      " ui-corner-tl" +
      ' ui-corner-tr"ip' + // eslint-disable-line quotes
      ">",
    buttons: ["csv", "colvis"],
  });

  table.removeAttribute("hidden");
}

function tableHeadersView() {
  const headers = document.querySelector("#teacher-list thead tr");
  model.criteria.forEach((criterion) => {
    const header = document.createElement("th");
    header.title = criterion.description;
    header.textContent = criterion.full_name;
    headers.appendChild(header);
  });
}

function tableRowView(teacher) {
  $("#teacher-list")
    .DataTable() // eslint-disable-line
    .row.add([
      ...[
        teacher.username,
        teacher.lastLogin ? formatDatetime(teacher.lastLogin) : "",
      ],
      ...model.criteria.map(
        (criterion) =>
          teacher.reputations.find(
            (reputation) => reputation.name == criterion.name,
          ).reputation,
      ),
    ])
    .draw(false);
}

/********/
/* init */
/********/

export async function init(urls) {
  initModel(urls);
  await update();
}
