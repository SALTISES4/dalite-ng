import { Component, h } from "preact";

import { Card } from "@rmwc/card";

import "@rmwc/card/node_modules/@material/card/dist/mdc.card.css";

export class QuestionCard extends Component {
  state = {
    loaded: false,
    question: null,
  };

  render() {
    return <Card />;
  }
}
