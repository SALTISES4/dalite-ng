import { Component, Fragment, h } from "preact";
import { triScale } from "../_theming/colours.js";
import { scaleThreshold } from "d3";
import { Favourites } from "./providers.js";
import { PlotConfusionMatrix } from "../_assignment/analytics.js";
import { get, submitData } from "../_ajax/ajax.js";

import {
  Card,
  CardActions,
  CardAction,
  CardActionIcons,
  CardActionButtons,
} from "@rmwc/card";
import {
  Dialog,
  DialogActions,
  DialogButton,
  DialogContent,
  DialogTitle,
} from "@rmwc/dialog";
import { Icon } from "@rmwc/icon";
import { Select, SelectHelperText } from "@rmwc/select";
import { Typography } from "@rmwc/typography";

import "@rmwc/button/node_modules/@material/button/dist/mdc.button.min.css";
import "@rmwc/card/node_modules/@material/card/dist/mdc.card.css";
import "@rmwc/dialog/node_modules/@material/dialog/dist/mdc.dialog.min.css";
import "@rmwc/icon/icon.css";
import "@rmwc/icon-button/node_modules/@material/icon-button/dist/mdc.icon-button.min.css";
import "@rmwc/select/node_modules/@material/select/dist/mdc.select.min.css";
import "@rmwc/theme/node_modules/@material/theme/dist/mdc.theme.min.css";
import "@rmwc/typography/node_modules/@material/typography/dist/mdc.typography.min.css";

triScale.reverse();

export function QuestionDialog(props) {
  return (
    <Dialog open={props.open} onClose={props.onClose}>
      <DialogTitle>{props.question.title}</DialogTitle>
      <DialogContent>
        <div style={{ marginBottom: 16 }}>
          <Info
            text={this.props.gettext(
              `The distribution of first and second choices along with the
            statistics for each possible outcome are shown in the figure
            below.  The most convincing rationales submitted by students
            (i.e. most selected be peers) are also listed for each answer
            choice.`,
            )}
          />
        </div>
        <Typography
          use="body2"
          tag="p"
          theme="text-secondary-on-background"
          style={{ fontWeight: "bold" }}
        >
          {props.gettext("Distribution of answer choices")}
        </Typography>
        <div style={{ margin: "16px 0px" }}>
          <PlotConfusionMatrix
            _matrix={props.question.matrix}
            freq={props.question.frequency}
            gettext={props.gettext}
            plot={props.open}
          />
        </div>
        <MostConvincingRationales
          gettext={props.gettext}
          rationales={props.question.most_convincing_rationales}
        />
      </DialogContent>
      <DialogActions>
        <DialogButton ripple action="accept" isDefaultAction>
          {props.gettext("Done")}
        </DialogButton>
      </DialogActions>
    </Dialog>
  );
}

export class QuestionFlagDialog extends Component {
  state = {
    reasons: [],
    selectedReason: "",
  };

  handleSubmit = async (evt) => {
    if (evt.target.form.checkValidity()) {
      console.debug("Submit flag");
      try {
        await submitData(
          this.props.urls[1],
          { reason: this.state.selectedReason, id: this.props.question.pk },
          "POST",
        );
        this.props.callback();
      } catch (error) {
        console.debug(error);
      }
    }
  };

  refreshFromDB = async () => {
    try {
      const data = await get(this.props.urls[0]);
      console.debug(data);
      this.setState({
        reasons: data.reasons,
      });
    } catch (error) {
      console.debug(error);
    }
  };

  shouldComponentUpdate(nextProps, nextState) {
    if (this.props.question != nextProps.question) {
      this.setState({ selectedReason: "" });
    }
  }

  componentDidMount() {
    this.refreshFromDB();
  }

  render() {
    return (
      <Dialog open={this.props.open} onClose={this.props.onClose}>
        <DialogTitle>{this.props.question.title}</DialogTitle>
        <DialogContent>
          <div style={{ marginBottom: 16 }}>
            <Info
              text={this.props.gettext(
                `You can flag this question as problematic using the form below.
                This will immediately remove it from search results pending
                review.  It will not remove it from assignments.`,
              )}
            />
          </div>
          <form
            id="flag-question-form"
            method="POST"
            onKeyDown={(evt) => evt.stopPropagation()}
            onSubmit={(evt) => evt.preventDefault()}
          >
            <Select
              autofocus
              onChange={(e) => {
                this.setState({
                  selectedReason: e.target.value,
                });
              }}
              options={this.state.reasons}
              outlined
              required
              style={{ appearance: "none" }}
              value={this.state.selectedReason}
            />
            <SelectHelperText persistent>
              {this.props.gettext(
                "Please select the reason for flagging this question.",
              )}
            </SelectHelperText>
          </form>
        </DialogContent>
        <DialogActions>
          <DialogButton ripple action="accept" isDefaultAction>
            {this.props.gettext("Cancel")}
          </DialogButton>
          <DialogButton
            ripple
            type="submit"
            form="flag-question-form"
            onClick={this.handleSubmit}
          >
            {this.props.gettext("Submit")}
          </DialogButton>
        </DialogActions>
      </Dialog>
    );
  }
}

function QuestionCardActionButtons(props) {
  return (
    <CardActionButtons>
      <Typography use="caption" tag="div">
        {props.gettext("Discipline")}:{" "}
        <span>
          {props.question.discipline
            ? props.question.discipline.title
            : props.gettext("Unlabelled")}
        </span>
      </Typography>
      <Typography use="caption" tag="div">
        {props.gettext("Categories")}:{" "}
        <span>
          {props.question.category
            ? props.question.category.map((c) => c.title).join("; ")
            : props.gettext("Uncategorized")}
        </span>
      </Typography>
      <Typography use="caption" tag="div">
        {props.gettext("Student answers")}: {props.question.answer_count}
      </Typography>
    </CardActionButtons>
  );
}

function Info(props) {
  return (
    <div class="info" style={{ display: "flex" }}>
      <Icon
        icon="info"
        iconOptions={{ strategy: "ligature", size: "small" }}
      />
      <Typography use="caption" tag="p">
        {props.text}
      </Typography>
    </div>
  );
}

function MostConvincingRationales(props) {
  if (props.rationales) {
    return (
      <div>
        {props.rationales.map((r, i) => {
          return (
            <div key={i}>
              <Typography
                use="body2"
                tag="p"
                theme="text-secondary-on-background"
                // This field is bleached and safe
                // eslint-disable-next-line
                dangerouslySetInnerHTML={{ __html: `${r.label}. ${r.text}` }}
                style={{ fontWeight: "bold" }}
              />
              <ul>
                {r.most_convincing.map((a, i) => {
                  return (
                    <Fragment key={i}>
                      <Typography
                        use="body2"
                        tag="li"
                        theme="text-secondary-on-background"
                        style={{
                          marginBottom: 4,
                          marginTop: 8,
                          listStyleType: "disc",
                        }}
                      >
                        {a.rationale}
                      </Typography>
                      <Typography
                        class="meta"
                        use="caption"
                        tag="div"
                        dangerouslySetInnerHTML={{
                          __html: `${props.gettext("Shown:")} ${
                            a.times_shown
                          } &middot; ${props.gettext("Chosen:")} ${
                            a.times_chosen
                          } &middot; ${props.gettext("Rate:")} ${(
                            (a.times_chosen / a.times_shown) *
                            100
                          ).toFixed(1)}%`,
                        }}
                      />
                    </Fragment>
                  );
                })}
              </ul>
            </div>
          );
        })}
      </div>
    );
  }
}

function AnswerChoices(props) {
  const answerChoice = (ac) => {
    if (Object.prototype.hasOwnProperty.call(ac, "correct")) {
      if (ac.correct) {
        return (
          <Icon
            icon="check"
            iconOptions={{ strategy: "ligature", size: "xsmall" }}
            style={{
              verticalAlign: "middle",
              transform: "translate(3px, -1px)",
            }}
            theme="primary"
          />
        );
      }
    }
  };

  if (props.show) {
    if (
      Object.prototype.hasOwnProperty.call(props.question, "answerchoice_set")
    ) {
      return (
        <div class="question-answers">
          <ol type={props.question.answer_style == 0 ? "A" : "l"}>
            {props.question.answerchoice_set.map((ac, i) => {
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
                  {answerChoice(ac)}
                </Typography>
              );
            })}
          </ol>
        </div>
      );
    }
  }
}

class Featured extends Component {
  state = {
    hovered: false,
  };

  render() {
    return (
      <Fragment>
        <a
          href={this.props.collection.url}
          rel="noreferrer"
          target="_blank"
          title={`${this.props.gettext(
            "This question is part of featured content curated by SALTISE.  Click to open the associated collection ",
          )}'${this.props.collection.title}' in a new tab.`}
        >
          <div
            class="featured-icon"
            onMouseEnter={() => this.setState({ hovered: true })}
            onMouseLeave={() => this.setState({ hovered: false })}
            style={{
              backgroundImage: this.state.hovered
                ? `url('${this.props.url[1]}')`
                : `url('${this.props.url[0]}')`,
            }}
          />
        </a>
      </Fragment>
    );
  }
}

function FavouriteIcon(props) {
  return (
    <Favourites.Consumer>
      {(favourites) => {
        return (
          <CardAction
            checked={favourites.includes(props.question)}
            onClick={props.handleToggle}
            onIcon="favorite"
            icon="favorite_border"
            theme="primary"
            title={props.gettext(
              "Select or remove this question as one of your favourites",
            )}
          />
        );
      }}
    </Favourites.Consumer>
  );
}

function FlagIcon(props) {
  return (
    <CardAction
      checked={this.props.checked}
      icon="outlined_flag"
      iconOptions={{
        strategy: "custom",
        render: ({ content, ...rest }) => (
          <span class="rmwc-icon material-icons-round mdc-icon-button__icon">
            {content}
          </span>
        ),
      }}
      onClick={() => props.handleToggle(props.question)}
      onIcon="flag"
      onIconOptions={{
        strategy: "custom",
        render: ({ content, ...rest }) => (
          <span class="rmwc-icon material-icons-round mdc-icon-button__icon mdc-icon-button__icon--on">
            {content}
          </span>
        ),
      }}
      theme="primary"
      title={props.gettext("Flag question for removal")}
    />
  );
}

class AssignmentAddIcon extends Component {
  render() {
    return (
      <CardAction
        theme="primary"
        icon="add"
        title={this.props.gettext("Add question to an assignment")}
      />
    );
  }
}

function Image(props) {
  if (props.image & props.show) {
    return (
      <Typography use="caption">
        <img alt={props.alt} class="question-image" src={props.image} />
      </Typography>
    );
  }
}

function Video(props) {
  if (props.url & props.show) {
    return (
      <object
        class="question-image"
        width="640"
        height="390"
        data={props.url}
      />
    );
  }
}

function QuestionCardHeader(props) {
  const byline = () => {
    if (Object.prototype.hasOwnProperty.call(props.question, "user")) {
      return (
        <div style={{ display: "inline" }}>
          <span>
            {props.gettext("by")} {props.question.user.username}
          </span>{" "}
          <span class="tag SALTISE">SALTISE</span>{" "}
          <span class="tag EXPERT">EXPERT</span>{" "}
          <span class="tag POWER">POWER USER</span>{" "}
          <span class="tag INFLUENCER">TOP CONTRIBUTOR</span>
        </div>
      );
    }
  };

  const featured = () => {
    if (props.question.featured) {
      return (
        <Featured
          collection={this.props.question.collections[0]}
          gettext={this.props.gettext}
          url={this.props.featuredIconURL}
        />
      );
    }
  };

  return (
    <Fragment>
      <div>
        <Typography
          class="title"
          use="headline5"
          tag="h2"
          // This field is bleached and safe
          // eslint-disable-next-line
          dangerouslySetInnerHTML={{
            __html: props.question.title,
          }}
        />
        {featured()}
      </div>
      <Typography
        use="caption"
        tag="div"
        theme="text-secondary-on-background"
        style={{ marginBottom: 10 }}
      >
        #{props.question.pk} {byline()}
      </Typography>
    </Fragment>
  );
}

function QuestionCardBody(props) {
  return (
    <div>
      <Typography
        use="body1"
        tag="div"
        theme="text-secondary-on-background"
        // This field is bleached and safe
        // eslint-disable-next-line
        dangerouslySetInnerHTML={{ __html: props.question.text }}
      />
      <Image
        alt={props.question.image_alt_text}
        image={props.question.image}
        show={true}
      />
      <Video url={props.question.video_url} show={true} />
      <AnswerChoices question={props.question} show={true} />
    </div>
  );
}

function Ratings(props) {
  const difficulty = () => {
    if (
      Object.prototype.hasOwnProperty.call(props.question.difficulty, "score")
    ) {
      const colourScale = scaleThreshold(triScale).domain([0.25, 0.5]);
      const color = colourScale(props.question.difficulty.score);
      const opacity = "30";
      const label = props.question.difficulty.label;
      return (
        <div
          class="rating"
          style={{
            backgroundColor: color + opacity,
            borderColor: color,
            cursor: "pointer",
          }}
          onClick={() => props.toggleDialog(props.question)}
        >
          <svg
            width="40"
            height="40"
            xmlns="http://www.w3.org/2000/svg"
            style={{ overflow: "visible" }}
          >
            <path
              id={`path-${props.question.pk}`}
              d="M -3 16 A 19 19 0 0 1 35 16"
              fill="transparent"
            />
            <text text-anchor="middle">
              <textPath
                fill={color}
                startOffset="50%"
                style={{ fill: color, fontSize: 8 }}
                xmlnsXlink="http://www.w3.org/1999/xlink"
                xlinkHref={`#path-${props.question.pk}`}
              >
                {this.props.gettext("Click!")}
              </textPath>
            </text>
          </svg>
          <div
            class="label"
            style={{
              color,
            }}
          >
            {label}
          </div>
        </div>
      );
    }
  };

  const impact = () => {
    if (
      Object.prototype.hasOwnProperty.call(props.question.peer_impact, "score")
    ) {
      const colourScale = scaleThreshold(triScale).domain([0.05, 0.25]);
      const color = colourScale(props.question.peer_impact.score);
      const opacity = "30";
      return (
        <div
          class="rating"
          style={{
            backgroundColor: color + opacity,
            borderColor: color,
          }}
        >
          <div class="label" style={{ color }}>
            {props.question.peer_impact.label}
          </div>
        </div>
      );
    }
  };

  return (
    <div class="ratings">
      {difficulty()}
      {impact()}
    </div>
  );
}

export function SearchQuestionCard(props) {
  return (
    <div>
      <Card class="question" style={{ position: "relative" }}>
        <Ratings
          gettext={this.props.gettext}
          question={props.question}
          toggleDialog={props.toggleDialog}
        />
        <div style={{ paddingRight: 40 }}>
          <QuestionCardHeader
            featuredIconURL={props.featuredIconURL}
            gettext={props.gettext}
            question={props.question}
          />
          <QuestionCardBody
            gettext={props.gettext}
            question={props.question}
          />
        </div>
        <CardActions>
          <QuestionCardActionButtons
            gettext={props.gettext}
            question={props.question}
          />
          <CardActionIcons>
            <FlagIcon
              checked={
                this.props.flagged
                  ? this.props.question.pk == this.props.flagged.pk
                  : false
              }
              gettext={props.gettext}
              handleToggle={props.toggleFlagDialog}
              question={{
                pk: props.question.pk,
                title: props.question.title,
              }}
            />
            <AssignmentAddIcon gettext={props.gettext} />
            <FavouriteIcon
              gettext={props.gettext}
              handleToggle={() =>
                props.handleToggleFavourite(parseInt(props.question.pk))
              }
              question={parseInt(props.question.pk)}
            />
          </CardActionIcons>
        </CardActions>
      </Card>
    </div>
  );
}
