import { MDCSnackbar } from "@material/snackbar";

export function init(
  assignUrl,
  unassignUrl,
  assignTrans,
  unassignTrans,
  assignedTo,
  unassignedFrom,
  error,
  groupUrl,
) {
  const snackbar = new MDCSnackbar(document.querySelector(".mdc-snackbar"));

  $.ajaxSetup({
    beforeSend: function(xhr, settings) {
      if (!bundle.csrfSafeMethod(settings.type) && !this.crossDomain) {
        xhr.setRequestHeader("X-CSRFToken", bundle.getCsrfToken());
      }
    },
  });

  function clickAssign(el) {
    const posting = $.post(assignUrl, {
      pk: el.getAttribute("id_pk"),
      ppk: el.getAttribute("id_ppk"),
    });
    posting.done(function(data) {
      console.info(data);
      document.getElementById(
        el.getAttribute("id_pk"),
      ).innerHTML = unassignTrans;
      document.getElementById(el.getAttribute("id_pk")).classList.add("added");
      document
        .getElementById(el.getAttribute("id_pk"))
        .classList.remove("removed");
      const dataObjAssigned = {
        message: assignedTo + el.getAttribute("name"),
      };
      snackbar.show(dataObjAssigned);
    });
    posting.fail(function(data) {
      console.info(data);
      const err = {
        message: error,
      };
      snackbar.show(err);
    });
  }

  function clickUnassign(el) {
    const posting = $.post(unassignUrl, {
      pk: el.getAttribute("id_pk"),
      ppk: el.getAttribute("id_ppk"),
    });
    posting.done(function(data) {
      console.info(data);
      document.getElementById(
        el.getAttribute("id_pk"),
      ).innerHTML = assignTrans;
      document
        .getElementById(el.getAttribute("id_pk"))
        .classList.remove("added");
      document
        .getElementById(el.getAttribute("id_pk"))
        .classList.add("removed");
      const dataObjUnassigned = {
        message: unassignedFrom + el.getAttribute("name"),
      };
      snackbar.show(dataObjUnassigned);
    });
    posting.fail(function(data) {
      console.info(data);
      const err = {
        message: error,
      };
      snackbar.show(err);
    });
  }

  [].forEach.call(
    document.querySelectorAll(".collection-toggle-assign"),
    el => {
      el.addEventListener("click", () => {
        if (el.classList.contains("removed")) {
          clickAssign(el);
        } else {
          clickUnassign(el);
        }
      });
    },
  );

  [].forEach.call(document.querySelectorAll(".md-48"), el => {
    el.addEventListener("click", () => {
      const hash = el.getAttribute("id");
      window.location.assign(groupUrl.replace("0", hash));
    });
  });
}
