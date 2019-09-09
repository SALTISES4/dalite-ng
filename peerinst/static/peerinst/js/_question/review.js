// @flow

/*********/
/* model */
/*********/

let model: {
  submitAllowed: boolean,
};

function initModel() {
  model = {
    submitAllowed: false,
  };
}

/**********/
/* update */
/**********/

function startSubmitAllowedTimer(seconds: number) {
  setInterval(allowSubmit, seconds * 1000);
}

function allowSubmit() {
  model.submitAllowed = true;
  submitButtonView();
}

/********/
/* view */
/********/

function view() {
  submitButtonView();
}

function submitButtonView() {
  if (model.submitAllowed) {
    // $FlowFixMe
    document.getElementById("answer-form").disabled = false;
  } else {
    // $FlowFixMe
    document.getElementById("answer-form").disabled = true;
  }
}

/********/
/* init */
/********/

export function init() {
  initModel();
  view();
  startSubmitAllowedTimer(5);
}
