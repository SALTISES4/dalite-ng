import { buildReq } from "../ajax.js";
import { clear } from "../utils.js";

/*********/
/* model */
/*********/

let model;

function initModel(data) {
  model = {
    expiryBlinkingDelay: data.expiry_blinking_delay,
    joiningGroup: false,
    newStudent: data.new_student,
    student: {
      username: data.student.username,
      email: data.student.email,
      memberSince: new Date(data.student.member_since),
      tos: {
        sharing: data.student.tos.sharing,
        signedOn: new Date(data.student.tos.signed_on),
      },
    },
    groups: data.groups.map(group => ({
      connectedCourseUrl: group.connected_course_url,
      groupReviewUrl: group.group_review_url,
      name: group.name,
      title: group.title,
      notifications: group.notifications,
      memberOf: group.member_of,
      assignments: group.assignments.map(assignment => ({
        title: assignment.title,
        dueDate: new Date(assignment.due_date),
        link: assignment.link,
        results: {
          grade: assignment.results.grade,
          n: assignment.results.n,
        },
        done: assignment.done,
        almostExpired: assignment.almost_expired,
      })),
      studentId: group.student_id,
      studentIdNeeded: group.student_id_needed,
    })),
    urls: {
      tosModify: data.urls.tos_modify,
      joinGroup: data.urls.join_group,
      leaveGroup: data.urls.leave_group,
      saveStudentId: data.urls.save_student_id,
      studentToggleGroupnotifications:
        data.urls.student_toggle_group_notifications,
    },
    translations: {
      assignmentAboutToExpire: data.translations.assignment_about_to_expire,
      assignmentExpired: data.translations.assignment_expired,
      cancel: data.translations.cancel,
      completed: data.translations.completed,
      courseFlowButton: data.translations.course_flow_button,
      groupReviewButton: data.translations.group_review_button,
      day: data.translations.day,
      days: data.translations.days,
      dueOn: data.translations.due_on,
      editStudentId: data.translations.edit_student_id,
      expired: data.translations.expired,
      goToAssignment: data.translations.go_to_assignment,
      grade: data.translations.grade,
      hour: data.translations.hour,
      hours: data.translations.hours,
      leave: data.translations.leave,
      leaveGroupQuestion: data.translations.leave_group_question,
      leaveGroupText: data.translations.leave_group_text,
      leaveGroupTitle: data.translations.leave_group_title,
      minute: data.translations.minute,
      minutes: data.translations.minutes,
      noAssignments: data.translations.no_assignments,
      notificationsBell: data.translations.notifications_bell,
      notSharing: data.translations.not_sharing,
      sharing: data.translations.sharing,
      studentId: data.translations.student_id,
      studentIdNeeded: data.translations.student_id_needed,
    },
  };
}

/**********/
/* update */
/**********/

function handleStudentIdKeyDown(key, group, node) {
  if (key === "Enter") {
    saveStudentId(group, node);
  } else if (key === "Escape") {
    stopEditStudentId(group, node);
  }
}

function saveStudentId(group, node) {
  const url = model.urls.saveStudentId;
  const input = node.querySelector("input");

  const data = {
    student_id: input.value,
    group_name: group.name,
  };

  const req = buildReq(data, "post");
  fetch(url, req)
    .then(resp => resp.json())
    .then(function(data) {
      group.studentId = data.student_id;
      stopEditStudentId(group, node);
    })
    .catch(function(err) {
      stopEditStudentId(group, node);
      console.log(err);
    });
}

function toggleGroupNotifications(group, bell) {
  const url = model.urls.studentToggleGroupnotifications;
  const data = {
    group_name: group.name,
  };
  const req = buildReq(data, "post");
  fetch(url, req)
    .then(resp => resp.json())
    .then(function(data) {
      group.notifications = data.notifications;
      if (group.notifications) {
        bell.textContent = "notifications";
        bell.classList.remove("student-group--notifications__disabled");
      } else {
        bell.textContent = "notifications_off";
        bell.classList.add("student-group--notifications__disabled");
      }
    })
    .catch(function(err) {
      console.log(err);
    });
}

function leaveGroup(group, groupNode) {
  const url = model.urls.leaveGroup;
  const data = {
    group_name: group.name,
  };

  const req = buildReq(data, "post");
  fetch(url, req)
    .then(function(resp) {
      if (resp.ok) {
        model.groups.filter(g => g.name === group.name)[0].memberOf = false;
        groupsView();
      } else {
        console.log(resp);
      }
    })
    .catch(err => console.log(err));
}

function copyStudentIdToClipboard(group, node) {
  navigator.clipboard
    .writeText(group.studentId)
    .then(() => showCopyBubble(node));
}

export function goToAssignment(
  group: { studentId: string, studentIdNeeded: boolean, name: string },
  assignment: { link: string },
) {
  if (!group.studentIdNeeded || group.studentId !== "") {
    window.location = assignment.link;
  } else {
    toggleStudentIdNeededView(group);
  }
}

export function modifyTos() {
  const url = model.urls.tosModify + "?next=" + window.location.href;
  window.location.href = url;
}

export function toggleJoinGroup() {
  model.joiningGroup = !model.joiningGroup;
  joinGroupView();
}

export function handleJoinGroupLinkInput(event) {
  if (event.key === "Enter") {
    joinGroup();
  } else {
    if (event.currentTarget.value) {
      joinGroupErrorView("", false);
    }
    verifyJoinGroupDisabledStatus();
  }
}

export function joinGroup() {
  const url = model.urls.joinGroup;
  const input = document.querySelector("#student-add-group--box input");
  const select = document.querySelector("#student-add-group--box select");

  let data;
  if (input.value) {
    data = {
      username: model.student.username,
      group_link: input.value,
    };
  } else if (model.groups.some(group => !group.memberOf)) {
    data = {
      username: model.student.username,
      group_name: select.value,
    };
  } else {
    joinGroupErrorView("A URL is needed.", true);
    return;
  }

  const req = buildReq(data, "post");
  fetch(url, req)
    .then(resp => resp.json())
    .then(function(group) {
      input.value = "";
      if (model.groups.some(g => g.name === group.name)) {
        model.groups.filter(g => g.name === group.name)[0].memberOf =
          group.member_of;
      } else {
        model.groups.push({
          name: group.name,
          title: group.title,
          notifications: group.notifications,
          memberOf: group.member_of,
          assignments: group.assignments.map(assignment => ({
            title: assignment.title,
            dueDate: new Date(assignment.due_date),
            link: assignment.link,
            results: {
              n: assignment.results.n,
              grade: assignment.results.grade,
            },
            done: assignment.done,
            almostExpired: assignment.almost_expired,
          })),
          studentId: group.student_id,
          studentIdNeeded: group.student_id_needed,
        });
      }
      toggleJoinGroup();
      groupsView();
    })
    .catch(function(err) {
      joinGroupErrorView("There is no group with that link.", true);
    });
}

/********/
/* view */
/********/

function view(groupStudentId) {
  identityView();
  groupsView(groupStudentId);
  joinGroupView();
}

function identityView() {
  const emailSpan = document.getElementById("student-email");
  emailSpan.textContent = model.student.email;

  const memberSinceSpan = document.getElementById("student-member-since");
  memberSinceSpan.textContent = model.student.memberSince.toLocaleString(
    "en-ca",
    {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    },
  );

  const tosSharingIcon = document.getElementById("student-tos-sharing--icon");
  const tosSharingSpan = document.getElementById(
    "student-tos-sharing--sharing",
  );
  if (model.student.tos.sharing) {
    tosSharingIcon.textContent = "check";
    tosSharingSpan.textContent = model.translations.sharing;
  } else {
    tosSharingIcon.textContent = "clear";
    tosSharingSpan.textContent = model.translations.notSharing;
  }

  const tosSignedOnSpan = document.getElementById("student-tos-signed-on");
  tosSignedOnSpan.textContent = model.student.tos.signedOn.toLocaleString(
    "en-ca",
    {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    },
  );
}

function joinGroupView() {
  const box = document.getElementById("student-add-group--box");
  const input = document.querySelector("#student-add-group--box input");
  if (model.joiningGroup) {
    joinGroupsSelectView();
    box.style.display = "flex";
  } else {
    box.style.display = "none";
    input.value = "";
  }
  joinGroupErrorView("", false);
}

function joinGroupErrorView(msg: string, show: boolean) {
  const error = document.getElementById("student-add-group__error");
  const input = document.querySelector("#student-add-group--box input");
  error.textContent = msg;
  if (show) {
    error.removeAttribute("hidden");
    input.classList.add("input--error");
  } else {
    error.setAttribute("hidden", "");
    input.classList.remove("input--error");
  }
}

function joinGroupsSelectView() {
  const groupsSelect = document.getElementById("student-old-groups");
  clear(groupsSelect);
  const oldGroups = model.groups.filter(group => !group.memberOf);
  if (oldGroups.length) {
    oldGroups.map(group =>
      groupsSelect.appendChild(joinGroupSelectView(group)),
    );
    groupsSelect.style.display = "inline-block";
    verifyJoinGroupDisabledStatus();
  } else {
    groupsSelect.style.display = "none";
  }
}

function joinGroupSelectView(group) {
  const option = document.createElement("option");
  option.value = group.name;
  option.textContent = group.title;
  return option;
}

function verifyJoinGroupDisabledStatus() {
  const input = document.querySelector("#student-add-group--box input");
  const select = document.querySelector("#student-add-group--box select");

  if (input.value) {
    select.disabled = true;
  } else {
    select.disabled = false;
  }
}

function groupsView(groupStudentId: string = "") {
  const groups = document.getElementById("student-groups");
  clear(groups);
  model.groups
    .filter(group => group.memberOf)
    .map(group => groups.appendChild(groupView(group)));
  if (groupStudentId) {
    for (let i = 0; i < model.groups.length; i++) {
      if (model.groups[i].name == groupStudentId) {
        toggleStudentIdNeededView(model.groups[i]);
        break;
      }
    }
  }
}

function groupView(group) {
  const div = document.createElement("div");
  div.classList.add("student-group");
  div.setAttribute("data-group", group.name);

  div.appendChild(groupTitleView(group));
  div.appendChild(groupAssignmentsView(group));

  return div;
}

function groupTitleView(group) {
  const div = document.createElement("div");
  div.classList.add("student-group--title");

  if (group.studentIdNeeded) {
    div.appendChild(groupTitleIdView(group));
  }

  const title = document.createElement("h3");
  title.textContent = group.title;
  div.appendChild(title);

  const icons = document.createElement("div");
  icons.classList.add("student-group--icons");
  div.appendChild(icons);

  if (group.connectedCourseUrl) {
    const courseButtonContainer = document.createElement("div");
    courseButtonContainer.classList.add("student-group--course");
    icons.appendChild(courseButtonContainer);

    const courseButton = document.createElement("i");
    courseButton.classList.add("material-icons", "md-28");
    courseButton.title = model.translations.courseFlowButton;
    courseButton.addEventListener(
      "click",
      () => (window.location.href = group.connectedCourseUrl),
    );
    courseButton.classList.add("course-flow-button");
    courseButton.textContent = "calendar_today";
    courseButtonContainer.appendChild(courseButton);
  }

  const reviewButtonContainer = document.createElement("div");
  reviewButtonContainer.classList.add("student-group--course");
  icons.appendChild(reviewButtonContainer);

  const reviewButton = document.createElement("i");
  reviewButton.classList.add("material-icons", "md-28");
  reviewButton.title = model.translations.groupReviewButton;
  reviewButton.addEventListener(
    "click",
    () => (window.location.href = group.groupReviewUrl),
  );
  reviewButton.classList.add("group-review-button");
  reviewButton.textContent = "chrome_reader_mode";
  reviewButtonContainer.appendChild(reviewButton);

  const notifications = document.createElement("div");
  notifications.classList.add("student-group--notifications");
  icons.appendChild(notifications);

  const bell = document.createElement("i");
  bell.classList.add("material-icons", "md-28");
  bell.title = model.translations.notificationsBell;
  bell.addEventListener("click", () => toggleGroupNotifications(group, bell));
  if (group.notifications) {
    bell.textContent = "notifications";
  } else {
    bell.textContent = "notifications_off";
    bell.classList.add("student-group--notifications__disabled");
  }
  notifications.appendChild(bell);

  icons.appendChild(leaveGroupView(group, div));

  return div;
}

function groupTitleIdView(group) {
  const div = document.createElement("div");
  div.classList.add("student-group--id");

  const copyIcon = document.createElement("i");
  copyIcon.classList.add("material-icons", "md-28", "student-group--id__copy");
  copyIcon.style.display = "flex";
  copyIcon.textContent = "file_copy";
  copyIcon.addEventListener("click", () =>
    copyStudentIdToClipboard(group, div),
  );
  div.appendChild(copyIcon);

  const studentId = document.createElement("span");
  studentId.classList.add("student-group--id__id");
  studentId.style.display = "inline-block";
  studentId.textContent = group.studentId;
  studentId.title = model.translations.studentId;
  studentId.addEventListener("click", () => editStudentId(group, div));
  div.appendChild(studentId);

  const input = document.createElement("input");
  input.classList.add("student-group--id__input");
  input.value = group.schoolId;
  input.style.display = "none";
  input.addEventListener("keydown", event =>
    handleStudentIdKeyDown(event.key, group, div),
  );
  div.appendChild(input);

  const editIcon = document.createElement("i");
  editIcon.classList.add("material-icons", "md-28", "student-group--id__edit");
  editIcon.style.display = "flex";
  editIcon.textContent = "edit";
  editIcon.title = model.translations.editStudentId;
  editIcon.addEventListener("click", () => editStudentId(group, div));
  div.appendChild(editIcon);

  const confirmIcon = document.createElement("i");
  confirmIcon.classList.add(
    "material-icons",
    "md-28",
    "student-group--id__confirm",
  );
  confirmIcon.style.display = "none";
  confirmIcon.textContent = "check";
  confirmIcon.addEventListener("click", () => saveStudentId(group, div));
  div.appendChild(confirmIcon);

  const cancelIcon = document.createElement("i");
  cancelIcon.classList.add(
    "material-icons",
    "md-28",
    "student-group--id__cancel",
  );
  cancelIcon.style.display = "none";
  cancelIcon.textContent = "close";
  cancelIcon.addEventListener("click", () => stopEditStudentId(group, div));
  div.appendChild(cancelIcon);

  return div;
}

function groupAssignmentsView(group) {
  const div = document.createElement("div");
  div.classList.add("student-group--assignments");
  if (group.assignments.length) {
    const ul = document.createElement("ul");
    group.assignments.map(assignment =>
      ul.appendChild(groupAssignmentView(assignment, group)),
    );
    div.appendChild(ul);
  } else {
    const span = document.createElement("span");
    span.classList.add("student-group--no-assignments");
    span.textContent = model.translations.noAssignments;
    div.appendChild(span);
  }
  return div;
}

function groupAssignmentView(assignment, group) {
  const a = document.createElement("a");
  a.href = assignment.link;

  const li = document.createElement("li");
  li.classList.add("student-group--assignment");
  if (assignment.done) {
    li.classList.add("student-group--assignment-complete");
  }
  li.addEventListener("click", (event: MouseEvent) =>
    goToAssignment(group, assignment),
  );

  const almostExpiredMin = new Date(assignment.dueDate);
  almostExpiredMin.setDate(
    almostExpiredMin.getDate() - model.expiryBlinkingDelay,
  );

  const iconSpan = document.createElement("span");
  iconSpan.classList.add("student-group--assignment-icon");
  li.appendChild(iconSpan);
  const icon = document.createElement("i");
  icon.classList.add("material-icons", "md-28");
  if (assignment.done) {
    iconSpan.title = model.translations.goToAssignment;
    icon.textContent = "assignment_turned_in";
  } else if (assignment.dueDate <= new Date(Date.now())) {
    iconSpan.title = model.translations.assignmentExpired;
    icon.textContent = "assignment_late";
  } else if (almostExpiredMin <= new Date(Date.now())) {
    iconSpan.title = model.translations.assignmentAboutToExpire;
    icon.textContent = "assignment_late";
  } else {
    iconSpan.title = model.translations.goToAssignment;
    icon.textContent = "assignment";
  }
  iconSpan.appendChild(icon);

  const gradeSpan = document.createElement("span");
  gradeSpan.classList.add("student-group--assignment-questions");
  gradeSpan.title = model.translations.grade;
  li.appendChild(gradeSpan);
  const grade = document.createElement("span");
  grade.textContent = assignment.results.grade;
  gradeSpan.appendChild(grade);
  const slash = document.createElement("span");
  slash.textContent = "/";
  gradeSpan.appendChild(slash);
  const n = document.createElement("span");
  n.textContent = assignment.results.n;
  gradeSpan.appendChild(n);

  const title = document.createElement("span");
  title.classList.add("student-group--assignment-title");
  title.title = model.translations.goToAssignment;
  title.textContent = assignment.title;
  li.appendChild(title);

  const date = document.createElement("span");
  date.classList.add("student-group--assignment-date");
  if (assignment.done) {
    date.removeAttribute("title");
    date.textContent = model.translations.completed;
  } else if (assignment.dueDate <= new Date(Date.now())) {
    date.title = model.translations.assignmentExpired;
    date.textContent = model.translations.expired;
  } else {
    date.title =
      model.translations.dueOn +
      " " +
      assignment.dueDate.toLocaleString("en-ca", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    const dateIcon = document.createElement("i");
    dateIcon.classList.add("material-icons", "md-18");
    dateIcon.textContent = "access_time";
    date.appendChild(dateIcon);
    const remainingTimeSpan = document.createElement("span");
    remainingTimeSpan.textContent = timeuntil(
      assignment.dueDate,
      new Date(Date.now()),
    );
    date.appendChild(remainingTimeSpan);
    if (almostExpiredMin <= new Date(Date.now())) {
      dateIcon.classList.add("blinking");
    }
  }
  li.appendChild(date);
  return li;
}

function leaveGroupView(group, groupNode) {
  const div = document.createElement("div");
  div.classList.add("student-group--remove");
  div.title = model.translations.leaveGroupTitle;

  const icon = document.createElement("i");
  icon.classList.add("material-icons", "md-28");
  icon.addEventListener("click", () => toggleLeaveGroup(groupNode));
  icon.textContent = "remove_circle_outline";
  div.appendChild(icon);

  const box = document.createElement("div");
  box.classList.add("student-group--remove-confirmation-box");
  box.style.display = "none";
  box.addEventListener("click", function(event: MouseEvent) {
    event.stopPropagation;
    toggleLeaveGroup(groupNode);
  });
  div.appendChild(box);

  const boxDiv = document.createElement("div");
  boxDiv.addEventListener("click", (event: MouseEvent) =>
    event.stopPropagation(),
  );
  box.appendChild(boxDiv);

  const title = document.createElement("h3");
  title.textContent = model.translations.leaveGroupTitle + " " + group.title;
  boxDiv.appendChild(title);

  const text = document.createElement("p");
  text.textContent = model.translations.leaveGroupText;
  boxDiv.appendChild(text);

  const question = document.createElement("p");
  question.textContent = model.translations.leaveGroupQuestion;
  boxDiv.appendChild(question);

  const leave = document.createElement("button");
  leave.classList.add("mdc-button", "mdc-button--unelevated");
  leave.addEventListener("click", () => leaveGroup(group, groupNode));
  leave.textContent = model.translations.leave;
  boxDiv.appendChild(leave);

  const cancel = document.createElement("button");
  cancel.classList.add("mdc-button");
  cancel.addEventListener("click", () => toggleLeaveGroup(groupNode));
  cancel.textContent = model.translations.cancel;
  boxDiv.appendChild(cancel);

  return div;
}

function editStudentId(group, node) {
  const span = node.querySelector(".student-group--id__id");
  const input = node.querySelector(".student-group--id__input");
  const copyBtn = node.querySelector(".student-group--id__copy");
  const editBtn = node.querySelector(".student-group--id__edit");
  const confirmBtn = node.querySelector(".student-group--id__confirm");
  const cancelBtn = node.querySelector(".student-group--id__cancel");

  input.value = group.studentId;

  span.style.display = "none";
  copyBtn.style.display = "none";
  editBtn.style.display = "none";
  input.style.display = "inline-block";
  confirmBtn.style.display = "flex";
  cancelBtn.style.display = "flex";

  input.focus();
  toggleStudentIdNeededView(group);
}

function stopEditStudentId(group, node) {
  const span = node.querySelector("span");
  const input = node.querySelector("input");
  const copyBtn = node.querySelector(".student-group--id__copy");
  const editBtn = node.querySelector(".student-group--id__edit");
  const confirmBtn = node.querySelector(".student-group--id__confirm");
  const cancelBtn = node.querySelector(".student-group--id__cancel");

  span.textContent = group.studentId;

  span.style.display = "inline-block";
  copyBtn.style.display = "flex";
  editBtn.style.display = "flex";
  input.style.display = "none";
  confirmBtn.style.display = "none";
  cancelBtn.style.display = "none";
}

function toggleStudentIdNeededView(group) {
  const node = document.querySelector(
    `.student-group[data-group='${group.name}'] .student-group--id`,
  );
  if (
    node.querySelector(".student-group--id__input")?.style.display === "none"
  ) {
    const alert = document.createElement("div");
    alert.classList.add("student-group--id__alert");
    alert.textContent = model.translations.studentIdNeeded;
    node.appendChild(alert);
    alert.scrollIntoView(true);
  } else {
    const alert = node.querySelector(".student-group--id__alert");
    alert?.parentNode.removeChild(alert);
  }
}

function toggleLeaveGroup(node) {
  const box = node.querySelector(".student-group--remove-confirmation-box");
  if (box.style.display == "none") {
    box.style.display = "flex";
  } else {
    box.style.display = "none";
  }
}

function showCopyBubble(node) {
  const bubble = document.createElement("div");
  bubble.classList.add("bubble");
  bubble.textContent = "Copied to clipboard!";
  node.appendChild(bubble);

  setTimeout(() => node.removeChild(bubble), 600);
}

/*************/
/* listeners */
/*************/

function initListeners() {
  addLinkListeners();
  addJoinGroupListeners();
}

function addLinkListeners() {
  document
    .getElementById("edit-user-btn")
    .addEventListener("click", function() {
      edit_user();
    });
  document
    .getElementById("modify-tos-btn")
    .addEventListener("click", function() {
      modifyTos();
    });
}

function addJoinGroupListeners() {
  document
    .querySelector("#student-add-group .admin-link")
    .addEventListener("click", function() {
      toggleJoinGroup();
    });
  document
    .getElementById("student-add-group--box")
    .addEventListener("click", function() {
      event.stopPropagation;
    });
  document
    .querySelector("#student-add-group--box > div")
    .addEventListener("click", function() {
      event.stopPropagation;
    });
  document
    .querySelector("#student-add-group--box input[name='new-group']")
    .addEventListener("keyup", function(event) {
      handleJoinGroupLinkInput(event);
    });
  document
    .getElementById("join-group-btn")
    .addEventListener("click", function() {
      joinGroup();
    });
  document
    .getElementById("cancel-join-group-btn")
    .addEventListener("click", function() {
      toggleJoinGroup();
    });
}

/*********/
/* utils */
/*********/

function timeuntil(date1, date2) {
  let diff = date1 - date2;
  const diffDays = Math.floor(diff / 1000 / 60 / 60 / 24);
  diff = diff - diffDays * 24 * 60 * 60 * 1000;
  const diffHours = Math.floor(diff / 1000 / 60 / 60);
  diff = diff - diffHours * 60 * 60 * 1000;
  const diffMinutes = Math.floor(diff / 1000 / 60);
  let diff_ = "";
  if (diffDays > 1) {
    diff_ = diff_ + parseInt(diffDays) + " " + model.translations.days + ", ";
  } else if (diffDays === 1) {
    diff_ = diff_ + parseInt(diffDays) + " " + model.translations.day + ", ";
  }
  if (diffHours === 1) {
    diff_ = diff_ + parseInt(diffHours) + " " + model.translations.hour + ", ";
  } else if (diffHours > 1 || diffDays) {
    diff_ =
      diff_ + parseInt(diffHours) + " " + model.translations.hours + ", ";
  }
  if (diffMinutes === 1) {
    diff_ = diff_ + parseInt(diffMinutes) + " " + model.translations.minute;
  } else {
    diff_ = diff_ + parseInt(diffMinutes) + " " + model.translations.minutes;
  }
  return diff_;
}

/********/
/* init */
/********/

export function initStudentPage(data, groupStudentId = "") {
  initModel(data);
  view(groupStudentId);
  initListeners();
}
