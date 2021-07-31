const transition = {
  duration: 600,
  direction: "right",
  easing: "easeInOutCubic",
};

export function init(url) {
  // Rating system
  $("#rationales .mdc-card").each((i, el) => {
    const id = el.getAttribute("data-id");
    let score;

    // Score
    $(el)
      .find(".star")
      .each((i, star) => {
        // Handle hover
        star.addEventListener("mouseover", () => {
          score = star.getAttribute("data-rank");
          $(".star").each((i, _star) => {
            if (_star.getAttribute("data-rank") <= score) {
              _star.innerHTML = "star";
            } else {
              _star.innerHTML = "star_border";
            }
          });
        });
        star.addEventListener("mouseout", () => {
          $(".star").each((i, _star) => {
            _star.innerHTML = "star_border";
          });
        });

        // Submit score
        $(star).one("click", () => {
          const posting = $.post(url, { id, score });
          posting.done((data) => {
            processResponse(data);
          });
        });
      });

    // Flag inappropriate
    $(el)
      .find(".flag")
      .each((i, flag) => {
        flag.addEventListener("mouseover", () => {
          $(".flag").each((i, _flag) => {
            _flag.innerHTML = "flag";
          });
        });
        flag.addEventListener("mouseout", () => {
          $(".flag").each((i, _flag) => {
            _flag.innerHTML = "outlined_flag";
          });
        });
        $(flag).one("click", () => {
          const posting = $.post(url, { id, score: 0 });
          posting.done((data) => {
            processResponse(data);
          });
        });
      });

    function processResponse(data) {
      $(el).toggle("fade", () => {
        $(el).remove();
        $("#rationales").append(data);
        $("#rationales .mdc-card").hide().toggle("slide", transition);
        init(url);
        // Refresh reputation score
        document
          .getElementsByTagName("teacher-reputation-header")[0]
          .setAttribute("stale", "");
      });
    }
  });
}
