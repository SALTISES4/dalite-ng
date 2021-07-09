import { Component, Fragment, h } from "preact";
import { triScale } from "../_theming/colours.js";
import { scaleThreshold } from "d3";
import { Favourites } from "./providers.js";
import { PlotConfusionMatrix } from "../_assignment/analytics.js";

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
import { Typography } from "@rmwc/typography";

import "@rmwc/button/node_modules/@material/button/dist/mdc.button.min.css";
import "@rmwc/card/node_modules/@material/card/dist/mdc.card.css";
import "@rmwc/dialog/node_modules/@material/dialog/dist/mdc.dialog.min.css";
import "@rmwc/icon/icon.css";
import "@rmwc/icon-button/node_modules/@material/icon-button/dist/mdc.icon-button.min.css";
import "@rmwc/theme/node_modules/@material/theme/dist/mdc.theme.min.css";
import "@rmwc/typography/node_modules/@material/typography/dist/mdc.typography.min.css";

triScale.reverse();

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
                    <Typography
                      use="body2"
                      tag="li"
                      theme="text-secondary-on-background"
                      key={i}
                      style={{ marginBottom: 8, listStyleType: "disc" }}
                    >
                      {a.rationale}
                    </Typography>
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

function Image(props) {
  if (props.image) {
    return (
      <Typography use="caption">
        <img alt={props.alt} class="question-image" src={props.image} />
      </Typography>
    );
  }
}

function Video(props) {
  if (props.url) {
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
        image={props.question.image}
        alt={props.question.image_alt_text}
      />
      <Video url={props.question.video_url} />
      <AnswerChoices question={props.question} show={true} />
    </div>
  );
}

function SearchQuestionCardActionIcons(props) {
  return (
    <Fragment>
      <CardAction
        theme="primary"
        onIcon="flag"
        icon="outlined_flag"
        title={props.gettext("Flag question for removal")}
      />
      <CardAction
        theme="primary"
        icon="add"
        title={props.gettext("Add question to an assignment")}
      />
    </Fragment>
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
      const label = props.dialogOpen
        ? "close"
        : props.question.difficulty.label;
      return (
        <div
          class="rating"
          style={{
            backgroundColor: color + opacity,
            borderColor: color,
            cursor: "pointer",
          }}
          onClick={props.toggleDialog}
        >
          <div
            class="label"
            style={{
              color,
              fontFamily: props.dialogOpen ? "Material Icons" : "inherit",
              fontSize: props.dialogOpen ? 18 : "inherit",
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

export class SearchQuestionCard extends Component {
  state = {
    dialogOpen: false,
  };

  toggleDialog = () => {
    this.setState({ dialogOpen: !this.state.dialogOpen });
  };

  render() {
    return (
      <div>
        <Card class="question" style={{ position: "relative" }}>
          <Ratings
            dialogOpen={this.state.dialogOpen}
            question={this.props.question}
            toggleDialog={this.toggleDialog}
          />
          <div style={{ paddingRight: 40 }}>
            <QuestionCardHeader
              featuredIconURL={this.props.featuredIconURL}
              gettext={this.props.gettext}
              question={this.props.question}
            />
            <QuestionCardBody
              analyticsOpen={this.state.analyticsOpen}
              gettext={this.props.gettext}
              question={this.props.question}
            />
          </div>
          <CardActions>
            <CardActionButtons>
              <Typography use="caption" tag="div">
                {this.props.gettext("Discipline")}:{" "}
                <span>
                  {this.props.question.discipline
                    ? this.props.question.discipline.title
                    : this.props.gettext("Unlabelled")}
                </span>
              </Typography>
              <Typography use="caption" tag="div">
                {this.props.gettext("Categories")}:{" "}
                <span>
                  {this.props.question.category
                    ? this.props.question.category
                        .map((c) => c.title)
                        .join("; ")
                    : this.props.gettext("Uncategorized")}
                </span>
              </Typography>
              <Typography use="caption" tag="div">
                {this.props.gettext("Student answers")}:{" "}
                {this.props.question.answer_count}
              </Typography>
            </CardActionButtons>
            <CardActionIcons>
              <SearchQuestionCardActionIcons gettext={this.props.gettext} />
              <FavouriteIcon
                gettext={this.props.gettext}
                handleToggle={() =>
                  this.props.handleToggleFavourite(
                    parseInt(this.props.question.pk),
                  )
                }
                question={parseInt(this.props.question.pk)}
              />
            </CardActionIcons>
          </CardActions>
        </Card>
        <Dialog open={this.state.dialogOpen} onClose={this.toggleDialog}>
          <DialogTitle>{this.props.question.title}</DialogTitle>
          <DialogContent>
            <div style={{ marginBottom: 16 }}>
              <Info
                text={this.props.gettext(
                  `The distribution of first and second choices along with the
                statistics for each possible outcome is shown in the figure
                below.  The most convincing rationales submitted by students
                (i.e. most selected be peers) are listed below for each answer
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
              {this.props.gettext("Distribution of answer choices")}
            </Typography>
            <div style={{ margin: "16px 0px" }}>
              <PlotConfusionMatrix
                _matrix={this.props.question.matrix}
                freq={this.props.question.frequency}
                gettext={this.props.gettext}
                plot={this.state.dialogOpen}
              />
            </div>
            <MostConvincingRationales
              rationales={this.props.question.most_convincing_rationales}
            />
          </DialogContent>
          <DialogActions>
            <DialogButton ripple action="accept" isDefaultAction>
              {this.props.gettext("Done")}
            </DialogButton>
          </DialogActions>
        </Dialog>
      </div>
    );
  }
}
