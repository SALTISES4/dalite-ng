import { Component, Fragment, h } from "preact";

import { get } from "../_ajax/ajax";

import { Breadcrumb, Heading } from "./heading";

type Assignment = {
  editable: boolean;
  pk: string;
  question_pks: number[]; // eslint-disable-line camelcase
  title: string;
  urls: {
    preview: string;
    update: string;
  };
};

type TeacherAccountAssignmentAppProps = {
  gettext: (a: string) => string;
  urls: {
    assignmentCreate: string;
    assignmentDistribute: string;
    assignmentList: string;
    assignmentSearch: string;
    generateReport: string;
  };
};

type TeacherAccountAssignmentAppState = {
  archived: number[];
  assignments: Assignment[];
  open: boolean;
  view: string;
};

export class TeacherAccountAssignmentApp extends Component<
  TeacherAccountAssignmentAppProps,
  TeacherAccountAssignmentAppState
> {
  state = {
    archived: [],
    assignments: [],
    open:
      localStorage.getItem("teacher-account-assignment-section") === "true",
    view: "",
  };

  refreshFromDB = async (): Promise<void> => {
    try {
      const data = await get(this.props.urls.assignmentList);
      console.debug(data);
      this.setState(
        {
          //archived: data["archived_assignments"],
          assignments: data["assignments"],
        },
        () => console.debug(this.state, this.props),
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

  searchAssignments = (): JSX.Element | undefined => {
    return (
      <Breadcrumb
        onClick={() =>
          (window.location.href = this.props.urls.assignmentSearch)
        }
        text={this.props.gettext("Search")}
      />
    );
  };

  generateReport = (): JSX.Element | undefined => {
    return (
      <Breadcrumb
        onClick={() => (window.location.href = this.props.urls.generateReport)}
        text={this.props.gettext("Generate report")}
      />
    );
  };

  breadcrumbs = (): JSX.Element | undefined => {
    if (this.state.view != "") {
      return (
        <Breadcrumb
          onClick={() => this.setState({ view: "" })}
          text={this.props.gettext("Return to list")}
        />
      );
    }
    if (this.state.view == "") {
      return (
        <Fragment>
          <Breadcrumb
            onClick={() =>
              (window.location.href = this.props.urls.assignmentCreate)
            }
            text={this.props.gettext("Create new")}
          />
          {this.manageArchived()}
          {this.searchAssignments()}
          {this.generateReport()}
        </Fragment>
      );
    }
    return;
  };

  content = (): JSX.Element | undefined => {
    if (this.state.open) {
      return (
        <Fragment>
          <div style={{ marginLeft: 48, marginTop: -6, marginBottom: 16 }}>
            {this.breadcrumbs()}
          </div>
        </Fragment>
      );
    }
  };
  //<AssignmentList assignments={this.state.assignments} />
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
                  "teacher-account-assignment-section",
                  `${this.state.open}`,
                );
              } catch (error) {
                console.error(error);
              }
            })
          }
          open={this.state.open}
          title={this.props.gettext("Assignments")}
        />
        {this.content()}
      </div>
    );
  }
}
