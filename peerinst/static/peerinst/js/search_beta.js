import { get } from "./_ajax/ajax.js";
import { Component, h } from "preact";

import { Card, CardPrimaryAction } from "@rmwc/card";
import { CircularProgress } from "@rmwc/circular-progress";
import { TextField } from "@rmwc/textfield";
import { Typography } from "@rmwc/typography";

import "@rmwc/card/node_modules/@material/card/dist/mdc.card.css";
import "@rmwc/circular-progress/circular-progress.css";
import "@rmwc/textfield/node_modules/@material/textfield/dist/mdc.textfield.css";
import "@rmwc/typography/node_modules/@material/typography/dist/mdc.typography.min.css";

/*
.mdc-text-field--outlined .mdc-text-field__input {height: 100%}
*/

export class QuestionCard extends Component {
  state = {
    loaded: false,
  };

  byline = () => {
    if (Object.prototype.hasOwnProperty.call(this.props.question, "user")) {
      return <span>by {this.props.question.user.username}</span>;
    }
  };

  render() {
    return (
      <Card>
        <CardPrimaryAction>
          <div>
            <Typography use="headline6" tag="h2">
              {this.props.question.title}
            </Typography>
            <Typography
              use="subtitle2"
              tag="h3"
              theme="text-secondary-on-background"
              style={{ marginTop: "-1rem" }}
            >
              #{this.props.question.id} {this.byline()}
            </Typography>
            <Typography
              use="body1"
              tag="div"
              theme="text-secondary-on-background"
            >
              <div
                // eslint-disable-next-line
                dangerouslySetInnerHTML={{ __html: this.props.question.text }}
              />
            </Typography>
          </div>
        </CardPrimaryAction>
      </Card>
    );
  }
}

export class SearchApp extends Component {
  state = {
    query: "",
    questions: [],
    meta: {},
    searching: false,
  };

  handleSubmit = async () => {
    const queryString = new URLSearchParams();
    queryString.append("search_string", this.state.query);
    const url = new URL(this.props.url, window.location.origin);
    url.search = queryString;

    try {
      this.setState({ searching: true });
      const data = await get(url);
      console.debug(data);
      this.setState(
        {
          meta: data.meta,
          questions: data.results,
          searching: false,
        },
        () => console.debug(this.state.questions, this.state.meta),
      );
    } catch (error) {
      // Snackbar
      console.debug(error);
    }
  };

  results = () => {
    if (this.state.searching) {
      return <CircularProgress size="large" />;
    }
    if (this.state.questions) {
      return (
        <div id="results">
          {this.state.questions.map((question, i) => {
            return <QuestionCard question={question} key={i} />;
          })}
        </div>
      );
    }
  };

  render() {
    return (
      <div>
        <div id="search-form">
          <TextField
            outlined
            label="Contains words..."
            withLeadingIcon="search"
            onInput={(evt) => {
              this.setState({ query: evt.target.value }, this.handleSubmit);
            }}
            value={this.state.query}
          />
        </div>
        {this.results()}
      </div>
    );
  }
}
