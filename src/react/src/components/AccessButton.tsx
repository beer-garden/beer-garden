import { Button, ButtonProps } from "primereact/button";
import { PropsWithChildren } from "react";

import { HasAccessProps } from "../models/models";
import HasAccess from "./HasAccess";

const AccessButton = ({
  config,
  permission,
  isGlobal,
  hasGardenName,
  hasNamespace,
  hasSystemName,
  hasSystemVersion,
  hasCommandName,
  hasInstanceName,
  isLoading,
  renderAuthFailed,
  children,
  basic,
  ...props
}: PropsWithChildren<
  ButtonProps & HasAccessProps & { basic?: boolean | undefined }
>) => {
  if (!Object.hasOwn(props, "tooltip")) {
    if (Object.hasOwn(props, "aria-label")) {
      props["tooltip"] = props["aria-label"];
    } else if (Object.hasOwn(props, "title")) {
      props["tooltip"] = props.title;
    } else if (Object.hasOwn(props, "label")) {
      props["tooltip"] = props.label;
    } else if (Object.hasOwn(props, "name")) {
      props["tooltip"] = props.name;
    }
  }

  if (!Object.hasOwn(props, "aria-label")) {
    if (Object.hasOwn(props, "label")) {
      props["aria-label"] = props.label;
    } else if (Object.hasOwn(props, "tooltip")) {
      props["aria-label"] = props.tooltip;
    }
  }

  if (Object.hasOwn(props, "title")) {
    props.title = undefined;
  }

  if (!Object.hasOwn(props, "tooltipOptions")) {
    props.tooltipOptions = { position: "bottom" };
  }

  if (
    Object.hasOwn(props, "aria-label") &&
    Object.hasOwn(props, "label") &&
    props["aria-label"] !== props["label"]
  ) {
    console.error(
      "Mismatched Label and Aria-Label, migrating for 508 compliance to Label value:",
      props["aria-label"],
      " !== ",
      props["label"],
    );
    props["aria-label"] = props["label"];
  }

  if (!Object.hasOwn(props, "style") || props.style === undefined) {
    props.style = {};
  }

  // Custom Class Styles
  if (basic) {
    if (Object.hasOwn(props, "className") && props.className) {
      props.className = `${props.className} basic`;
    } else {
      props.className = "basic";
    }
  }

  if (permission && config && config?.auth_enabled === true) {
    return (
      <HasAccess
        config={config}
        permission={permission}
        isGlobal={isGlobal}
        hasGardenName={hasGardenName}
        hasNamespace={hasNamespace}
        hasSystemName={hasSystemName}
        hasSystemVersion={hasSystemVersion}
        hasCommandName={hasCommandName}
        hasInstanceName={hasInstanceName}
        isLoading={
          isLoading ?? (
            <Button {...{ ...props, ...{ disabled: true } }}>{children}</Button>
          )
        }
        renderAuthFailed={
          renderAuthFailed ?? (
            <Button {...{ ...props, ...{ disabled: true } }}>{children}</Button>
          )
        }
      >
        <Button {...props}>{children}</Button>
      </HasAccess>
    );
  } else {
    return <Button {...props}>{children}</Button>;
  }
};

export default AccessButton;
