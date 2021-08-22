import { Component, h } from "preact";

import { LinearProgress } from "@rmwc/linear-progress";
import { Select, SelectHelperText } from "@rmwc/select";
import { Snackbar } from "@rmwc/snackbar";
import {
  TextField,
  TextFieldHelperText,
  TextFieldIcon,
} from "@rmwc/textfield";

import "@rmwc/linear-progress/node_modules/@material/linear-progress/dist/mdc.linear-progress.min.css";
import "@rmwc/snackbar/node_modules/@material/snackbar/dist/mdc.snackbar.min.css";
import "@rmwc/textfield/node_modules/@material/textfield/dist/mdc.textfield.min.css";
import "@rmwc/textfield/node_modules/@material/floating-label/dist/mdc.floating-label.min.css";
import "@rmwc/textfield/node_modules/@material/notched-outline/dist/mdc.notched-outline.min.css";
import "@rmwc/textfield/node_modules/@material/line-ripple/dist/mdc.line-ripple.min.css";
import "@rmwc/select/node_modules/@material/select/dist/mdc.select.min.css";

import { get, submitData } from "../_ajax/ajax";
import { QuestionCard, Favourites, User } from "./question.jsx";

export class SearchBar extends Component {
  state = {
    searchTerms: "",
  };

  render() {
    return (
      <div>
        <div style={{ marginBottom: "20px", marginTop: "20px" }}>
          <TextField
            withLeadingIcon={<TextFieldIcon icon="search" theme="secondary" />}
            withTrailingIcon={
              <TextFieldIcon
                tabIndex="0"
                icon="close"
                onClick={() =>
                  this.setState(
                    { searchTerms: "" },
                    this.props.handleSubmit(
                      new Event("init", { type: "init" }),
                    ),
                  )
                }
                theme="primary"
                style={
                  this.state.searchTerms.length > 0
                    ? {}
                    : { opacity: "0", pointerEvents: "none" }
                }
              />
            }
            label={this.props.gettext("Type search terms")}
            value={this.state.searchTerms}
            onInput={(evt) => {
              this.setState({ searchTerms: evt.target.value });
            }}
            onKeyPress={(evt) => {
              this.props.handleSubmit(evt, this.state.searchTerms);
            }}
            theme="secondary"
            outlined
          />
          <TextFieldHelperText persistent>
            {this.props.gettext(
              "The quick add search engine checks question meta data for the complete phrase only.  You can also search on username to find all content from a certain contributor.  Search results are filtered to remove questions already part of this assignment.",
            )}
          </TextFieldHelperText>
        </div>
      </div>
    );
  }
}

export class SearchDbApp extends Component {
  /* Expects a paginated response from server */
  state = {
    disciplines: [],
    favourites: [],
    questions: [],
    searching: false,
    selectedDiscipline: this.props.defaultDiscipline,
    snackbarIsOpen: false,
    snackbarMessage: "",
  };

  componentDidMount() {
    this.refreshFromDB();
  }

  refreshFromDB = async () => {
    // Load disicplines
    try {
      const data = await get(this.props.disciplineURL);
      console.debug(data);
      this.setState({
        disciplines: data,
        selectedDiscipline: this.props.defaultDiscipline,
      });
    } catch (error) {
      console.error(error);
      this.setState({
        snackbarIsOpen: true,
        snackbarMessage: this.props.gettext(
          "An error occurred.  Try refreshing this page.",
        ),
      });
    }
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
          "Could not load favourites.  Try refreshing this page.",
        ),
      });
    }
    this.handleSubmit(new Event("init", { type: "init" }));
  };

  handleSubmit = (evt, searchTerms = "") => {
    if (
      (searchTerms != "" && evt.type === "change") |
      (evt.type === "init") |
      (evt.key === "Enter")
    ) {
      this.setState({ searching: true, questions: [] }, async () => {
        console.debug("Searching...");
        const queryString = new URLSearchParams({
          assignment_id: this.props.assignment,
          discipline: this.state.selectedDiscipline,
          search_string: searchTerms,
        });
        const url = `${this.props.searchURL}?${queryString.toString()}`;

        try {
          const data = await get(url);
          console.debug(data);
          if (data["count"] > 0) {
            this.setState({
              questions: data["results"].map((d, i) => {
                return {
                  question: d,
                  rank: i,
                };
              }),
              searching: false,
            });
          } else {
            this.setState({
              searching: false,
              snackbarIsOpen: evt.type !== "init",
              snackbarMessage: this.props.gettext("No questions match query."),
            });
          }
        } catch (error) {
          console.error(error);
          this.setState({
            snackbarIsOpen: true,
            snackbarMessage: this.props.gettext(
              "An error occurred.  Try refreshing this page.",
            ),
          });
        }
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

  add = async (pk, i) => {
    try {
      await submitData(
        this.props.assignmentQuestionURL,
        { assignment: this.props.assignment, question_pk: pk },
        "POST",
      );
      const _questions = this.state.questions;
      _questions.splice(i, 1);
      this.setState({
        questions: _questions,
        snackbarIsOpen: true,
        snackbarMessage: this.props.gettext("Item added."),
      });
      this.props.callback();
    } catch (error) {
      console.error(error);
      this.setState({
        snackbarIsOpen: true,
        snackbarMessage: this.props.gettext("An error occurred."),
      });
    }
  };

  searchBar = () => {
    if (this.state.searching) {
      return (
        <LinearProgress determinate={false} style={{ marginTop: "40px" }} />
      );
    }
    return (
      <div style={{ marginBottom: "20px" }}>
        <SearchBar
          gettext={this.props.gettext}
          handleSubmit={this.handleSubmit}
        />
        <Select
          value={this.state.selectedDiscipline}
          onChange={(e) => {
            this.setState(
              {
                selectedDiscipline: e.target.value,
              },
              this.handleSubmit(e),
            );
          }}
          outlined
          options={this.state.disciplines.map((d) => {
            return { label: d.title, value: d.pk };
          })}
          style={{ appearance: "none" }}
        />
        <SelectHelperText persistent>
          {this.props.gettext(
            "Search results will only include questions in the selected discipline.",
          )}
        </SelectHelperText>
      </div>
    );
  };

  render() {
    return (
      <div>
        <Favourites.Provider value={this.state.favourites}>
          <User.Provider value={this.props.user}>
            {this.searchBar()}
            {this.state.questions.map((q, i) => (
              <QuestionCard
                cloneURL={this.props.questionCloneBaseURL}
                editURL={this.props.questionEditBaseURL}
                handleQuestionDelete={null}
                handleQuestionAdd={this.add}
                handleToggleFavourite={this.handleToggleFavourite}
                key={i}
                question={q.question}
                rank={i}
                gettext={this.props.gettext}
                showChoices={true}
                showImages={true}
                minimizeCards={false}
              />
            ))}
          </User.Provider>
        </Favourites.Provider>
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
