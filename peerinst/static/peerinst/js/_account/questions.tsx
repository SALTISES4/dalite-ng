import { Component, Fragment, h } from "preact";

import { get, submitData } from "../_ajax/ajax";

import { LinearProgress } from "@rmwc/linear-progress";

import { Breadcrumb, Heading } from "./heading";
import {
  ListedQuestion,
  QuestionList,
} from "../_components/lists/questionList";

import "@rmwc/linear-progress/node_modules/@material/linear-progress/dist/mdc.linear-progress.min.css";

type TeacherAccountQuestionAppProps = {
  gettext: (a: string) => string;
  urls: { questionCreate: string; questionEdit: string; questionList: string };
};

type TeacherAccountQuestionAppState = {
  archived: number[];
  deleted: number[];
  loaded: boolean;
  open: boolean;
  questions: ListedQuestion[];
  shared: ListedQuestion[];
  view: string;
  waitingOnResponse: boolean;
};

export class TeacherAccountQuestionApp extends Component<
  TeacherAccountQuestionAppProps,
  TeacherAccountQuestionAppState
> {
  state = {
    archived: [],
    deleted: [],
    loaded: false,
    open: localStorage.getItem("teacher-account-question-section") === "true",
    questions: [],
    shared: [],
    view: "",
    waitingOnResponse: true,
  };

  updateView = (): void => {
    console.debug("Updating view");
    if (this.state.view == "archived" && this.state.archived.length == 0) {
      this.setState({ view: "" });
      return;
    }
    if (this.state.view == "deleted" && this.state.deleted.length == 0) {
      this.setState({ view: "" });
      return;
    }
  };

  handleToggleArchived = async (pk: number): Promise<void> => {
    if (!this.state.waitingOnResponse) {
      console.debug("Toggle archived");
      console.debug(pk);

      const _archived: number[] = Array.from(this.state.archived);
      if (_archived.includes(pk)) {
        _archived.splice(_archived.indexOf(pk), 1);
      } else {
        _archived.push(pk);
      }
      try {
        this.setState({ waitingOnResponse: true });
        const data = await submitData(
          this.props.urls.questionList,
          { archived_questions: _archived },
          "PUT",
        );
        console.debug(data);
        this.setState(
          {
            archived: data["archived_questions"],
            waitingOnResponse: false,
          },
          this.updateView,
        );
      } catch (error) {
        console.error(error);
        this.setState({ waitingOnResponse: false });
      }
    }
  };

  handleToggleDeleted = async (pk: number): Promise<void> => {
    if (!this.state.waitingOnResponse) {
      console.debug("Toggle deleted");
      console.debug(pk);

      const _deleted: number[] = Array.from(this.state.deleted);
      if (_deleted.includes(pk)) {
        _deleted.splice(_deleted.indexOf(pk), 1);
      } else {
        _deleted.push(pk);
      }
      try {
        this.setState({ waitingOnResponse: true });
        const data = await submitData(
          this.props.urls.questionList,
          { deleted_questions: _deleted },
          "PUT",
        );
        console.debug(data);
        this.setState(
          {
            deleted: data["deleted_questions"],
            waitingOnResponse: false,
          },
          this.updateView,
        );
      } catch (error) {
        console.error(error);
        this.setState({ waitingOnResponse: false });
      }
    }
  };

  refreshFromDB = async (): Promise<void> => {
    try {
      const data = await get(this.props.urls.questionList);
      console.debug(data);
      this.setState(
        {
          archived: data["archived_questions"],
          deleted: data["deleted_questions"],
          loaded: true,
          questions: data["questions"],
          shared: data["shared_questions"],
          waitingOnResponse: false,
        },
        () => console.debug(this.state),
      );
    } catch (error) {
      console.error(error);
    }
  };

  manageArchived = (): JSX.Element | undefined => {
    if (this.state.archived.length > 0) {
      return (
        <Breadcrumb
          onClick={() => this.setState({ view: "archived" })}
          text={this.props.gettext("Manage archived")}
        />
      );
    }
  };

  manageDeleted = (): JSX.Element | undefined => {
    if (this.state.deleted.length > 0) {
      return (
        <Breadcrumb
          onClick={() => this.setState({ view: "deleted" })}
          text={this.props.gettext("Manage deleted")}
        />
      );
    }
  };

  breadcrumbs = (): JSX.Element | undefined => {
    if (this.state.view != "") {
      return (
        <Fragment>
          <Breadcrumb
            onClick={() => this.setState({ view: "" })}
            text={this.props.gettext("Return to list")}
          />
        </Fragment>
      );
    }
    if (this.state.view == "") {
      return (
        <Fragment>
          <Breadcrumb
            onClick={() =>
              (window.location.href = this.props.urls.questionCreate)
            }
            text={this.props.gettext("Create new")}
          />
          {this.manageDeleted()}
          {this.manageArchived()}
        </Fragment>
      );
    }
    return;
  };

  content = (): JSX.Element | undefined => {
    if (this.state.open && !this.state.loaded) {
      return <LinearProgress determinate={false} style={{ width: 600 }} />;
    }
    if (this.state.open) {
      return (
        <Fragment>
          <div style={{ marginLeft: 48, marginTop: -6, marginBottom: 16 }}>
            {this.breadcrumbs()}
          </div>
          <QuestionList
            archived={this.state.archived}
            deleted={this.state.deleted}
            disabled={this.state.waitingOnResponse}
            editURL={this.props.urls.questionEdit}
            gettext={this.props.gettext}
            handleToggleArchived={this.handleToggleArchived}
            handleToggleDeleted={this.handleToggleDeleted}
            questions={this.state.questions}
            shared={this.state.shared}
            view={this.state.view}
          />
        </Fragment>
      );
    }
  };

  componentDidMount(): void {
    this.refreshFromDB();
  }

  render(): JSX.Element {
    return (
      <div>
        <Heading
          gettext={this.props.gettext}
          onClick={() =>
            this.setState({ open: !this.state.open }, () => {
              try {
                localStorage.setItem(
                  "teacher-account-question-section",
                  `${this.state.open}`,
                );
              } catch (error) {
                console.error(error);
              }
            })
          }
          open={this.state.open}
          title={this.props.gettext("Questions")}
        />
        {this.content()}
      </div>
    );
  }
}
