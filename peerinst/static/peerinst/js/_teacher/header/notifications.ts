import { clear, createSvg } from "../../utils";

/*********/

/* model */

/*********/
export type Notification = {
  text: string;
  inProgress: boolean;
  error: boolean;
  onClick: () => Promise<void>;
  onCloseClick: () => Promise<void>;
};
let model: {
  notificationsOpen: boolean;
  notifications: Array<Notification>;
};

function initModel(): void {
  model = {
    notificationsOpen: false,
    notifications: []
  };
}

/**********/

/* update */

/**********/
function toggleNotifications(): void {
  const header = document.querySelector(".notifications");
  document.querySelectorAll(".header--togglable > *").forEach(header_ => {
    if (header_ != header && header_.hasAttribute("open")) {
      if (header_.shadowRoot) {
        header_.shadowRoot.querySelector(".header__icon").dispatchEvent(new Event("click"));
      } else {
        header_.querySelector(".header__icon").dispatchEvent(new Event("click"));
      }
    }
  });
  model.notificationsOpen = !model.notificationsOpen;
  notificationsView();
}

export function updateNotifications(notifications: Array<Notification>): void {
  model.notifications = notifications;
  notificationsView();
}

function clearAll(): void {
  model.notifications.forEach(notification => {
    notification.onCloseClick();
  });
}

/********/

/* view */

/********/
function view(): void {
  notificationsView();
}

function notificationsView(): void {
  const notifications = document.querySelector(".notifications");
  const badge = notifications?.querySelector(".notifications__icon__badge");
  const notificationsList = notifications?.querySelector(".notifications__notifications");

  if (!notifications || !badge || !notificationsList) {
    return;
  }

  const completedNotifications = model.notifications.filter(notification => !notification.inProgress);

  if (completedNotifications.length > 0) {
    badge.textContent = completedNotifications.length.toString();
    badge.style.display = "flex";
  } else {
    badge.textContent = "";
    badge.style.display = "none";
  }

  clear(notificationsList);

  if (model.notifications.length) {
    model.notifications.map(function (notification) {
      notificationsList.appendChild(notificationView(notification));
    });
    document.querySelector(".notifications__clear-all-btn").removeAttribute("hidden");
  } else {
    notificationsList.appendChild(noNotificationView());
    document.querySelector(".notifications__clear-all-btn").setAttribute("hidden", "");
  }

  if (model.notifications.some(notification => notification.inProgress)) {
    document.querySelector(".notifications__spinner")?.classList.add("notifications__spinner--loading");
  } else {
    document.querySelector(".notifications__spinner")?.classList.remove("notifications__spinner--loading");
  }

  if (model.notificationsOpen) {
    notifications.setAttribute("open", "");
    notifications.classList.add("notifications--open");
  } else {
    notifications.removeAttribute("open");
    notifications.classList.remove("notifications--open");
  }
}

function notificationView(notification: Notification): HTMLDivElement {
  const div = document.createElement("div");
  div.classList.add("notification");
  div.addEventListener("click", notification.onClick);

  if (notification.inProgress) {
    const spinner = document.createElement("loading-spinner");
    spinner.classList.add("notification__spinner");
    div.appendChild(spinner);
  } else {
    let icon;

    if (notification.error) {
      icon = createSvg("error");
      icon.classList.add("notification__icon--error");
    } else {
      div.classList.add("notification--completed");
      icon = createSvg("cloud_download");
    }

    icon.classList.add("notification__icon");
    div.appendChild(icon);
  }

  const description = document.createElement("span");
  description.classList.add("notification__description");
  description.innerHTML = notification.text;
  div.appendChild(description);
  const remove = createSvg("close");
  remove.classList.add("notification__close");
  remove.addEventListener("click", notification.onCloseClick);
  div.appendChild(remove);
  return div;
}

function noNotificationView(): HTMLDivElement {
  const div = document.createElement("div");
  div.textContent = "No new notifications";
  return div;
}

/*************/

/* listeners */

/*************/
function initEventListeners(): void {
  addNotificationsOpenListener();
  addClearAllListener();
}

function addNotificationsOpenListener(): void {
  document.querySelector(".notifications")?.addEventListener("click", function (event: MouseEvent) {
    event.stopPropagation();
  });
  document.querySelector(".notifications__icon")?.addEventListener("click", function (event: MouseEvent) {
    toggleNotifications();
  });
  document.body?.addEventListener("click", function (event: MouseEvent) {
    if (model.notificationsOpen) {
      event.stopPropagation();
      toggleNotifications();
    }
  });
}

function addClearAllListener(): void {
  document.querySelector(".notifications__clear-all-btn")?.addEventListener("click", () => clearAll());
}

/********/

/* init */

/********/
export function init(): void {
  initModel();
  view();
  initEventListeners();
}