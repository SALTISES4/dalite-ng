import { Fragment, h } from "preact";

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

import { Info } from "../question";

import "@rmwc/icon-button/node_modules/@material/icon-button/dist/mdc.icon-button.min.css";
import "@rmwc/list/node_modules/@material/list/dist/mdc.list.css";

export type Assignment = {
  editable: boolean;
  pk: string;
  question_pks: number[]; // eslint-disable-line camelcase
  title: string;
  urls: {
    preview: string;
    update: string;
  };
};

type AssignmentListProps = {
  archived: Assignment[];
  assignments: Assignment[];
  gettext: (a: string) => string;
  handleToggleArchived: (a: Assignment) => Promise<void>;
  ownedAssignments: Assignment[];
  view: string;
};

export function AssignmentList({
  archived,
  assignments,
  gettext,
  handleToggleArchived,
  ownedAssignments,
  view,
}: AssignmentListProps): JSX.Element {
  console.debug(
    archived,
    assignments,
    gettext,
    handleToggleArchived,
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
    <Fragment>
      <div style={{ marginBottom: 8, maxWidth: 600 }}>{info()}</div>
      <List twoLine>
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
                  owned={ownedPks.includes(a.pk)}
                />
              </div>
            );
          })}
        <ListDivider />
      </List>
    </Fragment>
  );
}

type AssignmentListItemProps = {
  archived: boolean;
  assignment: Assignment;
  gettext: (a: string) => string;
  handleToggleArchived: (a: Assignment) => Promise<void>;
  owned: boolean;
};

function AssignmentListItem({
  archived,
  assignment,
  gettext,
  handleToggleArchived,
  owned,
}: AssignmentListItemProps): JSX.Element {
  const archiveIcon = (): JSX.Element | undefined => {
    return (
      <IconButton
        icon={
          owned && archived ? "unarchive" : owned ? "archive" : "remove_circle"
        }
        onClick={() => handleToggleArchived(assignment)}
        title={
          archived
            ? gettext("Unarchive this assignment.")
            : owned
            ? gettext("Archive this assignment to hide it.")
            : gettext("Unfollow this assignment.")
        }
      />
    );
  };

  const editIcon = (): JSX.Element | undefined => {
    if (owned && !archived && assignment.editable) {
      return (
        <IconButton
          icon="edit"
          onClick={() => (window.location.href = assignment.urls.update)}
          title={gettext("Edit or clone this assignment to make changes.")}
        />
      );
    }
  };

  const icons = () => {
    return (
      <div style={{ marginLeft: "auto" }}>
        {editIcon()}
        {archiveIcon()}
      </div>
    );
  };

  return (
    <Fragment>
      <ListDivider />
      <ListItem
        className={
          archived ? "question-list-item hatched" : "question-list-item"
        }
        onClick={() => (window.location.href = assignment.urls.preview)}
      >
        <ListItemGraphic
          icon={"assignment"}
          style={{ fontSize: 36 }}
          theme="primary"
        />
        <ListItemText>
          <ListItemPrimaryText
            style={{ fontWeight: "bold" }}
            theme="secondary"
          >
            {assignment.title}
          </ListItemPrimaryText>
          <ListItemSecondaryText theme="textHintOnBackground">
            {assignment.question_pks.length} {gettext("questions")}
          </ListItemSecondaryText>
        </ListItemText>
        {icons()}
      </ListItem>
    </Fragment>
  );
}
