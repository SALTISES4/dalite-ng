import { h } from "preact";

import { IconButton } from "@rmwc/icon-button";
import { Typography } from "@rmwc/typography";

import "@rmwc/icon-button/node_modules/@material/icon-button/dist/mdc.icon-button.min.css";
import "@rmwc/typography/node_modules/@material/typography/dist/mdc.typography.min.css";

type HeadingProps = {
  gettext: (a: string) => string;
  onClick: (a: React.MouseEvent) => void;
  open: boolean;
  title: string;
};

export function Heading({
  gettext,
  onClick,
  open,
  title,
}: HeadingProps): JSX.Element {
  return (
    <div style={{ alignItems: "baseline", display: "flex" }}>
      <IconButton
        checked={open}
        icon={"chevron_right"}
        onClick={onClick}
        onIcon={"expand_more"}
        theme="secondary"
        title={
          open
            ? gettext("Collapse to hide list.")
            : gettext("Expand to show list.")
        }
      />
      <Typography
        onClick={onClick}
        use="headline4"
        tag="h2"
        style={{ cursor: "pointer", marginBottom: 0 }}
        theme="text-secondary-on-background"
      >
        {title}
      </Typography>
    </div>
  );
}

type BreadcrumbProps = {
  text: string;
  onClick: (a: React.MouseEvent) => void;
};

export function Breadcrumb({ onClick, text }: BreadcrumbProps): JSX.Element {
  return (
    <Typography
      className="breadcrumb"
      onClick={onClick}
      use="caption"
      tag="span"
    >
      {text}
    </Typography>
  );
}
