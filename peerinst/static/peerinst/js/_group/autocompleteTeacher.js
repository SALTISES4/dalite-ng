import { Component, h } from "preact";

import { Chip, ChipSet } from "@rmwc/chip";
import {
  TextField,
  TextFieldHelperText,
  TextFieldIcon,
} from "@rmwc/textfield";
import { Typography } from "@rmwc/typography";

// Rely on mdc default styles from global use

import { get, submitData } from "../_ajax/ajax.js";

export class TeacherInputWithAutocomplete extends Component {
  state = {
    searchResult: "",
    searchTerm: "",
    teachers: this.props.teachers.map((t) => {
      return { user: t["user__username"], pk: t["pk"] };
    }),
  };

  search = async () => {
    if (this.state.searchTerm != "") {
      try {
        const queryString = new URLSearchParams({
          query: this.state.searchTerm,
        });
        const url = `${this.props.searchURL}?${queryString.toString()}`;
        const data = await get(url);
        console.debug(data);
        if (data.length > 0) {
          this.setState({
            searchResult: {
              user: data[0]["user"]["username"],
              pk: data[0]["pk"],
            },
          });
        } else {
          this.setState({
            searchResult: {},
          });
        }
      } catch (error) {
        console.error(error);
      }
    } else {
      this.setState({
        searchResult: {},
      });
    }
  };

  save = async () => {
    if (this.state.searchTerm == this.state.searchResult.user) {
      if (
        !this.state.teachers
          .map((t) => t.user)
          .includes(this.state.searchResult.user)
      ) {
        try {
          const _teachers = this.state.teachers;
          _teachers.push({
            user: this.state.searchResult.user,
            pk: this.state.searchResult.pk,
          });
          await submitData(
            this.props.updateURL,
            { teacher: _teachers.map((t) => t.pk) },
            "PUT",
          );
          this.setState({
            teachers: _teachers,
            searchTerm: "",
            searchResult: {},
          });
        } catch (error) {
          console.error(error);
          this.setState({ searchTerm: "", searchResult: {} });
        }
      }
    }
  };

  render() {
    return (
      <div>
        <TextField
          dense
          outlined
          placeholder={this.props.gettext("Add teachers to group")}
          onInput={(evt) => {
            this.setState({ searchTerm: evt.target.value }, () =>
              this.search(),
            );
          }}
          value={this.state.searchTerm}
          onKeyDown={(evt) => {
            if (evt.key === "Enter") {
              evt.preventDefault();
              this.save();
            }
            if (evt.key === "Tab") {
              this.setState({ searchTerm: this.state.searchResult.user });
              evt.preventDefault();
            }
          }}
          style={{ position: "relative" }}
          withTrailingIcon={
            <TextFieldIcon
              tabIndex="0"
              icon={
                this.state.searchTerm.length != 0
                  ? this.state.searchTerm == this.state.searchResult.user
                    ? "check"
                    : "close"
                  : ""
              }
              onClick={() => {
                this.save();
                this.setState({ searchTerm: "", searchResult: {} });
              }}
              theme="primary"
            />
          }
        >
          <div
            style={{
              color: "gray",
              opacity: "0.4",
              position: "absolute",
              bottom: "14px",
              left: "12px",
              letterSpacing: ".04em",
            }}
          >
            {this.state.searchResult.user}
          </div>
        </TextField>
        <TextFieldHelperText persistent>
          {this.props.gettext(
            "Type another teacher's username to add them to this group.  Note: this cannot be undone without contacting an administrator.",
          )}
        </TextFieldHelperText>
        <ChipSet>
          <Typography use="body2">
            {this.state.teachers.map((teacher, i) => {
              return (
                <Chip
                  id={`chip-${i}`}
                  key={i}
                  text={teacher.user}
                  theme="secondary"
                />
              );
            })}
          </Typography>
        </ChipSet>
      </div>
    );
  }
}
