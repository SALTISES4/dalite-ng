import { buildReq } from "../../ajax.js";
import { clear } from "../../utils.js";

/*********/
/* model */
/*********/

let model;

function initModel(data) {
  model = {
    notificationsOpen: false,
    notifications: data.notifications,
    urls: {
      studentPage: data.urls.student_page,
      removeNotification: data.urls.remove_notification,
      removeNotifications: data.urls.remove_notifications,
    },
  };
}

/**********/
/* update */
/**********/

function toggleNotifications() {
  const header = document.querySelector(".notifications");
  document.querySelectorAll(".header--togglable > *").forEach(header_ => {
    if (header_ != header && header_.hasAttribute("open")) {
      if (header_.shadowRoot) {
        header_.shadowRoot
          .querySelector(".header__icon")
          .dispatchEvent(new Event("click"));
      } else {
        header_
          .querySelector(".header__icon")
          .dispatchEvent(new Event("click"));
      }
    }
  });
  model.notificationsOpen = !model.notificationsOpen;
  notificationsView();
}

function markNotificationRead(notification) {
  const url = model.urls.removeNotification;
  const data = {
    notification_pk: notification.pk,
  };
  const req = buildReq(data, "post");
  fetch(url, req)
    .then(resp => resp.text())
    .then(groupName => {
      if (groupName) {
        window.location =
          model.urls.studentPage + "?group-student-id-needed=" + groupName;
      } else if (notification.link) {
        window.location = notification.link;
      } else {
        model.notifications.splice(
          model.notifications.indexOf(notification),
          1,
        );
        notificationsView();
      }
    })
    .catch(function(err) {
      console.log(err);
    });
}

function markAllNotificationsRead() {
  const url = model.urls.removeNotifications;
  const req = buildReq({}, "post");
  fetch(url, req)
    .then(function(resp) {
      if (resp.ok) {
        model.notifications = [];
        notificationsView();
      }
    })
    .catch(function(err) {
      console.log(err);
    });
}

/********/
/* view */
/********/

function view() {
  notificationsView();
}

function notificationsView() {
  const notifications = document.querySelector(".notifications");
  const badge = notifications.querySelector(".notifications__icon__badge");
  const notificationsList = notifications.querySelector(
    ".notifications__notifications",
  );

  if (model.notifications.length) {
    badge.textContent = model.notifications.length;
    badge.style.display = "flex";
  } else {
    badge.textContent = "";
    badge.style.display = "none";
  }

  clear(notificationsList);
  if (model.notifications.length) {
    model.notifications.map(function(notification) {
      notificationsList.appendChild(notificationView(notification));
    });
  } else {
    notificationsList.appendChild(noNotificationView());
  }

  if (model.notificationsOpen) {
    notifications.setAttribute("open", "");
    notifications.classList.add("notifications--open");
  } else {
    notifications.removeAttribute("open");
    notifications.classList.remove("notifications--open");
  }
}

function notificationView(notification) {
  const div = document.createElement("div");
  div.classList.add("notification");
  div.textContent = notification.text;
  div.addEventListener("click", () => markNotificationRead(notification));
  return div;
}

function noNotificationView() {
  const div = document.createElement("div");
  div.classList.add("notifications__no-new");
  div.textContent = "No new notifications";
  return div;
}

/*************/
/* listeners */
/*************/

function initListeners() {
  addNotificationsOpenListener();
  addAllNotificationsReadListener();
}

function addNotificationsOpenListener() {
  document
    .querySelector(".notifications")
    ?.addEventListener("click", function(event) {
      event.stopPropagation();
    });
  document
    .querySelector(".notifications__icon")
    ?.addEventListener("click", function(event) {
      toggleNotifications();
    });
  document.body.addEventListener("click", function(event) {
    if (model.notificationsOpen) {
      toggleNotifications();
    }
  });
}

function addAllNotificationsReadListener() {
  document
    .querySelector(".notifications__read-all-btn")
    ?.addEventListener("click", markAllNotificationsRead);
}

/********/
/* init */
/********/

export function init(url) {
  if (document.querySelector(".notifications")) {
    const req = buildReq(null, "get");
    fetch(url, req)
      .then(resp => resp.json())
      .then(function(data) {
        initModel(data);
        initListeners();
        view();
      })
      .catch(err => console.log(err));
  }
}
