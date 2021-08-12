import { Component, Fragment, h } from "preact";
import { useCallback, useState } from "preact/hooks";
import { triScale } from "../_theming/colours.js";
import { scaleThreshold } from "d3";
import { Favourites } from "./providers.js";
import { PlotConfusionMatrix } from "../_assignment/analytics.jsx";
import { get, submitData } from "../_ajax/ajax";

import { Button } from "@rmwc/button";
import {
  Card,
  CardActions,
  CardAction,
  CardActionIcons,
  CardActionButtons,
} from "@rmwc/card";
import { Checkbox } from "@rmwc/checkbox";
import {
  Dialog,
  DialogActions,
  DialogButton,
  DialogContent,
  DialogTitle,
} from "@rmwc/dialog";
import Icon from "@rmwc/icon";
import { IconButton } from "@rmwc/icon-button";
import { Select, SelectHelperText } from "@rmwc/select";
import { TextField, TextFieldHelperText } from "@rmwc/textfield";
import { Typography } from "@rmwc/typography";

import "@rmwc/button/node_modules/@material/button/dist/mdc.button.min.css";
import "@rmwc/card/node_modules/@material/card/dist/mdc.card.css";
import "@rmwc/checkbox/node_modules/@material/checkbox/dist/mdc.checkbox.min.css";
import "@rmwc/dialog/node_modules/@material/dialog/dist/mdc.dialog.min.css";
import "@rmwc/formfield/node_modules/@material/form-field/dist/mdc.form-field.min.css";
import "@rmwc/icon/icon.css";
import "@rmwc/icon-button/node_modules/@material/icon-button/dist/mdc.icon-button.min.css";
import "@rmwc/select/node_modules/@material/select/dist/mdc.select.min.css";
import "@rmwc/textfield/node_modules/@material/textfield/dist/mdc.textfield.css";
import "@rmwc/theme/node_modules/@material/theme/dist/mdc.theme.min.css";
import "@rmwc/typography/node_modules/@material/typography/dist/mdc.typography.min.css";

import {
  Assignment,
  AssignmentCreate,
  AssignmentForm,
  Question,
} from "./types";

triScale.reverse();

type AssigmentDialogProps = {
  assignments: Assignment[];
  checkIdURL: string;
  helpTexts: AssignmentForm;
  handleSubmit: (
    a: number,
    b: string[],
    c: {
      conclusion_page: string; // eslint-disable-line camelcase
      description: string;
      intro_page: string; // eslint-disable-line camelcase
      pk: string;
      title: string;
    },
  ) => Promise<void>;
  gettext: (a: string) => string;
  open: boolean;
  onClose: () => void;
  question: Question;
};

type AssignmentDialogState = {
  assignmentsSelected: string[];
  introduction: string;
  conclusion: string;
  create: boolean;
  description: string;
  pk: string;
  title: string;
};

export class AssignmentDialog extends Component<
  AssigmentDialogProps,
  AssignmentDialogState
> {
  state = {
    assignmentsSelected: [],
    introduction: "",
    conclusion: "",
    create: false,
    description: "",
    pk: "",
    title: "",
  };

  selectAssignment = (pk: string): void => {
    const _sa: string[] = Array.from(this.state.assignmentsSelected);
    const index = _sa.indexOf(pk);
    index < 0 ? _sa.push(pk) : _sa.splice(index, 1);
    this.setState({ assignmentsSelected: _sa });
  };

  checkUniqueness = async (evt: InputEvent): Promise<void> => {
    console.debug("Checking validity");

    // Model-level validation
    const target = evt.target as HTMLInputElement;
    const queryString = new URLSearchParams();
    queryString.append("id", target.value);
    const url = new URL(this.props.checkIdURL, window.location.origin);
    url.search = queryString.toString();
    try {
      const check = (await get(url.toString())) as { valid: boolean };
      console.debug(check);
      if (!check.valid) {
        target.setCustomValidity(
          this.props.gettext("This identifier has already been used."),
        );
      } else {
        target.setCustomValidity("");
      }
    } catch (error) {
      console.debug(error);
    }

    target.form?.checkValidity();
  };

  count = (): number =>
    this.props.assignments.filter(
      (a) => a.question_pks.indexOf(this.props.question.pk) < 0,
    ).length;

  goBack = (): JSX.Element => {
    if (this.state.create) {
      return (
        <Button ripple onClick={() => this.setState({ create: false })}>
          {this.props.gettext("Back")}
        </Button>
      );
    }
    return <Fragment />;
  };

  info = (): JSX.Element => {
    if (this.count() == 0) {
      return (
        <Info
          type="alert"
          text={this.props.gettext(
            `You have no editable assignments to which this
             question can be added, but you can create a new one below.  The
             question will be added to the new assignment automatically.`,
          )}
        />
      );
    }
    return (
      <Info
        text={this.props.gettext(
          `You can add this question to an existing assignment (if it is
           editable) or use this question to start a new assignment.`,
        )}
      />
    );
  };

  form = (): JSX.Element => {
    if (this.state.create || this.count() == 0) {
      return (
        <div style={{ maxWidth: 500 }}>
          <div style={{ marginBottom: 10 }}>
            <TextField
              autoFocus
              className="wide tight"
              label={this.props.gettext("Assignment title")}
              maxLength={200}
              name="title"
              onInput={(evt) => {
                this.setState({ title: evt.target.value });
              }}
              outlined
              required
              value={this.state.title}
            />
            <TextFieldHelperText persistent>
              {this.props.helpTexts.title}
            </TextFieldHelperText>
          </div>
          <div style={{ marginBottom: 10 }}>
            <TextField
              className="wide tight"
              label={this.props.gettext("Assignment identifier")}
              maxLength={100}
              name="identifier"
              onInput={(evt) => {
                this.setState({ pk: evt.target.value });
                this.checkUniqueness(evt);
              }}
              outlined
              pattern="[\d\w_-]+"
              required
              value={this.state.pk}
            />
            <TextFieldHelperText persistent>
              {this.props.helpTexts.identifier}
            </TextFieldHelperText>
          </div>
          <div style={{ marginBottom: 10 }}>
            <TextField
              fullwidth
              textarea
              label={this.props.gettext("Assignment description (optional)")}
              name="description"
              onInput={(evt) => {
                this.setState({ description: evt.target.value });
              }}
              outlined
              rows={4}
              value={this.state.description}
            />
            <TextFieldHelperText persistent>
              {this.props.helpTexts.description}
            </TextFieldHelperText>
          </div>
          <div style={{ marginBottom: 10 }}>
            <TextField
              textarea
              fullwidth
              label={this.props.gettext("Assignment introduction (optional)")}
              name="intro_page"
              onInput={(evt) => {
                this.setState({ introduction: evt.target.value });
              }}
              outlined
              rows={4}
              value={this.state.introduction}
            />
            <TextFieldHelperText persistent>
              {this.props.helpTexts.intro_page}
            </TextFieldHelperText>
          </div>
          <div style={{ marginBottom: 10 }}>
            <TextField
              textarea
              fullwidth
              label={this.props.gettext("Assignment conclusion (optional)")}
              name="conclusion_page"
              onInput={(evt) => {
                this.setState({ conclusion: evt.target.value });
              }}
              outlined
              rows={4}
              value={this.state.conclusion}
            />
            <TextFieldHelperText persistent>
              {this.props.helpTexts.conclusion_page}
            </TextFieldHelperText>
          </div>
        </div>
      );
    }
    return (
      <div>
        <div style={{ marginBottom: 10 }}>
          <IconButton
            icon="add"
            onClick={() => {
              this.setState({ assignmentsSelected: [], create: true });
            }}
            style={{
              padding: 0,
              marginLeft: 8,
              width: 24,
              height: 24,
              verticalAlign: "middle",
            }}
          />
          <Typography
            use="body2"
            tag="span"
            style={{ verticalAlign: "middle", marginLeft: 12 }}
          >
            {this.props.gettext("Create assignment")}
          </Typography>
        </div>
        {this.props.assignments
          .filter((a) => a.question_pks.indexOf(this.props.question.pk) < 0)
          .sort((x, y) => x.title.localeCompare(y.title))
          .map((a, i) => {
            return (
              <div key={i}>
                <Checkbox
                  checked={
                    (
                      Array.from(this.state.assignmentsSelected) as string[]
                    ).indexOf(a.pk) >= 0
                  }
                  onChange={() => this.selectAssignment(a.pk)}
                  label={`${a.title} (#${a.pk})`}
                  required={this.state.assignmentsSelected.length == 0}
                />
              </div>
            );
          })}
      </div>
    );
  };

  handleSubmit = async (evt: React.MouseEvent): Promise<void> => {
    const target = evt.target as HTMLInputElement;
    if (target.form?.checkValidity()) {
      if (this.state.create || this.count() == 0) {
        this.props.handleSubmit(this.props.question.pk, [], {
          intro_page: this.state.introduction,
          conclusion_page: this.state.conclusion,
          description: this.state.description,
          pk: this.state.pk,
          title: this.state.title,
        });
        this.setState({
          introduction: "",
          conclusion: "",
          description: "",
          pk: "",
          title: "",
        });
      } else {
        this.props.handleSubmit(
          this.props.question.pk,
          this.state.assignmentsSelected,
          {} as AssignmentCreate,
        );
        this.setState({ assignmentsSelected: [] });
      }
    }
  };

  shouldComponentUpdate(nextProps: AssigmentDialogProps): boolean {
    if (this.props.question != nextProps.question) {
      this.setState({
        assignmentsSelected: [],
        create: false,
        introduction: "",
        conclusion: "",
        description: "",
        pk: "",
        title: "",
      });
    }
    return true;
  }

  render(): JSX.Element {
    return (
      <Dialog open={this.props.open} onClose={this.props.onClose}>
        <DialogTitle>{this.props.question.title}</DialogTitle>
        <DialogContent>
          <div style={{ marginBottom: 16 }}>{this.info()}</div>
          <form
            id="assignment-form"
            method="POST"
            onKeyDown={(evt) => evt.stopPropagation()}
            onSubmit={(evt) => evt.preventDefault()}
          >
            {this.form()}
          </form>
        </DialogContent>
        <DialogActions>
          {this.goBack()}
          <DialogButton ripple action="accept" isDefaultAction>
            {this.props.gettext("Cancel")}
          </DialogButton>
          <DialogButton
            ripple
            type="submit"
            form="assignment-form"
            onClick={this.handleSubmit}
          >
            {this.props.gettext("Submit")}
          </DialogButton>
        </DialogActions>
      </Dialog>
    );
  }
}

type QuestionDialogProps = {
  gettext: (a: string) => string;
  open: boolean;
  onClose: () => void;
  question: Question;
};

export function QuestionDialog({
  gettext,
  open,
  onClose,
  question,
}: QuestionDialogProps): JSX.Element {
  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>
        #{question.pk} - {question.title}
      </DialogTitle>
      <DialogContent>
        <div style={{ marginBottom: 16 }}>
          <Info
            text={gettext(
              `The distribution of first and second choices along with the
            statistics for each possible outcome are shown in the figure
            below.  The most convincing rationales submitted by students
            (i.e. most selected be peers) are also listed for each answer
            choice.`,
            )}
          />
        </div>
        <Typography
          use="body2"
          tag="p"
          theme="text-secondary-on-background"
          style={{ fontWeight: "bold" }}
        >
          {gettext("Distribution of answer choices")}
        </Typography>
        <div style={{ margin: "16px 0px" }}>
          <PlotConfusionMatrix
            _matrix={question.matrix}
            freq={question.frequency}
            gettext={gettext}
            plot={open}
          />
        </div>
        <MostConvincingRationales
          gettext={gettext}
          rationales={question.most_convincing_rationales}
        />
      </DialogContent>
      <DialogActions>
        <DialogButton ripple action="accept" isDefaultAction>
          {gettext("Done")}
        </DialogButton>
      </DialogActions>
    </Dialog>
  );
}

type QuestionFlagDialogProps = {
  callback: () => Promise<void>;
  gettext: (a: string) => string;
  open: boolean;
  onClose: () => void;
  question: { title: string; pk: number };
  urls: string[];
};

type QuestionFlagDialogState = {
  reasons: string[];
  selectedReason: string;
};

export class QuestionFlagDialog extends Component<
  QuestionFlagDialogProps,
  QuestionFlagDialogState
> {
  state = {
    reasons: [],
    selectedReason: "",
  };

  handleSubmit = async (evt: React.MouseEvent): Promise<void> => {
    const target = evt.target as HTMLInputElement;
    if (target.form?.checkValidity()) {
      console.debug("Submit flag");
      try {
        await submitData(
          this.props.urls[1],
          { reason: this.state.selectedReason, id: this.props.question.pk },
          "POST",
        );
        this.props.callback();
      } catch (error) {
        console.debug(error);
      }
    }
  };

  refreshFromDB = async (): Promise<void> => {
    try {
      const data = (await get(this.props.urls[0])) as { reasons: string[] };
      console.debug(data);
      this.setState({
        reasons: data.reasons,
      });
    } catch (error) {
      console.debug(error);
    }
  };

  shouldComponentUpdate(nextProps: QuestionFlagDialogProps): boolean {
    if (this.props.question != nextProps.question) {
      this.setState({ selectedReason: "" });
    }
    return true;
  }

  componentDidMount(): void {
    this.refreshFromDB();
  }

  render(): JSX.Element {
    return (
      <Dialog open={this.props.open} onClose={this.props.onClose}>
        <DialogTitle>{this.props.question.title}</DialogTitle>
        <DialogContent>
          <div style={{ marginBottom: 16 }}>
            <Info
              text={this.props.gettext(
                `You can flag this question as problematic using the form below.
                This will immediately remove it from search results pending
                review.  It will not remove it from assignments.`,
              )}
            />
          </div>
          <form
            id="flag-question-form"
            method="POST"
            onKeyDown={(evt) => evt.stopPropagation()}
            onSubmit={(evt) => evt.preventDefault()}
          >
            <Select
              autoFocus
              onChange={(e: React.FormEvent<HTMLInputElement>) => {
                this.setState({
                  selectedReason: (e.target as HTMLInputElement).value,
                });
              }}
              options={this.state.reasons}
              outlined
              required
              style={{ appearance: "none" }}
              value={this.state.selectedReason}
            />
            <SelectHelperText persistent>
              {this.props.gettext(
                "Please select the reason for flagging this question.",
              )}
            </SelectHelperText>
          </form>
        </DialogContent>
        <DialogActions>
          <DialogButton ripple action="accept" isDefaultAction>
            {this.props.gettext("Cancel")}
          </DialogButton>
          <DialogButton
            ripple
            type="submit"
            form="flag-question-form"
            onClick={this.handleSubmit}
          >
            {this.props.gettext("Submit")}
          </DialogButton>
        </DialogActions>
      </Dialog>
    );
  }
}

function QuestionCardActionButtons(props) {
  return (
    <CardActionButtons>
      <Typography use="caption" tag="div">
        {props.gettext("Discipline")}:{" "}
        <span>
          {props.question.discipline
            ? props.question.discipline.title
            : props.gettext("Unlabelled")}
        </span>
      </Typography>
      <Typography use="caption" tag="div">
        {props.gettext("Categories")}:{" "}
        <span>
          {props.question.category
            ? props.question.category
                .map((c: { title: string }) => c.title)
                .join("; ")
            : props.gettext("Uncategorized")}
        </span>
      </Typography>
      <Typography use="caption" tag="div">
        {props.gettext("Student answers")}: {props.question.answer_count}
      </Typography>
    </CardActionButtons>
  );
}

type InfoProps = {
  className?: string;
  text: string;
  type?: string;
};

export function Info({
  className = "",
  text,
  type = "",
}: InfoProps): JSX.Element {
  return (
    <div className="info" style={{ display: "flex" }}>
      <Icon
        className={type}
        icon="info"
        iconOptions={{ strategy: "ligature", size: "small" }}
      />
      <Typography use="caption" tag="p" className={className}>
        {text}
      </Typography>
    </div>
  );
}

function MostConvincingRationales(props) {
  if (props.rationales) {
    return (
      <div>
        {props.rationales.map((r, i) => {
          return (
            <div key={i}>
              <Typography
                use="body2"
                tag="p"
                theme="text-secondary-on-background"
                // This field is bleached and safe
                // eslint-disable-next-line
                dangerouslySetInnerHTML={{ __html: `${r.label}. ${r.text}` }}
                style={{ fontWeight: "bold" }}
              />
              <ul>
                {r.most_convincing.map((a, i) => {
                  return (
                    <Fragment key={i}>
                      <Typography
                        use="body2"
                        tag="li"
                        theme="text-secondary-on-background"
                        style={{
                          marginBottom: 4,
                          marginTop: 8,
                          listStyleType: "disc",
                        }}
                      >
                        {a.rationale}
                      </Typography>
                      <Typography
                        className="meta"
                        use="caption"
                        tag="div"
                        dangerouslySetInnerHTML={{
                          __html: `${props.gettext("Shown:")} ${
                            a.times_shown
                          } &middot; ${props.gettext("Chosen:")} ${
                            a.times_chosen
                          } &middot; ${props.gettext("Rate:")} ${(
                            (a.times_chosen / a.times_shown) *
                            100
                          ).toFixed(1)}%`,
                        }}
                      />
                    </Fragment>
                  );
                })}
              </ul>
            </div>
          );
        })}
      </div>
    );
  }
  return <Fragment />;
}

function AnswerChoices(props) {
  const answerChoice = (ac) => {
    if (Object.prototype.hasOwnProperty.call(ac, "correct")) {
      if (ac.correct) {
        return (
          <Icon
            icon="check"
            iconOptions={{ strategy: "ligature", size: "xsmall" }}
            style={{
              verticalAlign: "middle",
              transform: "translate(3px, -1px)",
            }}
            theme="primary"
          />
        );
      }
    }
  };

  if (props.show) {
    if (
      Object.prototype.hasOwnProperty.call(props.question, "answerchoice_set")
    ) {
      return (
        <div className="question-answers">
          <ol type={props.question.answer_style == 0 ? "A" : "1"}>
            {props.question.answerchoice_set.map((ac, i) => {
              return (
                <Typography
                  key={i}
                  use="body1"
                  tag="li"
                  style={{ marginBottom: 2 }}
                >
                  <span
                    // This field is bleached and safe
                    // eslint-disable-next-line
                    dangerouslySetInnerHTML={{ __html: ac.text }}
                  />
                  {answerChoice(ac)}
                </Typography>
              );
            })}
          </ol>
        </div>
      );
    }
  }
  return <Fragment />;
}

type FeaturedProps = {
  collection: { title: string; url: string };
  gettext: (a: string) => string;
  url: string[];
};

type FeaturedState = {
  hovered: boolean;
};

class Featured extends Component<FeaturedProps, FeaturedState> {
  state = {
    hovered: false,
  };

  render() {
    return (
      <Fragment>
        <a
          href={this.props.collection.url}
          rel="noreferrer"
          target="_blank"
          title={`${this.props.gettext(
            "This question is part of featured content curated by SALTISE.  Click to open the associated collection ",
          )}'${this.props.collection.title}' in a new tab.`}
        >
          <div
            class="featured-icon"
            onMouseEnter={() => this.setState({ hovered: true })}
            onMouseLeave={() => this.setState({ hovered: false })}
            style={{
              backgroundImage: this.state.hovered
                ? `url('${this.props.url[1]}')`
                : `url('${this.props.url[0]}')`,
            }}
          />
        </a>
      </Fragment>
    );
  }
}

type FavouriteIconProps = {
  gettext: (a: string) => string;
  handleToggle: () => void;
  question: number;
};

function FavouriteIcon({
  gettext,
  handleToggle,
  question,
}: FavouriteIconProps) {
  return (
    <Favourites.Consumer>
      {(favourites: number[]) => {
        return (
          <CardAction
            checked={favourites.includes(question)}
            onClick={handleToggle}
            onIcon="favorite"
            icon="favorite_border"
            theme="primary"
            title={gettext(
              "Select or remove this question as one of your favourites",
            )}
          />
        );
      }}
    </Favourites.Consumer>
  );
}

type FlagIconProps = {
  checked: boolean;
  gettext: (a: string) => string;
  handleToggle: (a: { title: string; pk: number }, d?: boolean) => void;
  question: { title: string; pk: number };
};

function FlagIcon({
  checked,
  gettext,
  handleToggle,
  question,
}: FlagIconProps) {
  return (
    <CardAction
      checked={checked}
      icon="outlined_flag"
      iconOptions={{
        strategy: "custom",
        // eslint-disable-next-line react/display-name
        render: ({ content }) => (
          <span class="rmwc-icon material-icons-round mdc-icon-button__icon">
            {content}
          </span>
        ),
      }}
      onClick={() => handleToggle(question)}
      onIcon="flag"
      onIconOptions={{
        strategy: "custom",
        // eslint-disable-next-line react/display-name
        render: ({ content }) => (
          <span class="rmwc-icon material-icons-round mdc-icon-button__icon mdc-icon-button__icon--on">
            {content}
          </span>
        ),
      }}
      theme="primary"
      title={gettext("Flag question for removal")}
    />
  );
}

type AssignmentAddIconProps = {
  gettext: (a: string) => string;
  handleToggle: (a: Question) => void;
  question: Question;
};

function AssignmentAddIcon({
  gettext,
  handleToggle,
  question,
}: AssignmentAddIconProps) {
  return (
    <CardAction
      icon="add"
      onClick={() => handleToggle(question)}
      theme="primary"
      title={gettext("Add question to an assignment")}
    />
  );
}

type ImageProps = {
  alt?: string;
  image: string;
  show?: boolean;
};

function Image({ alt = "", image, show = true }: ImageProps) {
  if (image && show) {
    return (
      <Typography use="caption">
        <img alt={alt} class="question-image" src={image} />
      </Typography>
    );
  }
  return <Fragment />;
}

type VideoProps = {
  show?: boolean;
  url: string;
};

function Video({ show = true, url }: VideoProps) {
  if (url && show) {
    return (
      <object class="question-image" width="640" height="390" data={url} />
    );
  }
  return <Fragment />;
}

type QuestionCardHeaderProps = {
  featuredIconURL?: string[];
  gettext: (a: string) => string;
  question: Question;
};

function QuestionCardHeader({
  featuredIconURL,
  gettext,
  question,
}: QuestionCardHeaderProps) {
  const byline = () => {
    if (question.user?.username) {
      return (
        <div style={{ display: "inline" }}>
          <span>
            {gettext("by")} {question.user.username}
          </span>{" "}
          <span
            class="tag SALTISE"
            style={{
              display: question.user.saltise ? "inline" : "none",
            }}
          >
            SALTISE
          </span>{" "}
          <span
            class="tag EXPERT"
            style={{ display: question.user.expert ? "inline" : "none" }}
          >
            {gettext("EXPERT")}
          </span>{" "}
          {/*
          <span class="tag POWER">POWER USER</span>{" "}
          <span class="tag INFLUENCER">TOP CONTRIBUTOR</span>
          */}
        </div>
      );
    }
  };

  const featured = () => {
    if (featuredIconURL && question.featured && question.collections) {
      return (
        <Featured
          collection={question.collections[0]}
          gettext={gettext}
          url={featuredIconURL}
        />
      );
    }
  };

  return (
    <Fragment>
      <div>
        <Typography
          className="title"
          use="headline5"
          tag="h2"
          // This field is bleached and safe
          // eslint-disable-next-line
          dangerouslySetInnerHTML={{
            __html: question.title,
          }}
        />
        {featured()}
      </div>
      <Typography
        use="caption"
        tag="div"
        theme="text-secondary-on-background"
        style={{ marginBottom: 10 }}
      >
        #{question.pk} {byline()}
      </Typography>
    </Fragment>
  );
}

type QuestionCardBodyProps = {
  question: Question;
};

function QuestionCardBody({ question }: QuestionCardBodyProps) {
  return (
    <div>
      <Typography
        use="body1"
        tag="div"
        theme="text-secondary-on-background"
        // This field is bleached and safe
        // eslint-disable-next-line
        dangerouslySetInnerHTML={{ __html: question.text }}
      />
      <Image
        alt={question.image_alt_text}
        image={question.image}
        show={true}
      />
      <Video url={question.video_url} show={true} />
      <AnswerChoices question={question} show={true} />
    </div>
  );
}

type RatingsProps = {
  gettext: (a: string) => string;
  handleToggleDialog: (a: Question) => void;
  question: Question;
};

function Ratings({ gettext, handleToggleDialog, question }: RatingsProps) {
  const difficulty = () => {
    if (
      Object.prototype.hasOwnProperty.call(question.difficulty, "score") &&
      question.difficulty.score
    ) {
      const colourScale = scaleThreshold(triScale).domain([0.25, 0.5]);
      const color = colourScale(question.difficulty.score);
      const opacity = "30";
      const label = question.difficulty.label;
      return (
        <div
          class="rating"
          style={{
            backgroundColor: color + opacity,
            borderColor: color,
            cursor: "pointer",
          }}
          onClick={() => handleToggleDialog(question)}
        >
          <svg
            width="40"
            height="40"
            xmlns="http://www.w3.org/2000/svg"
            style={{ overflow: "visible" }}
          >
            <path
              id={`path-${question.pk}`}
              d="M -3 16 A 19 19 0 0 1 35 16"
              fill="transparent"
            />
            <text text-anchor="middle">
              {/* @ts-ignore: TS doesn't recognize textPath */}
              <textPath
                fill={color}
                startOffset="50%"
                style={{ fill: color, fontSize: 8 }}
                xmlnsXlink="http://www.w3.org/1999/xlink"
                xlinkHref={`#path-${question.pk}`}
              >
                {gettext("Click!")}
                {/* @ts-ignore: TS doesn't recognize textPath  */}
              </textPath>
            </text>
            <text
              text-anchor="middle"
              style={{ fill: color, fontSize: 8 }}
              x={15}
              y={42}
            >
              {gettext("Difficulty")}
            </text>
          </svg>
          <div
            class="label"
            style={{
              color,
            }}
          >
            {label}
          </div>
        </div>
      );
    }
  };

  const impact = () => {
    if (
      Object.prototype.hasOwnProperty.call(question.peer_impact, "score") &&
      question.peer_impact.score
    ) {
      const colourScale = scaleThreshold(triScale).domain([0.05, 0.25]);
      const color = colourScale(question.peer_impact.score);
      const opacity = "30";
      return (
        <div
          class="rating"
          style={{
            backgroundColor: color + opacity,
            borderColor: color,
          }}
        >
          <div class="label" style={{ color }}>
            {question.peer_impact.label}
          </div>
          <div class="title" style={{ color }}>
            {gettext("Peer impact")}
          </div>
        </div>
      );
    }
  };

  return (
    <div className="ratings">
      {difficulty()}
      {impact()}
    </div>
  );
}

type SearchQuestionCardProps = {
  featuredIconURL: string[];
  flagged: { title: string; pk: number };
  gettext: (a: string) => string;
  handleToggleAssignmentDialog: (a: Question, b?: boolean) => void;
  handleToggleDialog: (a: Question) => void;
  handleToggleFavourite: (a: number) => Promise<void>;
  handleToggleFlagDialog: (
    a: { title: string; pk: number },
    b?: boolean,
  ) => void;
  question: Question;
};

export function SearchQuestionCard({
  featuredIconURL,
  flagged,
  gettext,
  handleToggleAssignmentDialog,
  handleToggleDialog,
  handleToggleFavourite,
  handleToggleFlagDialog,
  question,
}: SearchQuestionCardProps): JSX.Element {
  return (
    <div>
      <Card className="question" style={{ position: "relative" }}>
        <Ratings
          gettext={gettext}
          question={question}
          handleToggleDialog={handleToggleDialog}
        />
        <div style={{ paddingRight: 40 }}>
          <QuestionCardHeader
            featuredIconURL={featuredIconURL}
            gettext={gettext}
            question={question}
          />
          <QuestionCardBody question={question} />
        </div>
        <CardActions>
          <QuestionCardActionButtons gettext={gettext} question={question} />
          <CardActionIcons>
            <FlagIcon
              checked={flagged ? question.pk == flagged.pk : false}
              gettext={gettext}
              handleToggle={handleToggleFlagDialog}
              question={{
                pk: question.pk,
                title: question.title,
              }}
            />
            <AssignmentAddIcon
              gettext={gettext}
              handleToggle={handleToggleAssignmentDialog}
              question={question}
            />
            <FavouriteIcon
              gettext={gettext}
              handleToggle={() => handleToggleFavourite(question.pk)}
              question={question.pk}
            />
          </CardActionIcons>
        </CardActions>
      </Card>
    </div>
  );
}

type ValidityCheckProps = {
  gettext: (a: string) => string;
  label: string;
  onClick: (() => void) | undefined;
  passes: boolean | undefined;
  pk: number;
  title: string;
};

function ValidityCheck({
  gettext,
  label,
  onClick,
  passes,
  pk,
  title,
}: ValidityCheckProps): JSX.Element {
  const colourScale = scaleThreshold(triScale).domain([0.25, 0.5]);
  const color = passes ? colourScale(0) : colourScale(1);
  const opacity = "30";
  return (
    <div
      class="rating"
      style={{
        backgroundColor: color + opacity,
        borderColor: color,
        cursor: passes || !onClick ? "default" : "pointer",
        margin: 8,
      }}
      onClick={passes ? undefined : onClick}
      title={title}
    >
      <svg
        width="40"
        height="40"
        xmlns="http://www.w3.org/2000/svg"
        style={{ overflow: "visible" }}
      >
        <path
          id={`validity-path-${pk}`}
          d="M -3 16 A 19 19 0 0 1 35 16"
          fill="transparent"
        />
        <text text-anchor="middle">
          {/* @ts-ignore: TS doesn't recognize textPath */}
          <textPath
            fill={color}
            startOffset="50%"
            style={{ fill: color, fontSize: 8 }}
            xmlnsXlink="http://www.w3.org/1999/xlink"
            xlinkHref={`#validity-path-${pk}`}
          >
            {passes || !onClick ? "" : gettext("Fix!")}
            {/* @ts-ignore: TS doesn't recognize textPath  */}
          </textPath>
        </text>
        {label.split(" ").map((word, i) => {
          return (
            <text
              key={i}
              text-anchor="middle"
              style={{ fill: color, fontSize: 8 }}
              x={15}
              y={42 + 9 * i}
            >
              {word}
            </text>
          );
        })}
      </svg>
      <div
        class="label"
        style={{
          color,
        }}
      >
        <Icon
          icon={passes ? "check" : "close"}
          iconOptions={{ strategy: "ligature", size: "small" }}
          style={{ verticalAlign: "middle" }}
        />
      </div>
    </div>
  );
}

type PreviewQuestionCardProps = {
  gettext: (a: string) => string;
  handleToggleDialog: (a: Question) => void;
  question: Question;
};

function useToggle(): {
  dialogOpen: boolean;
  toggleDialog: () => void;
} {
  const [dialogOpen, setValue] = useState(false);
  const toggleDialog = useCallback(() => {
    setValue(!dialogOpen);
  }, [dialogOpen]);
  return { dialogOpen, toggleDialog };
}

export function PreviewQuestionCard({
  gettext,
  handleToggleDialog,
  question,
}: PreviewQuestionCardProps): JSX.Element {
  const { dialogOpen: flagDialogOpen, toggleDialog: toggleFlaggedDialog } =
    useToggle();
  const {
    dialogOpen: ineditableDialogOpen,
    toggleDialog: toggleIneditableDialog,
  } = useToggle();

  const copy = () => {
    if (question.urls?.copy_question) {
      return (
        <DialogButton
          action="close"
          onClick={() => {
            window.open(question.urls?.copy_question);
          }}
        >
          {gettext("Copy")}
        </DialogButton>
      );
    }
  };

  const flagReasonsDialog = () => {
    if (question?.flag_reasons) {
      const body = (
        <Typography use="body1" tag="p">
          {gettext(
            "This question has been flagged by fellow members of the SALTISE community for the following reasons:",
          )}
          <ul>
            {question.flag_reasons
              .sort((a, b) => a.flag_reason__count - b.flag_reason__count)
              .map((fr, i) => (
                <li key={i} style={{ listStyleType: "disc" }}>
                  {fr.flag_reason__title} ({fr.flag_reason__count})
                </li>
              ))}
          </ul>
          {gettext(
            "Flags are reviewed by SALTISE administrators and removed once the issue has been resolved.  You can, however, copy this question, make the necessary changes and then use the new version in your assignments.",
          )}
        </Typography>
      );

      return (
        <Dialog open={flagDialogOpen} onClose={toggleFlaggedDialog}>
          <DialogTitle>{gettext("Question flags")}</DialogTitle>
          <DialogContent>{body}</DialogContent>
          <DialogActions>
            {copy()}
            <DialogButton action="accept" isDefaultAction>
              {gettext("Close")}
            </DialogButton>
          </DialogActions>
        </Dialog>
      );
    }
  };

  const ineditableDialog = () => {
    if (question?.is_editable == false) {
      const body = (
        <Typography use="body1" tag="p">
          {gettext(
            "This question cannot be edited, but you can make an editable copy.",
          )}
        </Typography>
      );

      return (
        <Dialog open={ineditableDialogOpen} onClose={toggleIneditableDialog}>
          <DialogTitle>{gettext("Question not editable")}</DialogTitle>
          <DialogContent>{body}</DialogContent>
          <DialogActions>
            {copy()}
            <DialogButton action="accept" isDefaultAction>
              {gettext("Close")}
            </DialogButton>
          </DialogActions>
        </Dialog>
      );
    }
  };

  return (
    <div>
      {flagReasonsDialog()}
      {ineditableDialog()}
      <Card className="question" style={{ position: "relative" }}>
        <Ratings
          gettext={gettext}
          question={question}
          handleToggleDialog={handleToggleDialog}
        />
        <div style={{ paddingRight: 40 }}>
          <QuestionCardHeader gettext={gettext} question={question} />
          <QuestionCardBody question={question} />
        </div>
        <CardActions>
          <QuestionCardActionButtons gettext={gettext} question={question} />
          <CardActionIcons>
            {[
              {
                include: true,
                label: question.is_not_flagged
                  ? gettext("Unflagged")
                  : gettext("Flagged"),
                onClick: toggleFlaggedDialog,
                passes: question.is_not_flagged,
                title: question.is_not_flagged
                  ? gettext("This question has not been flagged")
                  : gettext(
                      "This question has been flagged by a fellow member of the SALTISE community. Flags are reviewed by SALTISE administrators and removed once the issue has been resolved.",
                    ),
              },
              {
                include: question.type == "PI",
                label: gettext("Answer choices"),
                onClick: () => {
                  if (question.urls) {
                    if (question.is_editable) {
                      const tab = window.open(
                        question.urls.add_answer_choices,
                        "_blank",
                        "noopener,noreferrer",
                      );
                      if (tab) tab.focus();
                    } else {
                      toggleIneditableDialog();
                    }
                  }
                },
                passes: question.is_not_missing_answer_choices,
                title: question.is_not_missing_answer_choices
                  ? gettext("This question has enough answer choices")
                  : gettext(
                      "This question is missing answer choices. Click to add more.",
                    ),
              },
              {
                include: true,
                label: gettext("Expert rationale"),
                onClick: () => {
                  if (question.urls) {
                    const tab = window.open(
                      question.is_not_missing_answer_choices
                        ? question.urls.add_expert_rationales
                        : question.urls.add_answer_choices,
                      "_blank",
                      "noopener,noreferrer",
                    );
                    if (tab) tab.focus();
                  }
                },
                passes:
                  question.is_not_missing_expert_rationale &&
                  question.is_not_missing_answer_choices,
                title: question.is_not_missing_expert_rationale
                  ? gettext(
                      "This question has an expert rationale associated with all correct answer choices.",
                    )
                  : gettext(
                      "This question does not have an expert rationale for all correct answer choices.",
                    ),
              },
              {
                include: question.type == "PI",
                label: gettext("Sample answers"),
                onClick: () => {
                  if (question.urls) {
                    const tab = window.open(
                      question.is_not_missing_answer_choices
                        ? question.urls.add_sample_answers
                        : question.urls.add_answer_choices,
                      "_blank",
                      "noopener,noreferrer",
                    );
                    if (tab) tab.focus();
                  }
                },
                passes: question.is_not_missing_sample_answers,
                title: question.is_not_missing_sample_answers
                  ? gettext("This question has enough sample answers")
                  : gettext(
                      "This question does not have enough sample answers.  Click to add more.",
                    ),
              },
            ].map((el, i) => {
              if (el.include) {
                return (
                  <ValidityCheck
                    gettext={gettext}
                    key={i}
                    label={el.label}
                    onClick={el.onClick}
                    passes={el.passes}
                    pk={question.pk}
                    title={el.title}
                  />
                );
              }
            })}
          </CardActionIcons>
        </CardActions>
      </Card>
    </div>
  );
}
