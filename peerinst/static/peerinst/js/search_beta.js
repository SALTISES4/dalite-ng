import { get } from "./_ajax/ajax.js";
import { Component, h } from "preact";
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

export class QuestionCard extends Component {
  state = {
    analyticsOpen: false,
  };

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
      return <div />;
    }
    return (
      <div>
        <Typography
          use="body1"
          tag="div"
          theme="text-secondary-on-background"
          // This field is bleached and safe
          // eslint-disable-next-line
          dangerouslySetInnerHTML={{ __html: this.props.question.text }}
          style={{ marginTop: 10 }}
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
    meta: {},
    searching: false,
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
            meta: data.meta,
            questions: data.results,
            searching: false,
          },
          () => console.debug(this.state.questions, this.state.meta),
        );
      } catch (error) {
        // Snackbar
        console.debug(error);
      }
    } else {
      this.setState({ questions: [], meta: {} });
    }
  };

  results = () => {
    if (this.state.searching) {
      return <CircularProgress class="spinner" size="xlarge" />;
    }
    if (this.state.questions) {
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
                  this.setState({ query: "", questions: [], meta: {} })
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
        {this.results()}
      </div>
    );
  }
}
