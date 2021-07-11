import { Component, h } from "preact";

import { get, submitData } from "./_ajax/ajax.js";

import {
  QuestionDialog,
  QuestionFlagDialog,
  SearchQuestionCard,
} from "./_components/question.js";
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

export class SearchApp extends Component {
  state = {
    query: "",
    questions: [],
    categories: [],
    dialogOpen: false,
    dialogQuestion: {},
    difficulties: [],
    disciplines: [],
    favourites: [],
    flagDialogOpen: false,
    flagDialogQuestion: {},
    impacts: [],
    searching: false,
    selectedCategories: [],
    selectedDifficulty: "",
    selectedDiscipline: "",
    selectedImpact: "",
    snackbarIsOpen: false,
    snackbarMessage: "",
  };

  handleToggleDialog = (question) => {
    this.setState({
      dialogOpen: !this.state.dialogOpen,
      dialogQuestion: question,
    });
  };

  handleToggleFlagDialog = (question) => {
    console.debug(
      `Toggle flag for question: ${
        question ? question.pk + question.title : ""
      }`,
    );
    this.setState({
      flagDialogOpen: !this.state.flagDialogOpen,
      flagDialogQuestion: question
        ? { title: question.title, pk: question.pk }
        : {},
    });
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
        this.setState({
          categories: data.meta.categories,
          difficulties: data.meta.difficulties,
          disciplines: data.meta.disciplines,
          impacts: data.meta.impacts,
          questions: data.results,
          searching: false,
        });
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
  };

  handleToggleFavourite = async (questionPK) => {
    const currentFavourites = Array.from(this.state.favourites);
    const _favourites = Array.from(this.state.favourites);

    if (_favourites.includes(questionPK)) {
      _favourites.splice(_favourites.indexOf(questionPK), 1);
    } else {
      _favourites.push(questionPK);
    }

    try {
      const data = await submitData(
        this.props.teacherURL,
        { favourite_questions: _favourites },
        "PUT",
      );
      this.setState({
        favourites: data["favourite_questions"],
        snackbarIsOpen: true,
        snackbarMessage: data["snackbar_message"],
      });
    } catch (error) {
      this.setState({
        favourites: currentFavourites,
        snackbarIsOpen: true,
        snackbarMessage: this.props.gettext("An error occurred."),
      });
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
                  selected={this.state.selectedCategories.indexOf(c) >= 0}
                  text={c}
                  key={i}
                  onClick={() => {
                    const sc = [...this.state.selectedCategories];
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
                        query: `${sc
                          .map(
                            (_c) =>
                              `category__title::${_c.replaceAll(" ", "_")}`,
                          )
                          .join(" ")} ${_query}`,
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
                  selectedCategories: "",
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
                          query: `discipline.title::${d.replaceAll(
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
  };

  impactChips = () => {
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
          {this.state.impacts.map((d, i) => {
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
                          query: `peer_impact.label::${d.replaceAll(
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
  };

  chips = () => {
    return (
      <div>
        {this.disciplineChips()}
        {this.categoryChips()}
        {this.difficultyChips()}
        {this.impactChips()}
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
          <Favourites.Provider value={this.state.favourites}>
            {this.state.questions.map((question, i) => {
              return (
                <SearchQuestionCard
                  featuredIconURL={this.props.featuredIconURL}
                  gettext={this.props.gettext}
                  handleToggleFavourite={this.handleToggleFavourite}
                  key={i}
                  question={question}
                  staticURL={this.props.staticURL}
                  toggleDialog={this.handleToggleDialog}
                  toggleFlagDialog={this.handleToggleFlagDialog}
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
  };

  refreshFromDB = async () => {
    // Load favourites
    try {
      const data = await get(this.props.teacherURL);
      console.debug(data);
      this.setState({
        favourites: data["favourite_questions"],
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
  };

  componentDidMount() {
    this.refreshFromDB();
  }

  render() {
    return (
      <div>
        <div id="search-form" style={{ width: 500 }}>
          <TextField
            autofocus
            class="wide tight"
            outlined
            label={this.props.gettext("Type something...")}
            withLeadingIcon={<TextFieldIcon icon="search" theme="primary" />}
            withTrailingIcon={
              <TextFieldIcon
                style={
                  this.state.query ? { display: "block" } : { display: "none" }
                }
                tabIndex="0"
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
            theme="secondary"
          />
          <TextFieldHelperText persistent>
            {this.props.gettext(
              "You can search for keywords in question and answer texts, by username, by question id, by category, and by discipline.",
            )}
          </TextFieldHelperText>
        </div>
        {this.chips()}
        {this.results()}
        <QuestionDialog
          gettext={this.props.gettext}
          open={this.state.dialogOpen}
          onClose={this.handleToggleDialog}
          question={this.state.dialogQuestion}
        />
        <QuestionFlagDialog
          callback={this.handleSubmit}
          gettext={this.props.gettext}
          open={this.state.flagDialogOpen}
          onClose={this.handleToggleFlagDialog}
          question={this.state.flagDialogQuestion}
          urls={this.props.questionFlagURLs}
        />
        <Snackbar
          show={this.state.snackbarIsOpen}
          onHide={(evt) => this.setState({ snackbarIsOpen: false })}
          message={this.state.snackbarMessage}
          timeout={5000}
          actionHandler={() => {}}
          actionText="OK"
          dismissesOnAction={true}
        />
      </div>
    );
  }
}
