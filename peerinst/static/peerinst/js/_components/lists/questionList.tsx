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
import { Typography } from "@rmwc/typography";

import { Info } from "../question";

import "@rmwc/icon-button/node_modules/@material/icon-button/dist/mdc.icon-button.min.css";
import "@rmwc/list/node_modules/@material/list/dist/mdc.list.css";
import "@rmwc/typography/node_modules/@material/typography/dist/mdc.typography.min.css";

type QuestionListProps = {
  archived: number[];
  deleted: number[];
  editURL: string;
  gettext: (a: string) => string;
  handleToggleArchived: (a: number) => Promise<void>;
  handleToggleDeleted: (a: number) => Promise<void>;
  questions: {
    answer_count: number; // eslint-disable-line camelcase
    pk: number;
    title: string;
    type: string;
  }[];
  shared: {
    answer_count: number; // eslint-disable-line camelcase
    pk: number;
    title: string;
    type: string;
  }[];
  view: string;
};

export function QuestionList({
  archived,
  deleted,
  editURL,
  gettext,
  handleToggleArchived,
  handleToggleDeleted,
  questions,
  shared,
  view,
}: QuestionListProps): JSX.Element {
  const byPk = (a, b) => b.pk - a.pk;

  if (
    questions.filter(
      (q) => !deleted.includes(q.pk) && !archived.includes(q.pk),
    ).length == 0 &&
    view == ""
  ) {
    return (
      <div style={{ margin: "10px 0px" }}>
        <Typography use="body1" tag="p">
          <Info
            size={12}
            text={gettext(
              "You do not have any questions (or they are all archived/deleted).  You can create one using the link above.",
            )}
            type="tip"
          />
        </Typography>
      </div>
    );
  }
  return (
    <List twoLine>
      {questions
        .sort(byPk)
        .concat(shared.sort(byPk))
        .filter((q) => {
          return view == "deleted"
            ? deleted.includes(q.pk)
            : view == "archived"
            ? archived.includes(q.pk) && !deleted.includes(q.pk)
            : !deleted.includes(q.pk) && !archived.includes(q.pk);
        })
        .map(
          (
            q: {
              answer_count: number; // eslint-disable-line camelcase
              pk: number;
              title: string;
              type: string;
            },
            i: number,
          ) => {
            return (
              <div key={i}>
                <QuestionListItem
                  archived={archived.includes(q.pk)}
                  deleted={deleted.includes(q.pk)}
                  editURL={editURL}
                  gettext={gettext}
                  handleToggleArchived={handleToggleArchived}
                  handleToggleDeleted={handleToggleDeleted}
                  question={q}
                  shared={shared.map((sq) => sq.pk).includes(q.pk)}
                />
              </div>
            );
          },
        )}
      <ListDivider />
    </List>
  );
}

type QuestionListItemProps = {
  archived: boolean;
  deleted: boolean;
  editURL: string;
  gettext: (a: string) => string;
  handleToggleArchived: (a: number) => Promise<void>;
  handleToggleDeleted: (a: number) => Promise<void>;
  question: {
    answer_count: number; // eslint-disable-line camelcase
    pk: number;
    title: string;
    type: string;
  };
  shared: boolean;
};

function QuestionListItem({
  archived,
  deleted,
  editURL,
  gettext,
  handleToggleArchived,
  handleToggleDeleted,
  question,
  shared,
}: QuestionListItemProps): JSX.Element {
  const deleteIcon = (): JSX.Element | undefined => {
    if (!shared) {
      return (
        <IconButton
          icon={deleted ? "restore_from_trash" : "delete"}
          onClick={() => handleToggleDeleted(question.pk)}
          style={{ color: "#757575" }}
          title={
            deleted
              ? gettext("Undelete this question.")
              : gettext(
                  "Delete this question.  If there are no student answers associated  with it, deleting removes it from search results but won't prevent other teachers from using it if they have already included it in their assignments.",
                )
          }
        />
      );
    }
  };

  const archiveIcon = (): JSX.Element | undefined => {
    if (!deleted) {
      return (
        <IconButton
          icon={archived ? "unarchive" : "archive"}
          onClick={() => handleToggleArchived(question.pk)}
          style={{ color: "#757575" }}
          title={
            archived
              ? gettext("Unarchive this question.")
              : gettext("Archive this question to hide it.")
          }
        />
      );
    }
  };

  const editIcon = (): JSX.Element | undefined => {
    if (!deleted && !archived) {
      return (
        <IconButton
          icon="edit"
          onClick={() => (window.location.href = editURL + question.pk)}
          style={{ color: "#757575", marginRight: -12 }}
          title={gettext("Edit or clone this question to make changes.")}
        />
      );
    }
  };

  const icons = () => {
    return (
      <div style={{ marginLeft: "auto" }}>
        {deleteIcon()}
        {archiveIcon()}
        {editIcon()}
      </div>
    );
  };

  return (
    <Fragment>
      <ListDivider />
      <ListItem
        className={
          archived || deleted
            ? "question-list-item hatched"
            : "question-list-item"
        }
      >
        <ListItemGraphic
          icon={question.type == "RO" ? "chat" : "question_answer"}
          style={{ fontSize: 36 }}
          theme="primary"
        />
        <ListItemText>
          <ListItemPrimaryText
            style={{ fontWeight: "bold" }}
            theme="secondary"
          >
            {question.pk}: {question.title}
          </ListItemPrimaryText>
          <ListItemSecondaryText theme="textHintOnBackground">
            {question.answer_count} {gettext("student answers")}
          </ListItemSecondaryText>
        </ListItemText>
        {icons()}
      </ListItem>
    </Fragment>
  );
}
