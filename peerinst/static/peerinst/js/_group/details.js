// @flow
import { buildReq } from "../ajax.js";
import { editField } from "./common.js";

/*********/
/* model */
/*********/

type InitialData = {
  assignments: Array<{ url: string }>,
  students: Array<number>,
  urls: { update_url: string, get_student_information_url: string },
};

type Assignment = {
  url: string,
};

type Student = {
  id: number,
  email: ?string,
  lastLogin: ?Date,
  popularity: ?number,
};

let model: {
  language: string,
  assignments: Array<Assignment>,
  students: Array<Student>,
  urls: {
    updateUrl: string,
    getStudentInformationUrl: string,
  },
};

function initModel(data: InitialData): void {
  model = {
    language:
      document.getElementById("corner")?.getElementsByTagName("text")[0]
        .textContent == "FR"
        ? "en-ca"
        : "fr-ca",
    assignments: data.assignments.map(a => ({
      url: a.url,
    })),
    students: data.students.map(s => ({
      id: s,
      email: null,
      lastLogin: null,
      popularity: null,
    })),
    urls: {
      updateUrl: data.urls.update_url,
      getStudentInformationUrl: data.urls.get_student_information_url,
    },
  };
}

/**********/
/* update */
/**********/

async function update(): Promise<void> {
  model.students.forEach(student => {
    getStudentInformation(student);
  });
}

function removeAssignment(event: MouseEvent, url: string): void {
  event.stopPropagation();
  const li = event.currentTarget.parentNode.parentNode;
  const container = li.parentNode;

  const req = buildReq({}, "post");
  url = url + "remove/";

  fetch(url, req).then(function(resp) {
    if (resp.ok) {
      container.removeChild(li.nextSibling);
      container.removeChild(li);
      if (container.children.length == 1) {
        location.reload();
      }
    }
  });
}

function toggleStudentIdNeeded(event: MouseEvent, url: string): void {
  const idNeeded = event.currentTarget.checked;
  const data = {
    name: "student_id_needed",
    value: idNeeded,
  };
  const req = buildReq(data, "post");
  fetch(url, req)
    .then(function(resp) {
      if (!resp.ok) {
        console.log(resp);
      }
    })
    .catch(function(err) {
      console.log(err);
    });
}

export async function createCollection(
  groupPk,
  addAssignmentUrl,
  collectionUpdateUrl,
) {
  const req = buildReq({ group_pk: groupPk }, "post");
  const resp = await fetch(addAssignmentUrl, req);
  const data = await resp.json();
  window.location.assign(collectionUpdateUrl.replace("0", `${data.pk}`));
}

async function getStudentInformation(student: Student): Promise<void> {
  const req = buildReq({ id: student.id }, "post");

  const resp = await fetch(model.urls.getStudentInformationUrl, req);
  if (!resp.ok) {
    console.log(resp);
    return;
  }

  const data = await resp.json();
  student.email = data.email;
  student.lastLogin = new Date(data.last_login);
  student.popularity = data.popularity;

  studentListTableView(student);
}

/********/
/* view */
/********/

function studentListTableView(student: Student): void {
  // $FlowFixMe
  const table = $("#student_reputation_table").DataTable(); // eslint-disable-line
  table.row
    .add([
      student.email,
      student.lastLogin
        ? student.lastLogin.toLocaleString(model.language, {
            month: "short", // eslint-disable-line
            day: "numeric", // eslint-disable-line
            year: "numeric", // eslint-disable-line
            hour: "2-digit", // eslint-disable-line
            minute: "2-digit", // eslint-disable-line
          }) // eslint-disable-line
        : "",
      student.popularity,
    ])
    .draw();
}

/*************/
/* listeners */
/*************/

function initListeners(): void {
  addLinkListeners();
  addRemoveAssignmentListeners();
  addEditListeners();
  addToggleIdListener();
}

function addLinkListeners(): void {
  const links = document.getElementsByClassName("assignment-link");

  for (let i = 0; i < links.length; i++) {
    links[i].addEventListener("click", (event: MouseEvent) => {
      window.location.assign(model.assignments[i].url);
    });
  }
}

function addRemoveAssignmentListeners(): void {
  const btns = document.getElementsByClassName("delete-btn");

  for (let i = 0; i < btns.length; i++) {
    btns[i].addEventListener("click", (event: MouseEvent) => {
      removeAssignment(event, model.assignments[i].url);
    });
  }
}

function addEditListeners(): void {
  [...document.getElementsByClassName("edit-btn")].forEach(btn => {
    btn.addEventListener("click", (event: MouseEvent) => {
      editField(event, "text", "mdc-list-item__secondary-text");
    });
  });
}

function addToggleIdListener(): void {
  document
    .getElementById("toggle-id-btn")
    .addEventListener("click", (event: MouseEvent) => {
      toggleStudentIdNeeded(event, model.urls.updateUrl);
    });
}

/********/
/* init */
/********/

export function init(data: InitialData): void {
  initModel(data);
  initListeners();
  update();
}
