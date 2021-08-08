import { Component, h } from "preact";

import { get } from "../_ajax/ajax";
import { QuestionDialog, PreviewQuestionCard } from "../_components/question";
import { Question } from "../_components/types";

import { CircularProgress } from "@rmwc/circular-progress";

import "@rmwc/circular-progress/circular-progress.css";

type QuestionPreviewAppProps = {
  gettext: (a: string) => string;
  urls: {
    load: string;
  };
};

type QuestionPreviewAppState = {
  dialogOpen: boolean;
  dialogQuestion: Question;
  loaded: boolean;
  questions: Question[];
};

export class QuestionPreviewApp extends Component<
  QuestionPreviewAppProps,
  QuestionPreviewAppState
> {
  state = {
    dialogOpen: false,
    dialogQuestion: {} as Question,
    loaded: false,
    questions: [] as Question[],
  };

  handleToggleDialog = (question: Question): void => {
    console.debug("handleToggleDialog called");
    this.setState({
      dialogOpen: !this.state.dialogOpen,
      dialogQuestion: question,
    });
    return;
  };

  refreshFromDB = async (): Promise<void> => {
    // Load all question data
    try {
      const data = await get(this.props.urls.load);
      console.debug(data);
      this.setState({
        loaded: true,
        questions: data as Question[],
      });
    } catch (error) {
      console.error(error);
    }
  };

  componentDidMount() {
    this.refreshFromDB();
  }

  render(): JSX.Element {
    if (!this.state.loaded) {
      return <CircularProgress className="spinner" size="xlarge" />;
    }
    return (
      <div>
        <QuestionDialog
          gettext={this.props.gettext}
          open={this.state.dialogOpen}
          onClose={() => this.handleToggleDialog({} as Question)}
          question={this.state.dialogQuestion}
        />
        {this.state.questions.map((question, i) => {
          return (
            <PreviewQuestionCard
              gettext={this.props.gettext}
              key={i}
              handleToggleDialog={this.handleToggleDialog}
              question={question}
            />
          );
        })}
      </div>
    );
  }
}
