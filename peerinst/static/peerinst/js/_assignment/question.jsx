import { Component, createContext, Fragment, h } from "preact";

import {
  Card,
  CardAction,
  CardActions,
  CardActionButtons,
  CardActionIcons,
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

import { colours, PlotConfusionMatrix } from "./analytics";

import "@rmwc/icon-button/node_modules/@material/icon-button/dist/mdc.icon-button.min.css";
import "@rmwc/card/node_modules/@material/card/dist/mdc.card.min.css";
import "@rmwc/typography/node_modules/@material/typography/dist/mdc.typography.min.css";
import "@rmwc/dialog/node_modules/@material/dialog/dist/mdc.dialog.min.css";
import "@rmwc/button/node_modules/@material/button/dist/mdc.button.min.css";
import "@rmwc/theme/node_modules/@material/theme/dist/mdc.theme.min.css";
import "@rmwc/icon/icon.css";

export const User = createContext();
export const Favourites = createContext();

class Image extends Component {
  render() {
    if (this.props.url) {
      return (
        <img
          alt={this.props.altText}
          className="mdc-typography--caption question-image"
          src={this.props.url}
          style={{ display: this.props.show ? "block" : "none" }}
        />
      );
    }
  }
}

const Checkmark = (props) => {
  if (props.correct) {
    return (
      <Icon
        icon="check"
        iconOptions={{ strategy: "ligature", size: "xsmall" }}
        style={{ verticalAlign: "middle" }}
        theme="primary"
      />
    );
  }
  return <Fragment />;
};

export const Choices = (props) => {
  if (props.show) {
    return (
      <ol type={props.answerStyle == 0 ? "A" : "l"}>
        {props.choices.map((choice, i) => {
          return (
            <li className="dense-list" key={i}>
              {/* eslint-disable-next-line */}
              <span dangerouslySetInnerHTML={{ __html: choice.text }} />{" "}
              <Checkmark correct={choice.correct} />
            </li>
          );
        })}
      </ol>
    );
  }
  return <Fragment />;
};

export class QuestionCard extends Component {
  state = {
    dialogOpen: false,
  };

  renderCategory = () => {
    if (this.props.question.category.length > 0) {
      return this.props.question.category.map((el, index) =>
        index > 0 ? `, ${el.title}` : el.title,
      );
    }
    return this.props.gettext("Uncategorized");
  };

  editOrCopy = () => {
    return (
      <User.Consumer>
        {(user) => {
          let mode;
          let title;
          let onclick;
          if (
            this.props.question.user
              ? this.props.question.user.username == user ||
                this.props.question.collaborators.includes(user)
              : false
          ) {
            mode = "edit";
            title = this.props.gettext("Edit");
            onclick = () =>
              (window.location = this.props.editURL + this.props.question.pk);
          } else {
            mode = "file_copy";
            title = this.props.gettext("Copy and edit this question.");
            onclick = () =>
              (window.location = this.props.cloneURL + this.props.question.pk);
          }
          return (
            <CardAction
              icon={mode}
              onclick={onclick}
              title={title}
              theme="primary"
            />
          );
        }}
      </User.Consumer>
    );
  };

  addOrDelete = () => {
    if (this.props.handleQuestionDelete) {
      return (
        <CardAction
          icon="cancel"
          onClick={() => this.props.handleQuestionDelete(this.props.rank)}
          title={this.props.gettext(
            "Remove this question from this assignment.",
          )}
          theme="primary"
        />
      );
    }
    return (
      <CardAction
        icon="add_circle"
        onClick={() =>
          this.props.handleQuestionAdd(this.props.question.pk, this.props.rank)
        }
        title={this.props.gettext("Add this question to this assignment.")}
        theme="primary"
      />
    );
  };

  getDifficultyLabel = () => {
    return Object.entries(this.props.question.matrix).sort(
      (a, b) => b[1] - a[1],
    )[0][0];
  };

  insertActions = () => (
    <Fragment>
      <div
        style={{
          position: "relative",
        }}
      >
        <CardAction
          icon="info"
          onClick={() => {
            this.setState({ dialogOpen: true });
          }}
          style={{ color: colours[this.getDifficultyLabel()] }}
          title={this.props.gettext(
            "Difficulty level based on past student answers.",
          )}
        />
        <div
          style={{
            color: colours[this.getDifficultyLabel()],
            position: "absolute",
            left: "50%",
            width: "inherit",
            transform: "translateX(-50%)",
            fontSize: "x-small",
            marginTop: "-8px",
          }}
        >
          {Array.from(this.getDifficultyLabel()).map((letter, i) =>
            i == 0 ? letter.toUpperCase() : letter.toLowerCase(),
          )}
        </div>
      </div>
      <Favourites.Consumer>
        {(favourites) => {
          return (
            <CardAction
              checked={favourites.includes(this.props.question.pk)}
              onClick={() => {
                this.props.handleToggleFavourite(this.props.question.pk);
              }}
              onIcon="favorite"
              icon="favorite_border"
              theme="primary"
              title={this.props.gettext(
                "Select or remove this question as one of your favourites.",
              )}
            />
          );
        }}
      </Favourites.Consumer>
      {this.editOrCopy()}
      {this.addOrDelete()}
    </Fragment>
  );

  cardHeader = () => {
    let byline = "";
    if (this.props.question.user) {
      byline = `${this.props.gettext("by")} ${
        this.props.question.user.username
      }`;
    }
    return (
      <div className="card-header">
        <Typography use="headline5">
          <div
            // eslint-disable-next-line
            dangerouslySetInnerHTML={{ __html: this.props.question.title }}
          />
        </Typography>
        <Typography use="caption">
          #{this.props.question.pk} {byline}
        </Typography>
      </div>
    );
  };

  cardBody = () => {
    if (!this.props.minimizeCards) {
      return (
        <div style={{ marginTop: "12px", marginBottom: "4px" }}>
          <Typography use="body1">
            <div
              // eslint-disable-next-line
              dangerouslySetInnerHTML={{ __html: this.props.question.text }}
            />
          </Typography>
          <Image
            show={this.props.showImages}
            url={this.props.question.image}
            altText={this.props.question.image_alt_text}
          />
          <Choices
            answerStyle={this.props.question.answer_style}
            show={this.props.showChoices}
            choices={this.props.question.answerchoice_set}
          />
        </div>
      );
    }
  };

  cardActions = () => {
    if (!this.props.minimizeCards) {
      return (
        <CardActions>
          <CardActionButtons>
            <Typography use="caption">
              <div class="hint">
                {this.props.gettext("Discipline")}:{" "}
                {this.props.question.discipline
                  ? this.props.question.discipline.title
                  : this.props.gettext("None")}
              </div>
              <div class="hint">
                {this.props.gettext("Categories")}: {this.renderCategory()}
              </div>
              <div class="hint">
                {this.props.gettext("Student answers")}:{" "}
                {this.props.question.answer_count}
              </div>
            </Typography>
          </CardActionButtons>
          <CardActionIcons>{this.insertActions()}</CardActionIcons>
        </CardActions>
      );
    }
  };

  render() {
    return (
      <div>
        <Card style={{ marginBottom: "10px", padding: "20px 20px 12px" }}>
          {this.cardHeader()}
          {this.cardBody()}
          {this.cardActions()}
        </Card>
        <Dialog
          open={this.state.dialogOpen}
          onClose={(evt) => {
            this.setState({ dialogOpen: false });
          }}
        >
          <DialogTitle>{this.props.question.title}</DialogTitle>
          <DialogContent>
            <PlotConfusionMatrix
              _matrix={this.props.question.matrix}
              freq={this.props.question.frequency}
              gettext={this.props.gettext}
              plot={this.state.dialogOpen}
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
