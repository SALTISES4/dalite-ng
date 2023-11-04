export function initForm() {
  const allRationaleInputs = Array.from(
    document.querySelectorAll(".rationale-text-container md-radio"),
  ).reduce((acc, curr) => {
    acc.push(
      ...Array.from(curr.shadowRoot?.querySelectorAll("input[type=radio]")),
    );
    return acc;
  }, []);

  const secondAnswerChoices = document.querySelectorAll(
    "input[type=radio][name=second_answer_choice]",
  );

  // Clear all rationale selections if the user changes choice
  secondAnswerChoices.forEach((el) => {
    el.addEventListener("change", function () {
      const parent = el.closest(".rationale");
      console.info(parent);
      allRationaleInputs.forEach((el) => {
        console.info(el.getRootNode().host.closest(".rationale"));
        if (el.getRootNode().host.closest(".rationale") != parent) {
          el.getRootNode().host.checked = false;
        }
      });
    });
  });

  // Select the right parent option
  allRationaleInputs.forEach((el) => {
    el.addEventListener("click", () => {
      // Search ancestors for closest .rationale and then select correct child
      const choiceElement = el
        .getRootNode()
        .host.closest(".rationale")
        ?.querySelector(
          "input[type=radio][name=second_answer_choice]",
        ) as HTMLElement;
      if (choiceElement) {
        choiceElement.click();
      }
    });
  });
}
