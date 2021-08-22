import { Component, createRef, h } from "preact";
import { createPortal } from "preact/compat";

import { IconButton } from "@rmwc/icon-button";
import { Snackbar } from "@rmwc/snackbar";

import "@rmwc/icon-button/node_modules/@material/icon-button/dist/mdc.icon-button.min.css";
import "@rmwc/snackbar/node_modules/@material/snackbar/dist/mdc.snackbar.min.css";

type CopyBoxProps = {
  children: JSX.Element | JSX.Element[];
  gettext: (a: string) => string;
};

type CopyBoxState = {
  snackbarIsOpen: boolean;
  snackbarMessage: string;
};

export class CopyBox extends Component<CopyBoxProps, CopyBoxState> {
  state = {
    snackbarIsOpen: false,
    snackbarMessage: "",
  };

  ref = createRef();

  handleCopy = () => {
    console.debug("Copy to clipboard");
    try {
      window.navigator.clipboard.writeText(this.ref.current.innerText);
      this.setState({
        snackbarIsOpen: true,
        snackbarMessage: this.props.gettext("Copied to clipboard."),
      });
    } catch (error) {
      this.setState({
        snackbarIsOpen: true,
        snackbarMessage: this.props.gettext("An error occurred."),
      });
    }
  };

  render() {
    return (
      <div class="copybox">
        <IconButton
          icon="content_copy"
          onClick={() => this.handleCopy()}
          title={this.props.gettext("Copy to clipboard.")}
        />
        <div ref={this.ref}>{this.props.children}</div>
        {createPortal(
          <Snackbar
            show={this.state.snackbarIsOpen}
            onHide={() => this.setState({ snackbarIsOpen: false })}
            message={this.state.snackbarMessage}
            timeout={1000}
            actionHandler={() => {}} // eslint-disable-line @typescript-eslint/no-empty-function
            actionText="OK"
            dismissesOnAction={true}
          />,
          document.body,
        )}
      </div>
    );
  }
}
