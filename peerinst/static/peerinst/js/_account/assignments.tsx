import { Component, Fragment, h } from "preact";

import { get, submitData } from "../_ajax/ajax";

import { LinearProgress } from "@rmwc/linear-progress";

import { Breadcrumb, Heading } from "./heading";

import {
  Assignment,
  AssignmentList,
} from "../_components/lists/assignmentList";

import "@rmwc/linear-progress/node_modules/@material/linear-progress/dist/mdc.linear-progress.min.css";

type TeacherAccountAssignmentAppProps = {
  gettext: (a: string) => string;
  lti: {
    launchURL: string;
    consumerKey: string;
    sharedSecret: string;
    teacherHash: string;
  };
  urls: {
    assignmentCreate: string;
    assignmentList: string;
    assignmentSearch: string;
    assignmentUpdate: string;
    generateReport: string;
  };
};

type TeacherAccountAssignmentAppState = {
  archived: Assignment[];
  assignments: Assignment[];
  loaded: boolean;
  open: boolean;
  ownedAssignments: Assignment[];
  view: string;
  waitingOnResponse: boolean;
};

export class TeacherAccountAssignmentApp extends Component<
  TeacherAccountAssignmentAppProps,
  TeacherAccountAssignmentAppState
> {
  state = {
    archived: [],
    assignments: [],
    loaded: false,
    open:
      localStorage.getItem("teacher-account-assignment-section") === "true",
    ownedAssignments: [],
    view: "",
    waitingOnResponse: true,
  };

  archived = (
    assignments: Assignment[],
    owned: Assignment[],
  ): Assignment[] => {
    console.debug("Inferring archived assignments");
    const assignmentSet = new Set<string>(assignments.map((a) => a.pk));
    const archived = owned.filter((x) => !assignmentSet.has(x.pk));
    console.debug(assignmentSet, owned, archived);

    return archived;
  };

  updateView = (): void => {
    console.debug("Updating view");
    if (this.state.view == "archived" && this.state.archived.length == 0) {
      this.setState({ view: "" });
      return;
    }
  };

  handleToggleArchived = async (a: Assignment): Promise<void> => {
    if (!this.state.waitingOnResponse) {
      console.debug("Toggle archived");
      console.debug(a);

      const _assignments: Assignment[] = Array.from(this.state.assignments);
      const _archived: Assignment[] = Array.from(this.state.archived);

      if (_archived.map((_a) => _a.pk).includes(a.pk)) {
        _assignments.push(a);
      } else {
        _assignments.splice(_assignments.indexOf(a), 1);
      }

      try {
        this.setState({ waitingOnResponse: true });
        const data = await submitData(
          this.props.urls.assignmentList,
          { assignment_pks: _assignments.map((a) => a.pk) },
          "PUT",
        );
        console.debug(data);
        const archived = this.archived(
          data["assignments"],
          data["owned_assignments"],
        );
        this.setState(
          {
            archived,
            assignments: data["assignments"],
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
      const data = await get(this.props.urls.assignmentList);
      console.debug(data);

      this.setState({
        archived: this.archived(
          data["assignments"],
          data["owned_assignments"],
        ),
        assignments: data["assignments"],
        loaded: true,
        ownedAssignments: data["owned_assignments"],
        waitingOnResponse: false,
      });
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
        text={this.props.gettext("Index")}
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
    if (this.state.open && !this.state.loaded) {
      return <LinearProgress determinate={false} style={{ width: 600 }} />;
    }
    if (this.state.open) {
      return (
        <Fragment>
          <div style={{ marginLeft: 48, marginTop: -6, marginBottom: 16 }}>
            {this.breadcrumbs()}
          </div>
          <AssignmentList
            archived={this.state.archived}
            assignments={this.state.assignments}
            disabled={this.state.waitingOnResponse}
            gettext={this.props.gettext}
            lti={this.props.lti}
            handleToggleArchived={this.handleToggleArchived}
            ownedAssignments={this.state.ownedAssignments}
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
