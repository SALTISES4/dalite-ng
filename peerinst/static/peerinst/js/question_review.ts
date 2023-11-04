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
          // M3 doesn't update css when element unchecked via js
          el.parentNode.classList.remove("checked");
          (el as HTMLInputElement).checked = false;
        }
      });
    });
  });

  // Select the right parent option
  allRationaleInputs.forEach((el) => {
    el.addEventListener("click", () => {
      // M3 doesn't seem to update css if unchecked via the above
      el.parentNode.classList.add("checked");

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
