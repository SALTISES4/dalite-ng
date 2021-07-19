import { Component, Fragment, h } from "preact";

import { DragDropContext, Draggable, Droppable } from "react-beautiful-dnd";

import { Checkbox } from "@rmwc/checkbox";
import { FormField } from "@rmwc/formfield";
import { LinearProgress } from "@rmwc/linear-progress";
import { Snackbar } from "@rmwc/snackbar";

import "@rmwc/checkbox/node_modules/@material/checkbox/dist/mdc.checkbox.min.css";
import "@rmwc/formfield/node_modules/@material/form-field/dist/mdc.form-field.min.css";
import "@rmwc/linear-progress/node_modules/@material/linear-progress/dist/mdc.linear-progress.min.css";
import "@rmwc/snackbar/node_modules/@material/snackbar/dist/mdc.snackbar.min.css";

import { get, submitData } from "../_ajax/ajax";
import { QuestionCard, Favourites, User } from "./question.jsx";

class ToggleVisibleItems extends Component {
  toggleOrdering = () => {
    if (this.props.allowReordering) {
      return (
        <Fragment>
          <FormField theme="secondary">
            <label for="toggle-minimize">
              {this.props.gettext("Reorder questions?")}
            </label>
            <Checkbox
              aria-label={this.props.gettext(
                "Click to enable question reordering",
              )}
              checked={this.props.minimizeCards}
              id="toggle-minimize"
              onChange={this.props.handleMinimizeToggleClick}
              tabindex="0"
              title={this.props.gettext("Click to enable question reordering")}
            />
          </FormField>
        </Fragment>
      );
    }
  };

  showOptions = () => {
    if (!this.props.minimizeCards) {
      return (
        <Fragment>
          <FormField theme="secondary">
            <label for="toggle-images">
              {this.props.gettext("Show images")}
            </label>
            <Checkbox
              aria-label={this.props.gettext("Click to show question images")}
              checked={this.props.showImages}
              id="toggle-images"
              onChange={this.props.handleImageToggleClick}
              title={this.props.gettext("Click to show question images")}
            />
          </FormField>
          <FormField theme="secondary">
            <label for="toggle-answers">
              {this.props.gettext("Show choices")}
            </label>
            <Checkbox
              aria-label={this.props.gettext("Click to show answer choices")}
              checked={this.props.showChoices}
              id="toggle-answers"
              onChange={this.props.handleChoiceToggleClick}
              title={this.props.gettext("Click to show answer choices")}
            />
          </FormField>
        </Fragment>
      );
    }
  };

  render() {
    return (
      <div>
        {this.toggleOrdering()}
        {this.showOptions()}
      </div>
    );
  }
}

const getItemStyle = (isDragging, draggableStyle) => ({
  userSelect: "none",
  ...draggableStyle,
});

const getListStyle = (isDraggingOver) => ({
  background: isDraggingOver ? "var(--mdc-theme-primary)" : "lightgrey",
  padding: "10px 10px 1px",
});

export class AssignmentUpdateApp extends Component {
  state = {
    minimizeCards: false,
    favourites: [],
    showChoices: sessionStorage.answers == "block",
    showImages: sessionStorage.images == "block",
    questions: [],
    title: "",
    current: [],
    loaded: false,
    snackbarIsOpen: false,
    snackbarMessage: "",
  };

  handleChoiceToggleClick = () => {
    this.setState({ showChoices: !this.state.showChoices }, () => {
      sessionStorage.answers = this.state.showChoices ? "block" : "none";
    });
  };

  handleImageToggleClick = () => {
    this.setState({ showImages: !this.state.showImages }, () => {
      sessionStorage.images = this.state.showImages ? "block" : "none";
    });
  };

  handleMinimizeToggleClick = () => {
    this.setState({ minimizeCards: !this.state.minimizeCards });
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
      });
    } catch (error) {
      this.setState({
        favourites: currentFavourites,
        snackbarIsOpen: true,
        snackbarMessage: this.props.gettext("An error occurred."),
      });
    }
  };

  refreshFromDB = async () => {
    // Load assignment data
    try {
      const data = await get(this.props.assignmentURL);
      console.debug(data);
      this.setState({
        current: data["questions"],
        questions: data["questions"],
        title: data["title"],
        loaded: true,
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
  };

  componentDidMount() {
    this.refreshFromDB();
  }

  componentWillReceiveProps() {
    this.setState({ minimizeCards: false });
    this.refreshFromDB();
  }

  delete = async (pk) => {
    // Note that this is pk of through table object
    try {
      await submitData(this.props.assignmentQuestionURL + pk, {}, "DELETE");
      await this.refreshFromDB();

      this.setState({
        snackbarIsOpen: true,
        snackbarMessage: this.state.questions.map((q) => q.pk).includes(pk)
          ? this.props.gettext("An error occurred.")
          : this.props.gettext("Item removed."),
      });
    } catch (error) {
      console.error(error);
      this.setState({
        snackbarIsOpen: true,
        snackbarMessage: this.props.gettext("An error occurred."),
      });
    }
  };

  save = async () => {
    try {
      await submitData(
        this.props.assignmentURL,
        {
          title: this.state.title,
          questions: this.state.questions,
        },
        "PATCH",
      );
      this.setState({
        current: this.state.questions,
        snackbarIsOpen: true,
        snackbarMessage: this.props.gettext("Changes saved."),
      });
    } catch (error) {
      console.error(error);
      this.setState({
        questions: this.state.current,
        snackbarIsOpen: true,
        snackbarMessage: this.props.gettext("An error occurred."),
      });
    }
  };

  onDragEnd = (result) => {
    const _questions = Array.from(this.state.questions);
    const [dragged] = _questions.splice(result.source.index, 1);
    _questions.splice(result.destination.index, 0, dragged);
    _questions.forEach((el, i) => {
      el.rank = i;
    });
    this.setState({
      questions: _questions,
    });
    this.save();
  };

  toggles = () => {
    return (
      <ToggleVisibleItems
        allowReordering={this.state.questions.length > 1}
        gettext={this.props.gettext}
        showChoices={this.state.showChoices}
        showImages={this.state.showImages}
        minimizeCards={this.state.minimizeCards}
        handleChoiceToggleClick={this.handleChoiceToggleClick}
        handleImageToggleClick={this.handleImageToggleClick}
        handleMinimizeToggleClick={this.handleMinimizeToggleClick}
      />
    );
  };

  render() {
    if (!this.state.loaded) {
      return <LinearProgress determinate={false} />;
    }
    if (this.state.questions.length == 0) {
      return (
        <div>
          {this.props.gettext(
            "There are currently no questions in this assignment.  You can search for questions to add below.",
          )}
        </div>
      );
    }
    if (this.state.minimizeCards) {
      return (
        <div>
          {this.toggles()}
          <div style={{ marginBottom: "28px" }}>
            <DragDropContext
              nonce={this.props.nonce}
              onDragEnd={this.onDragEnd}
            >
              <Droppable droppableId="questions">
                {(provided, snapshot) => (
                  <div
                    {...provided.droppableProps}
                    ref={provided.innerRef}
                    style={getListStyle(snapshot.isDraggingOver)}
                  >
                    {this.state.questions.map((q, index) => (
                      <Draggable
                        key={`key-${q.question.pk}`}
                        draggableId={`id-${q.question.pk}`}
                        index={index}
                      >
                        {(provided, snapshot) => (
                          <div
                            ref={provided.innerRef}
                            {...provided.draggableProps}
                            {...provided.dragHandleProps}
                            style={getItemStyle(
                              snapshot.isDragging,
                              provided.draggableProps.style,
                            )}
                          >
                            <QuestionCard
                              question={q.question}
                              gettext={this.props.gettext}
                              showChoices={this.state.showChoices}
                              showImages={this.state.showImages}
                              minimizeCards={this.state.minimizeCards}
                            />
                          </div>
                        )}
                      </Draggable>
                    ))}
                    {provided.placeholder}
                  </div>
                )}
              </Droppable>
            </DragDropContext>
          </div>
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
    return (
      <div>
        <Favourites.Provider value={this.state.favourites}>
          <User.Provider value={this.props.user}>
            {this.toggles()}
            <div style={{ marginBottom: "28px" }}>
              {this.state.questions.map((q, i) => (
                <QuestionCard
                  cloneURL={this.props.questionCloneBaseURL}
                  editURL={this.props.questionEditBaseURL}
                  handleQuestionDelete={this.delete}
                  handleToggleFavourite={this.handleToggleFavourite}
                  key={i}
                  question={q.question}
                  rank={q.pk}
                  gettext={this.props.gettext}
                  showChoices={this.state.showChoices}
                  showImages={this.state.showImages}
                  minimizeCards={this.state.minimizeCards}
                  teacherURL={this.props.teacherURL}
                />
              ))}
            </div>
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
