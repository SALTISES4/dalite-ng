import { buildReq } from "../ajax.js";

/*********/
/* model */
/*********/
let model;

function initModel(data) {
  const disciplines = getDisciplines();
  model = {
    urls: {
      getGroupsActivity: data.urls.getGroupsActivity,
    },
    data: {
      disciplines: getDisciplines(),
    },
    state: {
      discipline: getDiscipline() || disciplines[0],
      activity: [],
    },
  };
  updateDiscipline(model.state.discipline);
}

function getDisciplines() {
  return [
    ...document.querySelectorAll("#discipline-activity__disciplines option"),
  ].map((elem) => elem.getAttribute("value"));
}

function getDiscipline() {
  return window.localStorage.getItem("group_activity_discipline");
}

/**********/
/* update */
/**********/

function updateDiscipline(discipline) {
  model.state.discipline = discipline;
  window.localStorage.setItem("group_activity_discipline", discipline);
  updateGroupsActivity();
}

async function updateGroupsActivity() {
  const req = buildReq({}, "get");
  const url = `${model.urls.getGroupsActivity}?discipline=${model.state.discipline}`;
  const resp = await fetch(url, req);
  model.state.activity = (await resp.json()).activity;
  updateTableData();
}

/********/
/* view */
/********/

function initView() {
  initSelectedDiscipline();
  initTables();
  initDisciplinesListeners();
}

function initSelectedDiscipline() {
  const select = document.querySelector("#discipline-activity__disciplines");
  select.value = model.state.discipline;
  select.removeAttribute("hidden");
}

function initTables() {
  document.querySelectorAll("table.display").forEach((elem) => {
    // prettier-ignore
    const table = $(elem).DataTable({ // eslint-disable-line
      pageLength: 10,
      dom:
        '<"fg-toolbar ui-toolbar ui-widget-header ui-helper-clearfix ui-corner-tl ui-corner-tr"Bf>t<"fg-toolbar ui-toolbar ui-widget-header ui-helper-clearfix ui-corner-bl ui-corner-br"ip>', // eslint-disable-line
      buttons: [],
    });
    table.order(0, "desc");
  });
}

function updateTableData() {
  const table = $("#discipline-activity__groups").DataTable(); // eslint-disable-line
  table.rows().remove();
  table.rows
    .add(
      model.state.activity.map((d) => [
        d.year,
        d.semester,
        d.name,
        d.teacher,
        d.n_students,
      ]),
    )
    .draw();
}

function initDisciplinesListeners() {
  document
    .querySelector("#discipline-activity__disciplines")
    .addEventListener("change", (event) =>
      updateDiscipline(event.currentTarget.value),
    );
}

/********/
/* init */
/********/

export async function init(data) {
  initModel(data);
  initView();
}
