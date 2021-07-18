import { Component, Fragment, h } from "preact";

import {
  Dialog,
  DialogActions,
  DialogButton,
  DialogContent,
} from "@rmwc/dialog";
import { Icon } from "@rmwc/icon";
import { LinearProgress } from "@rmwc/linear-progress";
import { Snackbar } from "@rmwc/snackbar";
import { Typography } from "@rmwc/typography";

import "@rmwc/button/node_modules/@material/button/dist/mdc.button.css";
import "@rmwc/dialog/node_modules/@material/dialog/dist/mdc.dialog.css";
import "@rmwc/icon/icon.css";
import "@rmwc/linear-progress/node_modules/@material/linear-progress/dist/mdc.linear-progress.min.css";
import "@rmwc/snackbar/node_modules/@material/snackbar/dist/mdc.snackbar.min.css";
import "@rmwc/typography/node_modules/@material/typography/dist/mdc.typography.min.css";

import { get } from "../_ajax/ajax.js";
import { Choices } from "../_assignment/question.jsx";

class Feedback extends Component {
  scores = Array.from([0, 1, 2, 3]);

  annotations = Array.from([
    this.props.gettext("Unacceptable"),
    this.props.gettext("Not convincing"),
    this.props.gettext("Somewhat convincing"),
    this.props.gettext("Very convincing"),
  ]);

  insertFeedback = () => {
    if (this.props.feedback.note) {
      return (
        <Fragment>
          <p>
            <strong>{this.props.gettext("Your teacher commented:")}</strong>
          </p>
          <blockquote>{this.props.feedback.note}</blockquote>
        </Fragment>
      );
    }
  };

  insertSummary = () => {
    if (this.props.feedback.answer.answer_choice.text) {
      return (
        <Fragment>
          <blockquote
            // eslint-disable-next-line
            dangerouslySetInnerHTML={{
              __html: this.props.feedback.answer.answer_choice.text,
            }}
          />
          <p>
            <strong>{this.props.gettext("because")}</strong>
          </p>
          <blockquote>{this.props.feedback.answer.rationale}</blockquote>
        </Fragment>
      );
    }
    return <blockquote>{this.props.feedback.answer.rationale}</blockquote>;
  };

  insertScore = () => {
    if (this.props.feedback.score >= 0) {
      const title =
        this.props.gettext("Your rationale is: ") +
        this.annotations[this.props.feedback.score].toLowerCase();
      return (
        <div
          style={{
            cursor: "default",
            paddingRight: "40px",
            textAlign: "right",
          }}
        >
          <Icon
            icon={this.props.feedback.score == 0 ? "flag" : "outlined_flag"}
            theme="primary"
            title={title}
          />

          {this.scores.slice(1).map((score, i) => {
            return (
              <Icon
                key={i}
                icon={
                  this.props.feedback.score >= score ? "star" : "star_border"
                }
                theme="primary"
                title={title}
              />
            );
          })}
        </div>
      );
    }
  };

  render() {
    return (
      <div style={{ marginTop: "14px", paddingBottom: "4px" }}>
        <Typography use="headline5">
          <div
            // eslint-disable-next-line
            dangerouslySetInnerHTML={{
              __html: this.props.feedback.answer.question.title,
            }}
            style={{ marginBottom: "12px" }}
          />
        </Typography>
        <Typography use="body1">
          <div
            // eslint-disable-next-line
            dangerouslySetInnerHTML={{
              __html: this.props.feedback.answer.question.text,
            }}
          />
        </Typography>
        <Choices
          show={true}
          choices={this.props.feedback.answer.question.answerchoice_set}
        />

        <div style={{ marginTop: "16px" }}>
          <Typography use="body1">
            <p>
              <strong>{this.props.gettext("You thought:")}</strong>
            </p>
            {this.insertSummary()}
            {this.insertFeedback()}
          </Typography>
          {this.insertScore()}
        </div>
      </div>
    );
  }
}

export class FeedbackApp extends Component {
  state = {
    loaded: false,
    feedback: [],
    snackbarIsOpen: false,
    snackbarMessage: "",
  };

  refreshFromDB = async () => {
    // Load answer data
    this.setState({ loaded: false });
    try {
      const data = await get(this.props.feedbackURL);
      console.debug(data);
      this.setState(
        {
          feedback: data,
          loaded: true,
        },
        this.props.callback(
          Array.from(
            new Set(
              data
                .filter((el) => this.props.teacherPk.includes(el.annotator))
                .map((el) => el.answer.assignment),
            ),
          ),
        ),
      );
    } catch (error) {
      console.error(error);
      this.setState({
        loaded: true,
        snackbarIsOpen: true,
        snackbarMessage: this.props.gettext(
          "An error occurred.  Try refreshing this page.",
        ),
      });
    }
  };

  componentDidMount() {
    this.refreshFromDB();
  }

  shouldComponentUpdate() {
    this.props.callback(
      Array.from(
        new Set(
          this.state.feedback
            .filter((el) => this.props.teacherPk.includes(el.annotator))
            .map((el) => el.answer.assignment),
        ),
      ),
    );
    return true;
  }

  render() {
    if (!this.state.loaded) {
      return <LinearProgress determinate={false} style={{ width: "775px" }} />;
    }
    const feedbackList = this.state.feedback.filter(
      (el) =>
        el.answer.assignment == this.props.assignmentId &&
        this.props.teacherPk.includes(el.annotator),
    );
    return (
      <div>
        <Dialog
          open={this.props.dialogIsOpen}
          onClose={() => this.props.listener()}
        >
          <DialogContent
            style={{
              display: "flex",
              flexDirection: "column",
            }}
          >
            <div style={{ maxWidth: "775px" }}>
              {feedbackList.map((el, i) => (
                <Feedback feedback={el} gettext={this.props.gettext} key={i} />
              ))}
            </div>
          </DialogContent>
          <DialogActions>
            <DialogButton action="accept" isDefaultAction theme="primary">
              {this.props.gettext("Done")}
            </DialogButton>
          </DialogActions>
        </Dialog>
        <Snackbar
          show={this.state.snackbarIsOpen}
          onHide={(evt) => this.setState({ snackbarIsOpen: false })}
          message={this.state.snackbarMessage}
          timeout={5000}
          actionHandler={() => {}}
          actionText="OK"
          dismissesOnAction={true}
          alignStart
        />
      </div>
    );
  }
}
