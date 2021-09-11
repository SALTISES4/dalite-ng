import moment from "moment";
import { Component, Fragment, h } from "preact";

import { CircularProgress } from "@rmwc/circular-progress";
import {
  DataTable,
  DataTableContent,
  DataTableHead,
  DataTableBody,
  DataTableHeadCell,
  DataTableRow,
  DataTableCell,
} from "@rmwc/data-table";
import {
  Dialog,
  DialogActions,
  DialogButton,
  DialogContent,
} from "@rmwc/dialog";
import { IconButton } from "@rmwc/icon-button";
import { LinearProgress } from "@rmwc/linear-progress";
import { Snackbar } from "@rmwc/snackbar";
import { TextField } from "@rmwc/textfield";
import { Typography } from "@rmwc/typography";

import "@rmwc/button/node_modules/@material/button/dist/mdc.button.css";
import "@rmwc/circular-progress/circular-progress.css";
import "@rmwc/data-table/data-table.css";
import "@rmwc/dialog/node_modules/@material/dialog/dist/mdc.dialog.css";
import "@rmwc/icon-button/node_modules/@material/icon-button/dist/mdc.icon-button.min.css";
import "@rmwc/linear-progress/node_modules/@material/linear-progress/dist/mdc.linear-progress.min.css";
import "@rmwc/snackbar/node_modules/@material/snackbar/dist/mdc.snackbar.min.css";
import "@rmwc/textfield/node_modules/@material/textfield/dist/mdc.textfield.css";
import "@rmwc/theme/node_modules/@material/theme/dist/mdc.theme.min.css";
import "@rmwc/typography/node_modules/@material/typography/dist/mdc.typography.min.css";

import { get, submitData } from "../_ajax/ajax";
import { Choices } from "../_assignment/question.jsx";

class Question extends Component {
  state = {
    loaded: false,
    question: null,
  };

  refreshFromDB = async () => {
    // Load question instance
    try {
      const data = await get(this.props.url);
      console.debug(data);
      this.setState({
        loaded: true,
        question: data,
      });
    } catch (error) {
      // Ignore 404s
      this.setState({
        loaded: true,
      });
    }
  };

  componentDidMount() {
    this.refreshFromDB();
  }

  render() {
    if (!this.state.loaded) {
      return <CircularProgress size="xlarge" />;
    }
    return (
      <div style={{ padding: "16px 0px", width: "775px" }}>
        <Typography use="headline5" theme="secondary">
          <div
            // eslint-disable-next-line
            dangerouslySetInnerHTML={{ __html: this.state.question.title }}
          />
        </Typography>
        <div style={{ marginTop: "12px", marginBottom: "4px" }}>
          <Typography use="body1">
            <div
              // eslint-disable-next-line
              dangerouslySetInnerHTML={{ __html: this.state.question.text }}
            />
          </Typography>
          <Choices
            show={true}
            choices={this.state.question.answerchoice_set}
          />
        </div>
      </div>
    );
  }
}

class AnswerFeedback extends Component {
  state = {
    changed: false,
    charcterCount: 0,
    create: true,
    loaded: false,
    note: "",
    saving: false,
    score: null,
    score_hover: null,
  };

  characterLimit = 2000;

  scores = Array.from([1, 2, 3]);
  annotations = Array.from([
    this.props.gettext("Not convincing"),
    this.props.gettext("Somewhat convincing"),
    this.props.gettext("Very convincing"),
  ]);

  refreshFromDB = async () => {
    // Load answer annotation instance
    try {
      const data = await get(
        `${this.props.feedbackURL}through_answer/${this.props.pk}/`,
      );
      console.debug(data);
      this.setState({
        characterCount: data["note"] ? data["note"].length : 0,
        create: false,
        loaded: true,
        note: data["note"] ? data["note"] : "",
        score: data["score"],
      });
    } catch (error) {
      // Ignore 404s
      this.setState({
        characterCount: 0,
        loaded: true,
      });
    }
  };

  save = async (score) => {
    if (!this.state.saving) {
      this.setState({ saving: true });
      let data;
      try {
        if (!this.state.create) {
          // Object exists, so PATCH
          data = await submitData(
            `${this.props.feedbackURL}through_answer/${this.props.pk}/`,
            { note: this.state.note, score },
            "PATCH",
          );
          console.info(data);
        } else {
          // Object doesn't exist, so POST
          data = await submitData(
            this.props.feedbackURL,
            {
              answer: this.props.pk,
              note: this.state.note,
              score,
            },
            "POST",
          );
          console.info(data);
        }
        this.setState({
          changed: false,
          create: false,
          saving: false,
          score: data["score"],
          score_hover: null,
        });
        this.props.setSnackbar(true, this.props.gettext("Saved"));
      } catch (error) {
        console.error(error);
        this.props.setSnackbar(
          true,
          this.props.gettext("An error occurred.  Try refreshing this page."),
        );
        this.setState({
          saving: false,
        });
      }
    }
  };

  note = () => {
    let msg;
    if (this.state.saving) {
      msg = this.props.gettext("Saving...");
    } else {
      const left = this.characterLimit - this.state.characterCount;
      msg = left + this.props.gettext(" characters left");
    }
    return (
      <div class="timestamp" style={{ textAlign: "right" }}>
        {msg}
      </div>
    );
  };

  componentDidMount() {
    this.refreshFromDB();
  }

  render() {
    if (!this.state.loaded) {
      return <CircularProgress size="xlarge" />;
    }
    return (
      <div style={{ position: "relative" }}>
        <TextField
          textarea
          fullwidth
          rows="3"
          label={this.props.gettext("Comments")}
          dense
          value={this.state.note}
          onInput={(evt) => {
            if (evt.target.value.length <= this.characterLimit) {
              this.setState({
                changed: true,
                characterCount: evt.target.value.length,
                note: evt.target.value,
              });
            } else {
              evt.target.value = this.state.note;
            }
          }}
          onBlur={() => {
            if (this.state.changed) {
              this.save(this.state.score);
            }
          }}
          style={{ resize: "vertical" }}
        />

        {this.note()}

        <div style={{ position: "relative", top: "-14px" }}>
          <IconButton
            icon="outlined_flag"
            checked={
              (this.state.score == 0 && this.state.score_hover == null) ||
              (this.state.score != 0 && this.state.score_hover == 0)
            }
            onClick={() =>
              this.state.score != 0 ? this.save(0) : this.save(null)
            }
            onIcon="flag"
            onMouseEnter={() => {
              this.setState({ score_hover: 0 });
            }}
            onMouseOut={() => {
              this.setState({ score_hover: null });
            }}
            theme="primary"
            title={this.props.gettext("Never show")}
          />

          {this.scores.map((score, i) => {
            return (
              <IconButton
                key={i}
                icon="star_border"
                checked={
                  (this.state.score >= score &&
                    this.state.score_hover >= score) ||
                  (this.state.score >= score &&
                    this.state.score_hover == null) ||
                  (this.state.score != score &&
                    this.state.score_hover >= score)
                }
                onClick={() => this.save(score)}
                onIcon="star"
                onMouseEnter={() => {
                  this.setState({ score_hover: score });
                }}
                onMouseOut={() => {
                  this.setState({ score_hover: null });
                }}
                theme="primary"
                title={this.annotations[i]}
              />
            );
          })}
        </div>
      </div>
    );
  }
}

export class RationaleTableApp extends Component {
  state = {
    answers: [],
    answersNatural: [],
    loaded: false,
    snackbarIsOpen: false,
    snackbarMessage: "",
  };

  refreshFromDB = async (url = this.props.readURL) => {
    // Load answer data
    this.setState({ loaded: false });
    try {
      const data = await get(url);
      console.debug(data);
      this.setState({
        answers: data["answers"],
        answersNatural: data["answers"],
        loaded: true,
      });
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

  setSnackbar = (snackbarIsOpen, snackbarMessage) => {
    this.setState({ snackbarIsOpen, snackbarMessage });
  };

  componentDidMount() {
    this.refreshFromDB();
  }

  shouldComponentUpdate(nextProps, nextState) {
    if (this.props.readURL != nextProps.readURL) {
      this.refreshFromDB(nextProps.readURL);
    }
    return true;
  }

  render() {
    if (!this.state.loaded) {
      return <LinearProgress determinate={false} style={{ width: "775px" }} />;
    }
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
              overflowY: "hidden",
            }}
          >
            <Question url={this.props.questionURL} />
            <DataTable
              stickyRows="1"
              style={{ height: "100%", width: "800px" }}
            >
              <DataTableContent>
                <DataTableHead>
                  <DataTableRow>
                    <DataTableHeadCell
                      alignStart
                      sort={this.state.sortDir || null}
                      onSortChange={(sortDir) => {
                        if (sortDir) {
                          const _answers = Array.from(this.state.answers);
                          _answers.sort((a, b) =>
                            a.user_email.localeCompare(b.user_email) < 0
                              ? sortDir * 1
                              : sortDir * -1,
                          );
                          this.setState({ sortDir, answers: _answers });
                        } else {
                          this.setState({
                            sortDir,
                            answers: this.state.answersNatural,
                          });
                        }
                      }}
                    >
                      <Typography use="body2" theme="secondary">
                        <span style={{ textDecoration: "underline" }}>
                          {this.props.gettext("Student")}
                        </span>
                      </Typography>
                    </DataTableHeadCell>
                    <DataTableHeadCell
                      style={{ paddingLeft: "0px", paddingRight: "0px" }}
                    >
                      <Typography use="body2" theme="secondary">
                        {this.props.gettext("1st")}
                      </Typography>
                    </DataTableHeadCell>
                    <DataTableHeadCell alignStart>
                      <Typography use="body2" theme="secondary">
                        {this.props.gettext("Rationale")}
                      </Typography>
                    </DataTableHeadCell>
                    <DataTableHeadCell
                      style={{ paddingLeft: "0px", paddingRight: "0px" }}
                    >
                      <Typography use="body2" theme="secondary">
                        {this.props.gettext("2nd")}
                      </Typography>
                    </DataTableHeadCell>
                    <DataTableHeadCell>
                      <Typography use="body2" theme="secondary">
                        {this.props.gettext("Chosen rationale")}
                      </Typography>
                    </DataTableHeadCell>
                    <DataTableHeadCell alignStart>
                      <Typography use="body2" theme="secondary">
                        {this.props.gettext("Feedback")}
                      </Typography>
                    </DataTableHeadCell>
                  </DataTableRow>
                </DataTableHead>
                <DataTableBody>
                  {this.state.answers.map((answer) => (
                    <Fragment key={answer.id}>
                      <DataTableRow>
                        <DataTableCell alignStart>
                          {answer.user_email.substring(0, 10)}
                        </DataTableCell>
                        <DataTableCell
                          alignMiddle
                          theme="secondary"
                          style={{ paddingLeft: "0px", paddingRight: "0px" }}
                        >
                          <strong>{answer.first_answer_choice_label}</strong>
                        </DataTableCell>
                        <DataTableCell
                          alignStart
                          style={{ whiteSpace: "normal" }}
                        >
                          <Typography use="body2">
                            {answer.rationale}
                          </Typography>
                          <div class="timestamp">
                            {moment(answer.timestamp).format("MM/DD/YY LT")}
                          </div>
                        </DataTableCell>
                        <DataTableCell
                          alignMiddle
                          theme="secondary"
                          style={{ paddingLeft: "0px", paddingRight: "0px" }}
                        >
                          <strong>{answer.second_answer_choice_label}</strong>
                        </DataTableCell>
                        <DataTableCell
                          alignStart
                          style={{ whiteSpace: "normal" }}
                        >
                          <Typography use="body2">
                            {answer.chosen_rationale}
                          </Typography>
                        </DataTableCell>
                        <DataTableCell
                          style={{
                            minWidth: "250px",
                            paddingRight: "0.75rem",
                            whiteSpace: "normal",
                          }}
                        >
                          <AnswerFeedback
                            feedbackURL={this.props.feedbackURL}
                            gettext={this.props.gettext}
                            pk={answer.id}
                            setSnackbar={this.setSnackbar}
                          />
                        </DataTableCell>
                      </DataTableRow>
                    </Fragment>
                  ))}
                </DataTableBody>
              </DataTableContent>
            </DataTable>
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
          timeout={2000}
          actionHandler={() => {}}
          actionText="OK"
          dismissesOnAction={true}
          alignStart
        />
      </div>
    );
  }
}
