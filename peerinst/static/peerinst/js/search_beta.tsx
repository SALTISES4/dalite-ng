import { Component, Fragment, h } from "preact";

import { get, submitData } from "./_ajax/ajax";

import {
  AssignmentDialog,
  QuestionDialog,
  QuestionFlagDialog,
  SearchQuestionCard,
} from "./_components/question";
import { Favourites } from "./_components/providers.js";

import { CircularProgress } from "@rmwc/circular-progress";
import { Snackbar } from "@rmwc/snackbar";
import {
  TextField,
  TextFieldIcon,
  TextFieldHelperText,
} from "@rmwc/textfield";
import { Typography } from "@rmwc/typography";

import "@rmwc/circular-progress/circular-progress.css";
import "@rmwc/snackbar/node_modules/@material/snackbar/dist/mdc.snackbar.min.css";
import "@rmwc/textfield/node_modules/@material/textfield/dist/mdc.textfield.css";
import "@rmwc/typography/node_modules/@material/typography/dist/mdc.typography.min.css";

import {
  Assignment,
  AssignmentCreate,
  AssignmentForm,
  Question,
} from "./_components/types";

type ChipProps = {
  onClick: (a: string) => void;
  selected: boolean;
  text: string;
};

function Chip({ onClick, selected, text }: ChipProps) {
  return (
    <div
      className={selected ? "selected chips" : "chips"}
      onClick={() => onClick(text)}
    >
      {text}
    </div>
  );
}

type SearchData = {
  meta: {
    categories: string[];
    difficulties: string[];
    disciplines: string[];
    impacts: string[];
  };
  results: Question[];
};

type SearchAppProps = {
  assignmentURL: string;
  assignmentFormCheckIdURL: string;
  assignmentFormMetaDataURL: string;
  assignmentListURL: string;
  gettext: (a: string) => string;
  questionFlagURLs: string[];
  staticURL: string;
  url: string;
  teacherURL: string;
  featuredIconURL: string[];
};

type SearchAppState = {
  assignments: Assignment[];
  assignmentDialogOpen: boolean;
  assignmentDialogQuestion: Question;
  assignmentFormMetaData: AssignmentForm;
  query: string;
  questions: Question[];
  categories: string[];
  dialogOpen: boolean;
  dialogQuestion: Question;
  difficulties: string[];
  disciplines: string[];
  favourites: number[];
  favouritesLoading: boolean;
  flagDialogOpen: boolean;
  flagDialogQuestion: { title: string; pk: number };
  impacts: string[];
  lastKeyStroke: number;
  searching: boolean;
  selectedCategories: string[];
  selectedDifficulty: string;
  selectedDiscipline: string;
  selectedImpact: string;
  snackbarIsOpen: boolean;
  snackbarMessage: string;
  timeoutID: number;
};

export class SearchApp extends Component<SearchAppProps, SearchAppState> {
  state = {
    assignments: [],
    assignmentDialogOpen: false,
    assignmentDialogQuestion: {} as Question,
    assignmentFormMetaData: {} as AssignmentForm,
    query: "",
    questions: [],
    categories: [],
    dialogOpen: false,
    dialogQuestion: {} as Question,
    difficulties: [],
    disciplines: [],
    favourites: [],
    favouritesLoading: false,
    flagDialogOpen: false,
    flagDialogQuestion: {} as { title: string; pk: number },
    impacts: [],
    lastKeyStroke: 0,
    searching: false,
    selectedCategories: [],
    selectedDifficulty: "",
    selectedDiscipline: "",
    selectedImpact: "",
    snackbarIsOpen: false,
    snackbarMessage: "",
    timeoutID: 0,
  };

  handleToggleAssignmentDialog = (question: Question, open = true): void => {
    console.debug("handleToggleAssignmentDialog called");
    this.setState({
      assignmentDialogOpen: open,
      assignmentDialogQuestion: question,
    });
    return;
  };

  handleToggleDialog = (question: Question): void => {
    console.debug("handleToggleDialog called");
    this.setState({
      dialogOpen: !this.state.dialogOpen,
      dialogQuestion: question,
    });
    return;
  };

  handleToggleFlagDialog = (
    question: { title: string; pk: number },
    open = true,
  ): void => {
    console.debug(
      "Toggle flag for question: " +
        (question ? question.pk + question.title : ""),
    );
    this.setState({
      flagDialogOpen: open,
      flagDialogQuestion: question
        ? { title: question.title, pk: question.pk }
        : ({} as { title: string; pk: number }),
    });
    return;
  };

  handleSubmit = async (): Promise<void> => {
    /* Prevent searches from being submitted faster than once per DT ms */
    const DT = 500;
    const startTime = performance.now();
    console.debug("handleSubmit called");
    const timeElapsed = performance.now() - this.state.lastKeyStroke;
    if (timeElapsed > DT || this.state.questions.length == 0) {
      console.info("Submitting...");
      window.clearTimeout(this.state.timeoutID);
      this.setState(
        {
          assignmentDialogOpen: false,
          assignmentDialogQuestion: {} as Question,
          dialogOpen: false,
          dialogQuestion: {} as Question,
          flagDialogOpen: false,
          flagDialogQuestion: {} as { title: string; pk: number },
          lastKeyStroke: performance.now(),
        },
        () => console.debug(this.state),
      );
      const queryString = new URLSearchParams();
      queryString.append("search_string", this.state.query);
      const url = new URL(this.props.url, window.location.origin);
      url.search = queryString.toString();

      if (this.state.query.length > 2) {
        try {
          this.setState({ searching: true });
          const data = (await get(url.toString())) as SearchData;
          console.debug(data);
          this.setState(
            {
              categories: data.meta.categories,
              difficulties: data.meta.difficulties,
              disciplines: data.meta.disciplines,
              impacts: data.meta.impacts,
              questions: data.results,
              searching: false,
            },
            () =>
              console.debug(
                "Search time: " +
                  ((performance.now() - startTime) / 1000).toExponential(3) +
                  "s",
              ),
          );
        } catch (error) {
          console.debug(error);
          this.setState({
            snackbarIsOpen: true,
            snackbarMessage: this.props.gettext(
              "An error occurred.  Try refreshing this page.",
            ),
          });
        }
      } else {
        this.setState({
          questions: [],
          categories: [],
          difficulties: [],
          disciplines: [],
          impacts: [],
          selectedCategories: [],
          selectedDifficulty: "",
          selectedDiscipline: "",
          selectedImpact: "",
        });
      }
    } else {
      window.clearTimeout(this.state.timeoutID);
      this.setState({
        lastKeyStroke: performance.now(),
        timeoutID: window.setTimeout(this.handleSubmit, DT),
      });
    }
    return;
  };

  handleAssignmentSubmit = async (
    questionPK: number,
    assignments: string[] = [],
    newAssignmentData: AssignmentCreate = {} as AssignmentCreate,
  ): Promise<void> => {
    console.debug("handleAssignmentSubmit called");
    console.debug(questionPK, assignments, newAssignmentData);
    if (Object.keys(newAssignmentData).length > 0) {
      try {
        const _assignment = await submitData(
          this.props.assignmentListURL,
          newAssignmentData,
          "POST",
        );
        console.debug(_assignment);
        assignments = [(_assignment as AssignmentCreate).pk];
      } catch (error) {
        console.error(error);
        this.setState({
          snackbarIsOpen: true,
          snackbarMessage: this.props.gettext("An error occurred."),
        });
      }
    }
    const added: string[] = [];
    for await (const a of assignments) {
      try {
        await submitData(
          this.props.assignmentURL,
          { assignment: a, question_pk: questionPK },
          "POST",
        );
        added.push(a);
        this.setState({
          assignmentDialogOpen: false,
          assignmentDialogQuestion: {} as Question,
        });
      } catch (error) {
        console.error(error);
        this.setState({
          snackbarIsOpen: true,
          snackbarMessage: this.props.gettext("An error occurred."),
        });
      }
    }

    let message = this.props.gettext("Added to ");
    if (added.length == 1) {
      message += added[0];
    } else {
      message += added.length + " " + this.props.gettext("assignments");
    }
    console.debug(message);
    this.setState(
      {
        snackbarIsOpen: true,
        snackbarMessage: message,
      },
      this.refreshFromDB,
    );
    return;
  };

  handleToggleFavourite = async (questionPK: number): Promise<void> => {
    if (!this.state.favouritesLoading) {
      const currentFavourites: number[] = Array.from(this.state.favourites);
      const _favourites: number[] = Array.from(this.state.favourites);

      if (_favourites.includes(questionPK)) {
        _favourites.splice(_favourites.indexOf(questionPK), 1);
      } else {
        _favourites.push(questionPK);
      }

      try {
        this.setState({ favouritesLoading: true });
        const data = await submitData(
          this.props.teacherURL,
          { favourite_questions: _favourites },
          "PUT",
        );
        this.setState({
          favourites: data["favourite_questions"],
          favouritesLoading: false,
          snackbarIsOpen: true,
          snackbarMessage: data["snackbar_message"],
        });
      } catch (error) {
        this.setState({
          favourites: currentFavourites,
          favouritesLoading: false,
          snackbarIsOpen: true,
          snackbarMessage: this.props.gettext("An error occurred."),
        });
      }
    }
    return;
  };

  categoryChips = (): JSX.Element => {
    if (this.state.categories.length > 0) {
      return (
        <div className="chip-container">
          <Typography
            use="caption"
            tag="div"
            style={{ fontWeight: "bold", paddingLeft: 3 }}
          >
            {this.props.gettext("Categories")}
          </Typography>
          {this.state.categories.map((c: string, i) => {
            if (c.length > 0) {
              const sc: string[] = [...this.state.selectedCategories];
              return (
                <Chip
                  selected={sc.indexOf(c) >= 0}
                  text={c}
                  key={i}
                  onClick={() => {
                    const index = sc.indexOf(c);
                    if (index >= 0) {
                      sc.splice(index, 1);
                    } else {
                      sc.push(c);
                    }
                    const _query = this.state.query
                      .replace(/category__title::\S+/gi, "")
                      .replace(/\s+/g, " ")
                      .trim();
                    this.setState(
                      {
                        selectedCategories: sc,
                        query:
                          sc
                            .map(
                              (_c: string) =>
                                "category__title::" + _c.replaceAll(" ", "_"),
                            )
                            .join(" ") +
                          " " +
                          _query,
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
                  selectedCategories: [],
                  query: this.state.query
                    .replace(/category__title::\S+/gi, "")
                    .replace(/\s+/g, " ")
                    .trim(),
                },
                this.handleSubmit,
              );
            }}
            style={{
              cursor: "pointer",
              display:
                this.state.selectedCategories.length > 0 ? "inline" : "none",
              fontSize: 18,
              verticalAlign: "middle",
            }}
          >
            close
          </i>
        </div>
      );
    }
    return <Fragment />;
  };

  difficultyChips = (): JSX.Element => {
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
          {this.state.difficulties.map((d: string, i) => {
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
                            .replace(/difficulty.label::\S+/gi, "")
                            .replace(/\s+/g, " ")
                            .trim(),
                        },
                        this.handleSubmit,
                      );
                    } else {
                      this.setState(
                        {
                          selectedDifficulty: d,
                          query:
                            "difficulty.label::" +
                            d.replaceAll(" ", "_") +
                            " " +
                            this.state.query,
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
                    .replace(/difficulty.label::\S+/gi, "")
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
    return <Fragment />;
  };

  disciplineChips = (): JSX.Element => {
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
          {this.state.disciplines.map((d: string, i) => {
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
                            .replace(/discipline.title::\S+/gi, "")
                            .replace(/\s+/g, " ")
                            .trim(),
                        },
                        this.handleSubmit,
                      );
                    } else {
                      this.setState(
                        {
                          selectedDiscipline: d,
                          query:
                            "discipline.title::" +
                            d.replaceAll(" ", "_") +
                            " " +
                            this.state.query,
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
                    .replace(/discipline::\S+/gi, "")
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
    return <Fragment />;
  };

  impactChips = (): JSX.Element => {
    if (this.state.impacts.length > 0) {
      return (
        <div class="chip-container">
          <Typography
            use="caption"
            tag="div"
            style={{ fontWeight: "bold", paddingLeft: 3 }}
          >
            {this.props.gettext("Peer impact levels")}
          </Typography>
          {this.state.impacts.map((d: string, i) => {
            if (d.length > 0) {
              return (
                <Chip
                  selected={this.state.selectedImpact == d}
                  text={d}
                  key={i}
                  onClick={() => {
                    if (this.state.selectedImpact) {
                      this.setState(
                        {
                          selectedImpact: "",
                          query: this.state.query
                            .replace(/peer_impact.label::\S+/gi, "")
                            .replace(/\s+/g, " ")
                            .trim(),
                        },
                        this.handleSubmit,
                      );
                    } else {
                      this.setState(
                        {
                          selectedImpact: d,
                          query:
                            "peer_impact.label::" +
                            d.replaceAll(" ", "_") +
                            " " +
                            this.state.query,
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
                  selectedImpact: "",
                  query: this.state.query
                    .replace(/peer_impact.label::\S+/gi, "")
                    .replace(/\s+/g, " ")
                    .trim(),
                },
                this.handleSubmit,
              );
            }}
            style={{
              cursor: "pointer",
              display: this.state.selectedImpact ? "inline" : "none",
              fontSize: 18,
              verticalAlign: "middle",
            }}
          >
            close
          </i>
        </div>
      );
    }
    return <Fragment />;
  };

  chips = (): JSX.Element => {
    return (
      <div>
        {this.disciplineChips()}
        {this.categoryChips()}
        {this.difficultyChips()}
        {this.impactChips()}
      </div>
    );
  };

  results = (): JSX.Element => {
    if (this.state.searching) {
      return <CircularProgress className="spinner" size="xlarge" />;
    }
    if (this.state.questions.length > 0) {
      return (
        <div id="results" style={{ marginTop: 20 }}>
          <Favourites.Provider value={this.state.favourites}>
            {this.state.questions.map((question, i) => {
              return (
                <SearchQuestionCard
                  featuredIconURL={this.props.featuredIconURL}
                  flagged={this.state.flagDialogQuestion}
                  gettext={this.props.gettext}
                  handleToggleAssignmentDialog={
                    this.handleToggleAssignmentDialog
                  }
                  handleToggleDialog={this.handleToggleDialog}
                  handleToggleFavourite={this.handleToggleFavourite}
                  handleToggleFlagDialog={this.handleToggleFlagDialog}
                  key={i}
                  question={question}
                />
              );
            })}
          </Favourites.Provider>
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
    return <Fragment />;
  };

  refreshFromDB = async (): Promise<void> => {
    // Load teacher data
    try {
      const data = await get(this.props.teacherURL);
      console.debug(data);
      this.setState({
        assignments: Object.prototype.hasOwnProperty.call(data, "assignments")
          ? data["assignments"]
          : [],
        favourites: Object.prototype.hasOwnProperty.call(
          data,
          "favourite_questions",
        )
          ? data["favourite_questions"]
          : [],
      });
    } catch (error) {
      console.error(error);
      this.setState({
        snackbarIsOpen: true,
        snackbarMessage: this.props.gettext(
          "Error.  Try refreshing this page.",
        ),
      });
    }
    // Load assignment form data
    try {
      const data = await get(this.props.assignmentFormMetaDataURL);
      console.debug(data);
      this.setState({
        assignmentFormMetaData: data as AssignmentForm,
      });
    } catch (error) {
      console.error(error);
      this.setState({
        snackbarIsOpen: true,
        snackbarMessage: this.props.gettext(
          "Error.  Try refreshing this page.",
        ),
      });
    }
    return;
  };

  componentDidMount(): void {
    this.refreshFromDB();
  }

  render(): JSX.Element {
    return (
      <div>
        <div id="search-form" style={{ width: 500 }}>
          <TextField
            autoFocus
            className="wide tight"
            outlined
            label={this.props.gettext("Type something...")}
            withLeadingIcon={<TextFieldIcon icon="search" theme="primary" />}
            withTrailingIcon={
              <TextFieldIcon
                style={
                  this.state.query ? { display: "block" } : { display: "none" }
                }
                tabIndex={0}
                icon="close"
                theme="primary"
                onClick={() =>
                  this.setState({
                    query: "",
                    questions: [],
                    categories: [],
                    difficulties: [],
                    disciplines: [],
                    impacts: [],
                    selectedCategories: [],
                    selectedDifficulty: "",
                    selectedDiscipline: "",
                    selectedImpact: "",
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
        <AssignmentDialog
          assignments={this.state.assignments.filter(
            (a: Assignment) => a.editable,
          )}
          checkIdURL={this.props.assignmentFormCheckIdURL}
          helpTexts={this.state.assignmentFormMetaData}
          handleSubmit={this.handleAssignmentSubmit}
          gettext={this.props.gettext}
          open={this.state.assignmentDialogOpen}
          onClose={() =>
            this.handleToggleAssignmentDialog({} as Question, false)
          }
          question={this.state.assignmentDialogQuestion}
        />
        <QuestionDialog
          gettext={this.props.gettext}
          open={this.state.dialogOpen}
          onClose={() => this.handleToggleDialog({} as Question)}
          question={this.state.dialogQuestion}
        />
        <QuestionFlagDialog
          callback={this.handleSubmit}
          gettext={this.props.gettext}
          open={this.state.flagDialogOpen}
          onClose={() =>
            this.handleToggleFlagDialog(
              {} as { title: string; pk: number },
              false,
            )
          }
          question={this.state.flagDialogQuestion}
          urls={this.props.questionFlagURLs}
        />
        <Snackbar
          show={this.state.snackbarIsOpen}
          onHide={() => this.setState({ snackbarIsOpen: false })}
          message={this.state.snackbarMessage}
          timeout={5000}
          actionHandler={() => {}} // eslint-disable-line @typescript-eslint/no-empty-function
          actionText="OK"
          dismissesOnAction={true}
        />
      </div>
    );
  }
}
