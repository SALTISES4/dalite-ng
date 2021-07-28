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

export type ListedQuestion = {
  answer_count: number; // eslint-disable-line camelcase
  is_valid: boolean; // eslint-disable-line camelcase
  pk: number;
  title: string;
  type: string;
};

type QuestionListProps = {
  archived: number[];
  deleted: number[];
  editURL: string;
  gettext: (a: string) => string;
  handleToggleArchived: (a: number) => Promise<void>;
  handleToggleDeleted: (a: number) => Promise<void>;
  questions: ListedQuestion[];
  shared: ListedQuestion[];
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
  const sharedPks = shared.map((sq) => sq.pk);
  const byPk = (a: ListedQuestion, b: ListedQuestion) => b.pk - a.pk;

  const info = (): JSX.Element | undefined => {
    if (view == "") {
      return (
        <Info
          className="large"
          text={gettext(
            "This is the list of questions for which you are the primary author or a co-author.",
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
            "This is the list of questions for which you are the primary author or a co-author and that you have archived.",
          )}
          type="tip"
        />
      );
    }
    if (view == "deleted") {
      return (
        <Info
          className="large"
          text={gettext(
            "This is the list of questions for which you are the primary author and that you have marked for deletion.  From time to time, questions marked for deletion that are not part of any assignment and that have no associated student answers will be removed from the database.  Questions that have been included in any assignment or have student answers cannot be deleted, only archived.",
          )}
          type="tip"
        />
      );
    }
  };

  if (
    questions.filter(
      (q) => !deleted.includes(q.pk) && !archived.includes(q.pk),
    ).length == 0 &&
    view == ""
  ) {
    return (
      <Info
        className="large"
        text={gettext(
          "You do not have any questions (or they are all archived/deleted).  You can create one using the link above.",
        )}
        type="alert"
      />
    );
  }
  return (
    <Fragment>
      <div style={{ marginBottom: 8, maxWidth: 600 }}>{info()}</div>
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
          .map((q: ListedQuestion, i: number) => {
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
                  shared={sharedPks.includes(q.pk)}
                />
              </div>
            );
          })}
        <ListDivider />
      </List>
    </Fragment>
  );
}

type QuestionListItemProps = {
  archived: boolean;
  deleted: boolean;
  editURL: string;
  gettext: (a: string) => string;
  handleToggleArchived: (a: number) => Promise<void>;
  handleToggleDeleted: (a: number) => Promise<void>;
  question: ListedQuestion;
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
          icon={
            question.is_valid
              ? question.type == "RO"
                ? "chat"
                : "question_answer"
              : "report"
          }
          style={{ fontSize: 36 }}
          theme={question.is_valid ? "primary" : "error"}
        />
        <ListItemText>
          <ListItemPrimaryText
            style={{ fontWeight: "bold" }}
            theme={question.is_valid ? "secondary" : "error"}
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
