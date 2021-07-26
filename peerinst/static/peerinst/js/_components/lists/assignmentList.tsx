import { Component, createRef, Fragment, h } from "preact";

import {
  Dialog,
  DialogActions,
  DialogButton,
  DialogContent,
  DialogTitle,
} from "@rmwc/dialog";
import { IconButton } from "@rmwc/icon-button";
import {
  List,
  ListDivider,
  ListItem,
  ListItemGraphic,
  ListItemText,
  ListItemPrimaryText,
  ListItemSecondaryText,
} from "@rmwc/list";
import { Menu, MenuItem, MenuSurfaceAnchor } from "@rmwc/menu";
import { Typography } from "@rmwc/typography";

import { CopyBox } from "../clipboard";
import { Info } from "../question";

import "@rmwc/button/node_modules/@material/button/dist/mdc.button.min.css";
import "@rmwc/dialog/node_modules/@material/dialog/dist/mdc.dialog.min.css";
import "@rmwc/icon-button/node_modules/@material/icon-button/dist/mdc.icon-button.min.css";
import "@rmwc/list/node_modules/@material/list/dist/mdc.list.css";
import "@rmwc/menu/node_modules/@material/menu/dist/mdc.menu.css";
import "@rmwc/menu/node_modules/@material/menu-surface/dist/mdc.menu-surface.css";
import "@rmwc/typography/node_modules/@material/typography/dist/mdc.typography.min.css";

type BasicQuestion = {
  answer_count: number; // eslint-disable-line camelcase
  answerchoice_set: { correct: boolean; text: string }[]; // eslint-disable-line camelcase

  category: { title: string }[];
  collaborators?: string[];
  discipline: { title: string };
  frequency: {
    first_choice: Record<string, number>; // eslint-disable-line camelcase
    second_choice: Record<string, number>; // eslint-disable-line camelcase
  };
  image: string;
  image_alt_text: string; // eslint-disable-line camelcase
  matrix: { easy: number; hard: number; tricky: number; peer: number };
  pk: number;
  text: string;
  title: string;
  user: { username: string } | null;
};

export type Assignment = {
  editable: boolean;
  is_valid: boolean; // eslint-disable-line camelcase
  pk: string;
  questions?: {
    assignment: string;
    pk: number;
    question: BasicQuestion;
    rank: number;
  }[];
  question_pks: number[]; // eslint-disable-line camelcase
  title: string;
  urls: {
    copy: string;
    distribute: string;
    fix: string;
    preview: string;
    update: string;
  };
};

type AssignmentListProps = {
  archived: Assignment[];
  assignments: Assignment[];
  gettext: (a: string) => string;
  handleToggleArchived: (a: Assignment) => Promise<void>;
  lti: {
    launchURL: string;
    consumerKey: string;
    sharedSecret: string;
    teacherHash: string;
  };
  ownedAssignments: Assignment[];
  view: string;
};

export function AssignmentList({
  archived,
  assignments,
  gettext,
  handleToggleArchived,
  lti,
  ownedAssignments,
  view,
}: AssignmentListProps): JSX.Element {
  console.debug(
    archived,
    assignments,
    gettext,
    handleToggleArchived,
    lti,
    ownedAssignments,
    view,
  );
  const archivedPks = archived.map((a) => a.pk);
  const ownedPks = ownedAssignments.map((a) => a.pk);

  const sort = (a: Assignment, b: Assignment): number => {
    // Triple sort on owned, then editable, then title
    if (+ownedPks.includes(b.pk) == +ownedPks.includes(a.pk)) {
      if (a.editable == b.editable || !ownedPks.includes(b.pk)) {
        return a.title.localeCompare(b.title);
      }
      return +b.editable - +a.editable;
    }
    return +ownedPks.includes(b.pk) - +ownedPks.includes(a.pk);
  };

  const info = (): JSX.Element | undefined => {
    if (assignments.length == 0 && view == "") {
      return (
        <Info
          className="large"
          text={gettext(
            "You are not currently following any assignments.  You can create one, search for one in the database, or unarchive an old one.",
          )}
          type="alert"
        />
      );
    }
    if (view == "") {
      return (
        <Info
          className="large"
          text={gettext(
            "This is the list of assignments you have authored or are currently following, and for which reports will be available.  You can archive or unfollow any assignments you are no longer using.",
          )}
          type="tip"
        />
      );
    }
    if (view == "archived") {
      return (
        <Info
          className="large"
          text={gettext(
            "This is the list of assignments you have authored and archived.",
          )}
          type="tip"
        />
      );
    }
    return;
  };

  return (
    <div>
      <div style={{ marginBottom: 8, maxWidth: 600 }}>{info()}</div>
      <List
        className="assignment-list"
        twoLine
        style={{ position: "relative" }}
      >
        {assignments
          .concat(archived)
          .sort(sort)
          .filter((a) => {
            return view == "archived"
              ? archivedPks.includes(a.pk)
              : !archivedPks.includes(a.pk);
          })
          .map((a: Assignment, i: number) => {
            return (
              <div key={i}>
                <AssignmentListItem
                  archived={archivedPks.includes(a.pk)}
                  assignment={a}
                  gettext={gettext}
                  handleToggleArchived={handleToggleArchived}
                  lti={lti}
                  owned={ownedPks.includes(a.pk)}
                />
              </div>
            );
          })}
        <ListDivider />
      </List>
    </div>
  );
}

type AssignmentListItemProps = {
  archived: boolean;
  assignment: Assignment;
  gettext: (a: string) => string;
  handleToggleArchived: (a: Assignment) => Promise<void>;
  lti: {
    launchURL: string;
    consumerKey: string;
    sharedSecret: string;
    teacherHash: string;
  };
  owned: boolean;
};

type AssingmentListItemState = {
  dialogIsOpen: boolean;
  menuIsOpen: boolean;
};

class AssignmentListItem extends Component<
  AssignmentListItemProps,
  AssingmentListItemState
> {
  state = {
    dialogIsOpen: false,
    menuIsOpen: false,
  };

  menuRef = createRef();

  archiveIcon = (): JSX.Element | undefined => {
    return (
      <IconButton
        icon={
          this.props.owned && this.props.archived
            ? "unarchive"
            : this.props.owned
            ? "archive"
            : "remove_circle"
        }
        onClick={() => this.props.handleToggleArchived(this.props.assignment)}
        title={
          this.props.archived
            ? this.props.gettext("Unarchive this assignment.")
            : this.props.owned
            ? this.props.gettext("Archive this assignment to hide it.")
            : this.props.gettext("Unfollow this assignment.")
        }
      />
    );
  };

  editIcon = (): JSX.Element | undefined => {
    const edit = this.props.owned && this.props.assignment.editable;
    if (!this.props.archived) {
      return (
        <IconButton
          icon={edit ? "edit" : "file_copy"}
          onClick={() =>
            (window.location.href = edit
              ? this.props.assignment.urls.update
              : this.props.assignment.urls.copy)
          }
          title={
            edit
              ? this.props.gettext("Edit this assignment to make changes.")
              : this.props.gettext("Copy this assignment to make changes.")
          }
        />
      );
    }
  };

  distributeIcon = (): JSX.Element | undefined => {
    if (
      !this.props.archived &&
      this.props.assignment.is_valid &&
      this.props.assignment?.questions &&
      this.props.assignment.questions.length > 0
    ) {
      return (
        <IconButton
          icon="share"
          onClick={() => this.setState({ menuIsOpen: true })}
          title={this.props.gettext(
            "Distribute this assignment to one of your groups.",
          )}
        />
      );
    }
  };

  icons = () => {
    return (
      <div style={{ marginLeft: "auto" }}>
        {this.distributeIcon()}
        {this.editIcon()}
        {this.archiveIcon()}
      </div>
    );
  };

  caption = (): JSX.Element => {
    if (this.props.assignment.is_valid) {
      return (
        <span>
          {this.props.assignment.question_pks.length}{" "}
          {this.props.gettext("questions")}
        </span>
      );
    }
    return (
      <span style={{ color: "var(--mdc-theme-error)" }}>
        {this.props.gettext("There is a problem with this assignment.")}
      </span>
    );
  };

  ltiDialog = (): JSX.Element | undefined => {
    if (
      this.props.assignment?.questions &&
      this.props.assignment.questions.length > 0
    ) {
      return (
        <Dialog
          open={this.state.dialogIsOpen}
          onClose={() => this.setState({ dialogIsOpen: false })}
        >
          <DialogTitle>{this.props.assignment.title}</DialogTitle>
          <DialogContent>
            <Info
              className="large"
              text={this.props.gettext(
                `Use the following information to configure the LTI tool in
             your Learning Management System (e.g. Moodle, OpenEdx):`,
              )}
              type="tip"
            />

            <div style={{ marginLeft: 26, marginTop: 10 }}>
              <Typography
                use="body2"
                tag="div"
                style={{ fontWeight: "bold", marginBottom: 4 }}
              >
                {this.props.gettext("LTI Launch URL")}
              </Typography>
              <Typography use="body2" tag="div">
                <CopyBox gettext={this.props.gettext}>
                  <ul style={{ paddingLeft: 8 }}>
                    <li>{this.props.lti.launchURL}</li>
                  </ul>
                </CopyBox>
              </Typography>
            </div>
            <div style={{ marginLeft: 26, marginTop: 10 }}>
              <Typography
                use="body2"
                tag="div"
                style={{ fontWeight: "bold", marginBottom: 4 }}
              >
                {this.props.gettext("LTI Consumer Key")}
              </Typography>
              <Typography use="body2" tag="div">
                <CopyBox gettext={this.props.gettext}>
                  <ul style={{ paddingLeft: 8 }}>
                    <li>{this.props.lti.consumerKey}</li>
                  </ul>
                </CopyBox>
              </Typography>
            </div>
            <div style={{ marginBottom: 24, marginLeft: 26, marginTop: 10 }}>
              <Typography
                use="body2"
                tag="div"
                style={{ fontWeight: "bold", marginBottom: 4 }}
              >
                {this.props.gettext("LTI Shared Secret")}
              </Typography>
              <Typography use="body2" tag="div">
                <CopyBox gettext={this.props.gettext}>
                  <ul style={{ paddingLeft: 8 }}>
                    <li>{this.props.lti.sharedSecret}</li>
                  </ul>
                </CopyBox>
              </Typography>
            </div>

            <Info
              className="large"
              text={this.props.gettext(
                `To import assignment questions, copy and paste the text
                 below the question title into the Custom Parameters box of your
                 LTI tool:`,
              )}
              type="tip"
            />
            {this.props.assignment.questions.map((q, i): JSX.Element => {
              return (
                <div key={i} style={{ marginLeft: 26, marginTop: 10 }}>
                  <Typography
                    key={i}
                    use="body2"
                    tag="div"
                    style={{ fontWeight: "bold", marginBottom: 4 }}
                  >
                    Q{i + 1}. {q.question.title}
                  </Typography>
                  <Typography use="body2" tag="div">
                    <CopyBox gettext={this.props.gettext}>
                      <ul style={{ paddingLeft: 8 }}>
                        <li>assignment_id={this.props.assignment.pk}</li>
                        <li>question_id={q.question.pk}</li>
                        <li>teacher_id={this.props.lti.teacherHash}</li>
                      </ul>
                    </CopyBox>
                  </Typography>
                </div>
              );
            })}
          </DialogContent>
          <DialogActions>
            <DialogButton
              ripple
              action="accept"
              isDefaultAction
              theme="primary"
            >
              {this.props.gettext("OK")}
            </DialogButton>
          </DialogActions>
        </Dialog>
      );
    }
  };

  render() {
    return (
      <Fragment>
        <ListDivider />
        {this.ltiDialog()}
        <MenuSurfaceAnchor
          style={{
            position: "absolute",
            right: 0,
          }}
        >
          <Menu
            open={this.state.menuIsOpen}
            onClose={() => this.setState({ menuIsOpen: false })}
          >
            <MenuItem onClick={() => this.setState({ dialogIsOpen: true })}>
              {this.props.gettext("Distribute via LMS (e.g. Moodle)")}
            </MenuItem>
            <MenuItem
              onClick={() =>
                (window.location.href = this.props.assignment.urls.distribute)
              }
            >
              {this.props.gettext("Distribute via myDALITE")}
            </MenuItem>
          </Menu>
        </MenuSurfaceAnchor>
        <ListItem
          className={
            this.props.archived
              ? "assignment-list-item hatched"
              : "assignment-list-item"
          }
        >
          <ListItemGraphic
            icon={this.props.assignment.is_valid ? "assignment" : "report"}
            onClick={() =>
              (window.location.href = this.props.assignment.is_valid
                ? this.props.assignment.urls.preview
                : this.props.assignment.urls.fix)
            }
            style={{ cursor: "pointer", fontSize: 36 }}
            theme={this.props.assignment.is_valid ? "primary" : "error"}
          />
          <ListItemText>
            <ListItemPrimaryText
              onClick={() =>
                (window.location.href = this.props.assignment.is_valid
                  ? this.props.assignment.urls.preview
                  : this.props.assignment.urls.fix)
              }
              style={{ cursor: "pointer", fontWeight: "bold" }}
              theme={this.props.assignment.is_valid ? "secondary" : "error"}
            >
              {this.props.assignment.title}
            </ListItemPrimaryText>
            <ListItemSecondaryText theme="textHintOnBackground">
              {this.caption()}
            </ListItemSecondaryText>
          </ListItemText>
          {this.icons()}
        </ListItem>
      </Fragment>
    );
  }
}
