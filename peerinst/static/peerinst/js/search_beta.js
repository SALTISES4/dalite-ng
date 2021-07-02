import { get } from "./_ajax/ajax.js";
import { Component, createRef, h } from "preact";
import { triScale } from "./_theming/colours.js";
import { scaleThreshold } from "d3";

import {
  Card,
  CardPrimaryAction,
  CardActions,
  CardAction,
  CardActionIcons,
  CardActionButtons,
} from "@rmwc/card";
import { CircularProgress } from "@rmwc/circular-progress";
import {
  TextField,
  TextFieldIcon,
  TextFieldHelperText,
} from "@rmwc/textfield";
import { Typography } from "@rmwc/typography";

import "@rmwc/card/node_modules/@material/card/dist/mdc.card.css";
import "@rmwc/circular-progress/circular-progress.css";
import "@rmwc/icon-button/node_modules/@material/icon-button/dist/mdc.icon-button.min.css";
import "@rmwc/textfield/node_modules/@material/textfield/dist/mdc.textfield.css";
import "@rmwc/typography/node_modules/@material/typography/dist/mdc.typography.min.css";

triScale.reverse();

function Chip(props) {
  return (
    <div
      class={this.props.selected ? "selected chips" : "chips"}
      onClick={() => props.onClick(props.text)}
    >
      {props.text}
    </div>
  );
}

export class QuestionCard extends Component {
  state = {
    analyticsOpen: false,
  };

  ref = createRef();

  answerChoice = (ac) => {
    if (Object.prototype.hasOwnProperty.call(ac, "correct")) {
      if (ac.correct) {
        return <i class="check material-icons">check</i>;
      }
    }
  };

  answerChoices = () => {
    if (
      Object.prototype.hasOwnProperty.call(
        this.props.question,
        "answerchoice_set",
      )
    ) {
      return (
        <div class="question-answers">
          <ol type={this.props.question.answer_style == 0 ? "A" : "l"}>
            {this.props.question.answerchoice_set.map((ac, i) => {
              return (
                <Typography
                  key={i}
                  use="body1"
                  tag="li"
                  style={{ marginBottom: 2 }}
                >
                  <span
                    // This field is bleached and safe
                    // eslint-disable-next-line
                    dangerouslySetInnerHTML={{ __html: ac.text }}
                  />
                  {this.answerChoice(ac)}
                </Typography>
              );
            })}
          </ol>
        </div>
      );
    }
  };

  byline = () => {
    if (Object.prototype.hasOwnProperty.call(this.props.question, "user")) {
      return <span>by {this.props.question.user.username}</span>;
    }
  };

  category = () => {
    if (this.props.question.category) {
      return this.props.question.category.map((c) => c.title).join("; ");
    }
    return this.props.gettext("Uncategorized");
  };

  difficulty = () => {
    if (
      Object.prototype.hasOwnProperty.call(
        this.props.question.difficulty,
        "score",
      )
    ) {
      const colourScale = scaleThreshold(triScale).domain([0.25, 0.5]);
      const color = colourScale(this.props.question.difficulty.score);
      const opacity = "30";
      const label = this.state.analyticsOpen
        ? "close"
        : this.props.question.difficulty.label;
      return (
        <div
          style={{
            backgroundColor: color + opacity,
            borderColor: color,
            borderRadius: "50%",
            borderWidth: "thin",
            borderStyle: "solid",
            cursor: "pointer",
            fontSize: "x-small",
            height: 32,
            position: "absolute",
            right: 20,
            top: 20,
            width: 32,
          }}
          onClick={() =>
            this.setState({ analyticsOpen: !this.state.analyticsOpen })
          }
        >
          <div
            style={{
              color,
              fontFamily: this.state.analyticsOpen
                ? "Material Icons"
                : "inherit",
              fontSize: this.state.analyticsOpen ? 18 : "inherit",
              fontWeight: "bold",
              left: "50%",
              position: "absolute",
              top: "50%",
              transform: "translate(-50%, -50%)",
            }}
          >
            {label}
          </div>
        </div>
      );
    }
  };

  discipline = () => {
    if (this.props.question.discipline) {
      return this.props.question.discipline;
    }
    return this.props.gettext("Unlabelled");
  };

  image = () => {
    if (this.props.question.image || this.props.question.image_alt_text) {
      return (
        <Typography use="caption">
          <img
            class="question-image"
            src={this.props.staticURL.slice(0, -1) + this.props.question.image}
            alt={this.props.question.image_alt_text}
          />
        </Typography>
      );
    }
  };

  innerContent = () => {
    if (this.state.analyticsOpen) {
      const height = this.ref.current.getBoundingClientRect().height + 16;
      return (
        <div
          style={{ backgroundColor: "lightgrey", height, overflowY: "scroll" }}
        >
          [Analytics placeholder]
        </div>
      );
    }
    return (
      <div ref={this.ref}>
        <Typography
          use="body1"
          tag="div"
          theme="text-secondary-on-background"
          // This field is bleached and safe
          // eslint-disable-next-line
          dangerouslySetInnerHTML={{ __html: this.props.question.text }}
        />
        {this.image()}
        {this.video()}
        {this.answerChoices()}
      </div>
    );
  };

  video = () => {
    if (this.props.question.video_url) {
      return (
        <object
          class="question-image"
          width="640"
          height="390"
          data={this.props.question.video_url}
        />
      );
    }
  };

  render() {
    return (
      <Card class="question" style={{ position: "relative" }}>
        {this.difficulty()}
        <CardPrimaryAction>
          <div>
            <Typography
              class="title"
              use="headline6"
              tag="h2"
              // This field is bleached and safe
              // eslint-disable-next-line
              dangerouslySetInnerHTML={{ __html: this.props.question.title }}
            />
            <Typography
              use="caption"
              tag="div"
              theme="text-secondary-on-background"
              style={{ marginBottom: 10 }}
            >
              #{this.props.question.id} {this.byline()}
            </Typography>
            {this.innerContent()}
          </div>
        </CardPrimaryAction>
        <CardActions>
          <CardActionButtons>
            <Typography use="caption" tag="div">
              {this.props.gettext("Discipline")}:{" "}
              <span class="capitalize">{this.discipline()}</span>
            </Typography>
            <Typography use="caption" tag="div">
              {this.props.gettext("Categories")}:{" "}
              <span class="capitalize">{this.category()}</span>
            </Typography>
            <Typography use="caption" tag="div">
              {this.props.gettext("Student answers")}:{" "}
              {this.props.question.answer_count}
            </Typography>
          </CardActionButtons>
          <CardActionIcons>
            <CardAction
              theme="primary"
              onIcon="favorite"
              icon="favorite_border"
              title={this.props.gettext("Toggle favourite")}
            />
            <CardAction
              theme="primary"
              onIcon="flag"
              icon="outlined_flag"
              title={this.props.gettext("Flag question for removal")}
            />
            <CardAction
              theme="primary"
              icon="add"
              title={this.props.gettext("Add question to an assignment")}
            />
          </CardActionIcons>
        </CardActions>
      </Card>
    );
  }
}

export class SearchApp extends Component {
  state = {
    query: "",
    questions: [],
    categories: [],
    difficulties: [],
    disciplines: [],
    searching: false,
    selectedCategory: "",
    selectedDiscipline: "",
  };

  handleSubmit = async () => {
    const queryString = new URLSearchParams();
    queryString.append("search_string", this.state.query);
    const url = new URL(this.props.url, window.location.origin);
    url.search = queryString;

    if (this.state.query.length > 2) {
      try {
        this.setState({ searching: true });
        const data = await get(url);
        console.debug(data);
        this.setState(
          {
            categories: data.meta.categories,
            difficulties: data.meta.difficulties,
            disciplines: data.meta.disciplines,
            questions: data.results,
            searching: false,
          },
          () => console.debug(this.state.questions, this.state.disciplines),
        );
      } catch (error) {
        // Snackbar
        console.debug(error);
      }
    } else {
      this.setState({ questions: [], disciplines: [] });
    }
  };

  categoryChips = () => {
    if (this.state.categories.length > 0) {
      return (
        <div class="chip-container">
          <Typography
            use="caption"
            tag="div"
            style={{ fontWeight: "bold", paddingLeft: 3 }}
          >
            {this.props.gettext("Categories")}
          </Typography>
          {this.state.categories.map((c, i) => {
            if (c.length > 0) {
              return (
                <Chip
                  selected={this.state.selectedCategory == c}
                  text={c}
                  key={i}
                  onClick={() => {
                    this.setState(
                      {
                        selectedCategory: c,
                        query: `category__title::${c.replaceAll(" ", "_")} ${
                          this.state.query
                        }`,
                      },
                      this.handleSubmit,
                    );
                  }}
                />
              );
            }
          })}
          <i
            class="material-icons"
            onClick={() => {
              this.setState(
                {
                  selectedCategory: "",
                  query: this.state.query
                    .replace(/category__title::\w+/gi, "")
                    .replace(/\s+/g, " ")
                    .trim(),
                },
                this.handleSubmit,
              );
            }}
            style={{
              cursor: "pointer",
              display: this.state.selectedCategory ? "inline" : "none",
              fontSize: 18,
              verticalAlign: "middle",
            }}
          >
            close
          </i>
        </div>
      );
    }
  };

  difficultyChips = () => {
    if (this.state.difficulties.length > 0) {
      return (
        <div class="chip-container">
          <Typography
            use="caption"
            tag="div"
            style={{ fontWeight: "bold", paddingLeft: 3 }}
          >
            {this.props.gettext("Difficulty levels")}
          </Typography>
          {this.state.difficulties.map((d, i) => {
            if (d.length > 0) {
              return (
                <Chip
                  selected={this.state.selectedDifficulty == d}
                  text={d}
                  key={i}
                  onClick={() => {
                    if (this.state.selectedDifficulty) {
                      this.setState(
                        {
                          selectedDifficulty: "",
                          query: this.state.query
                            .replace(/difficulty.label::\w+/gi, "")
                            .replace(/\s+/g, " ")
                            .trim(),
                        },
                        this.handleSubmit,
                      );
                    } else {
                      this.setState(
                        {
                          selectedDifficulty: d,
                          query: `difficulty.label::${d.replaceAll(
                            " ",
                            "_",
                          )} ${this.state.query}`,
                        },
                        this.handleSubmit,
                      );
                    }
                  }}
                />
              );
            }
          })}
          <i
            class="material-icons"
            onClick={() => {
              this.setState(
                {
                  selectedDifficulty: "",
                  query: this.state.query
                    .replace(/difficulty.label::\w+/gi, "")
                    .replace(/\s+/g, " ")
                    .trim(),
                },
                this.handleSubmit,
              );
            }}
            style={{
              cursor: "pointer",
              display: this.state.selectedDifficulty ? "inline" : "none",
              fontSize: 18,
              verticalAlign: "middle",
            }}
          >
            close
          </i>
        </div>
      );
    }
  };

  disciplineChips = () => {
    if (this.state.disciplines.length > 0) {
      return (
        <div class="chip-container">
          <Typography
            use="caption"
            tag="div"
            style={{ fontWeight: "bold", paddingLeft: 3 }}
          >
            {this.props.gettext("Disciplines")}
          </Typography>
          {this.state.disciplines.map((d, i) => {
            if (d.length > 0) {
              return (
                <Chip
                  selected={this.state.selectedDiscipline == d}
                  text={d}
                  key={i}
                  onClick={() => {
                    if (this.state.selectedDiscipline) {
                      this.setState(
                        {
                          selectedDiscipline: "",
                          query: this.state.query
                            .replace(/discipline::\w+/gi, "")
                            .replace(/\s+/g, " ")
                            .trim(),
                        },
                        this.handleSubmit,
                      );
                    } else {
                      this.setState(
                        {
                          selectedDiscipline: d,
                          query: `discipline::${d.replaceAll(" ", "_")} ${
                            this.state.query
                          }`,
                        },
                        this.handleSubmit,
                      );
                    }
                  }}
                />
              );
            }
          })}
          <i
            class="material-icons"
            onClick={() => {
              this.setState(
                {
                  selectedDiscipline: "",
                  query: this.state.query
                    .replace(/discipline::\w+/gi, "")
                    .replace(/\s+/g, " ")
                    .trim(),
                },
                this.handleSubmit,
              );
            }}
            style={{
              cursor: "pointer",
              display: this.state.selectedDiscipline ? "inline" : "none",
              fontSize: 18,
              verticalAlign: "middle",
            }}
          >
            close
          </i>
        </div>
      );
    }
  };

  chips = () => {
    return (
      <div>
        {this.disciplineChips()}
        {this.categoryChips()}
        {this.difficultyChips()}
      </div>
    );
  };

  results = () => {
    if (this.state.searching) {
      return <CircularProgress class="spinner" size="xlarge" />;
    }
    if (this.state.questions.length > 0) {
      return (
        <div id="results" style={{ marginTop: 20 }}>
          {this.state.questions.map((question, i) => {
            return (
              <QuestionCard
                question={question}
                key={i}
                staticURL={this.props.staticURL}
                gettext={this.props.gettext}
              />
            );
          })}
        </div>
      );
    }
    if (this.state.questions.length == 0 && this.state.query.length >= 3) {
      return (
        <div>
          <h3>{this.props.gettext("No search results")}</h3>
          <p>
            {this.props.gettext(
              "Ugh... doesn't look like there are any questions that match your query.  May we suggest:",
            )}
          </p>
          <ol>
            <li>
              {this.props.gettext(
                "Try the search again, but with different keywords and/or fewer filters;",
              )}
            </li>
            <li>
              {this.props.gettext(
                "Create the question you are looking for by selecting 'Create question' from the menu.",
              )}
            </li>
          </ol>
        </div>
      );
    }
  };

  render() {
    return (
      <div>
        <div id="search-form" style={{ width: 500 }}>
          <TextField
            autofocus
            class="wide tight"
            outlined
            label={this.props.gettext("Type something...")}
            withLeadingIcon="search"
            withTrailingIcon={
              <TextFieldIcon
                style={
                  this.state.query ? { display: "block" } : { display: "none" }
                }
                tabIndex="0"
                icon="close"
                onClick={() =>
                  this.setState({
                    query: "",
                    questions: [],
                    categories: [],
                    difficulties: [],
                    disciplines: [],
                    selectedCategory: "",
                    selectedDiscipline: "",
                  })
                }
              />
            }
            onInput={(evt) => {
              this.setState({ query: evt.target.value }, this.handleSubmit);
            }}
            value={this.state.query}
          />
          <TextFieldHelperText persistent>
            {this.props.gettext(
              "You can search for keywords in question and answer texts, by username, by question id, by category, and by discipline.",
            )}
          </TextFieldHelperText>
        </div>
        {this.chips()}
        {this.results()}
      </div>
    );
  }
}
