import { buildReq } from "../ajax";
import { updateNotifications } from "./header/notifications";
import type { Notification } from "./header/notifications";

/** *******/

/* model */

/** *******/
const CHECK_EVERY = 1;
type Task = {
  id: string;
  description: string;
  completed: boolean;
  datetime: Date;
  error: boolean;
};
let model: {
  urls: {
    requestGradebook: string;
    gradebookResult: string;
    removeFailedGradebook: string;
    downloadGradebook: string;
    tasks: string;
  };
  tasks: Array<Task>;
};

function initModel(urls: {
  requestGradebook: string;
  gradebookResult: string;
  removeFailedGradebook: string;
  downloadGradebook: string;
  tasks: string;
}): void {
  model = {
    tasks: [],
    urls: {
      requestGradebook: urls.requestGradebook,
      gradebookResult: urls.gradebookResult,
      removeFailedGradebook: urls.removeFailedGradebook,
      downloadGradebook: urls.downloadGradebook,
      tasks: urls.tasks,
    },
  };
}

/** ********/

/* update */

/** ********/
function update(): void {
  getTasks();
}

function getTasks(): void {
  const url = model.urls.tasks;
  const req = buildReq({}, "get");
  fetch(url, req)
    .then((resp) => resp.json())
    .then((data) => {
      initTasks(data.tasks);
    });
}

async function initTasks(
  data: Array<{
    id: string;
    description: string;
    completed: boolean;
    datetime: string;
  }>,
): Promise<void> {
  model.tasks = data
    .map((task) => ({
      id: task.id,
      description: task.description,
      completed: task.completed,
      datetime: new Date(task.datetime),
      error: false,
    }))
    .sort((a, b) =>
      a.datetime > b.datetime ? -1 : a.datetime < b.datetime ? 1 : 0,
    );
  updateNotifications(getNotifications());
  Promise.all(
    model.tasks
      .filter((task) => !task.completed)
      .map((task) => getGradebookResult(task)),
  );
}

async function requestGradebook(event: MouseEvent): Promise<void> {
  event.stopPropagation();
  const button = event.currentTarget;
  const groupId = button.getAttribute("data-group");
  const assignmentId = button.getAttribute("data-assignment");
  const data = {
    group_id: groupId,
    assignment_id: assignmentId,
  };
  const url = model.urls.requestGradebook;
  const req = buildReq(data, "post");
  const resp = await fetch(url, req);

  if (resp.status === 200) {
    const data = await resp.text();
    const title = data.split("\n")[0];
    const csv = data.split("\n").slice(1).join("\n");

    _downloadGradebook(title, csv);
  } else if (resp.status === 201) {
    const data = await resp.json();
    const task = {
      id: data.id,
      description: data.description,
      completed: data.completed,
      datetime: new Date(data.datetime),
      error: false,
    };
    model.tasks.unshift(task);
    setTimeout(() => getGradebookResult(task), 0);
    updateNotifications(getNotifications());
  } else {
    console.log(resp);
  }
}

async function getGradebookResult(task: Task): Promise<void> {
  const url = model.urls.gradebookResult;
  const req = buildReq(
    {
      task_id: task.id,
    },
    "post",
  );
  const resp = await fetch(url, req);

  if (resp.status == 200) {
    task.completed = true;
    updateNotifications(getNotifications());
  } else if (resp.status == 202) {
    await new Promise((resolve) =>
      setTimeout(() => getGradebookResult(task), CHECK_EVERY * 1000),
    );
  } else {
    task.completed = true;
    task.error = true;
    updateNotifications(getNotifications());
  }
}

async function removeGradebookError(task: Task): Promise<void> {
  const url = model.urls.removeFailedGradebook;
  const req = buildReq(
    {
      task_id: task.id,
    },
    "post",
  );
  const resp = await fetch(url, req);

  if (resp.ok) {
    model.tasks = model.tasks.filter((t) => t.id !== task.id);
  }

  updateNotifications(getNotifications());
}

async function downloadGradebook(task: Task): Promise<void> {
  const data = {
    task_id: task.id,
  };
  const url = model.urls.downloadGradebook;
  const req = buildReq(data, "post");
  const resp = await fetch(url, req);

  if (resp.ok) {
    const data = await resp.text();
    const title = data.split("\n")[0];
    const csv = data.split("\n").slice(1).join("\n");

    _downloadGradebook(title, csv);

    model.tasks = model.tasks.filter((t) => t.id != task.id);
    updateNotifications(getNotifications());
  } else {
    console.log(resp);
  }
}

function _downloadGradebook(title: string, csv: string): void {
  const a = document.createElement("a");
  a.href = `data:text/csv;charset=utf-8, ${escape(csv)}`;
  a.target = "_blank";
  a.download = title;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

function getNotifications(): Array<Notification> {
  return model.tasks.map((task) => ({
    text: task.completed
      ? task.error
        ? `There was an error creating the gradebook for ${task.description}.`
        : `The ${task.description} is ready.`
      : `Computing the ${task.description}...`,
    inProgress: !task.completed,
    error: task.error,
    onClick:
      task.completed && !task.error
        ? async () => await downloadGradebook(task)
        : async () => undefined,
    onCloseClick: async () => await removeGradebookError(task),
  }));
}

/** ******/

/* view */

/** ******/

/** ***********/

/* listeners */

/** ***********/
function initListeners(): void {
  addGradebookListeners();
}

function addGradebookListeners(): void {
  [...document.getElementsByClassName("gradebook-button")].forEach(
    (button) => {
      button.addEventListener(
        "click",
        async (event: MouseEvent) => await requestGradebook(event),
      );
    },
  );
}

/** ******/

/* init */

/** ******/
export function init(urls: {
  requestGradebook: string;
  gradebookResult: string;
  removeFailedGradebook: string;
  downloadGradebook: string;
  tasks: string;
}): void {
  initModel(urls);
  update();
  initListeners();
}
