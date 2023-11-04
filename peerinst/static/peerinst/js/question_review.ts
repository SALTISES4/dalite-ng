export function initForm() {
  const allRationaleInputs = Array.from(
    document.querySelectorAll(".rationale-text-container md-radio"),
  ).reduce((acc, curr) => {
    acc.push(
      ...(Array.from(
        (curr.shadowRoot as ShadowRoot).querySelectorAll("input[type=radio]"),
      ) as HTMLInputElement[]),
    );
    return acc;
  }, [] as Element[]);

  const secondAnswerChoices = document.querySelectorAll(
    "input[type=radio][name=second_answer_choice]",
  );

  // Clear all rationale selections if the user changes choice
  secondAnswerChoices.forEach((el) => {
    el.addEventListener("change", function () {
      const parent = el.closest(".rationale");
      allRationaleInputs.forEach((el) => {
        const host = (el.getRootNode() as ShadowRoot).host;
        if (host.closest(".rationale") != parent) {
          (host as HTMLInputElement).checked = false;
        }
      });
    });
  });

  // Select the right parent option
  allRationaleInputs.forEach((el) => {
    el.addEventListener("click", () => {
      // Search ancestors for closest .rationale and then select correct child
      const choiceElement = (el.getRootNode() as ShadowRoot).host
        .closest(".rationale")
        ?.querySelector(
          "input[type=radio][name=second_answer_choice]",
        ) as HTMLElement;
      if (choiceElement) {
        choiceElement.click();
      }
    });
  });
}
