import { Box, Button, ButtonProps, Tooltip } from "@mui/material";
import { PropsWithChildren } from "react";

import { HasAccessProps } from "../models/models";
import HasAccess from "./HasAccess";

const AccessButton = ({
  label,
  tooltip,
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
  text,
  raised,
  rounded,
  ...props
}: PropsWithChildren<
  ButtonProps &
    HasAccessProps & {
      basic?: boolean | undefined;
      text?: boolean | undefined;
      raised?: boolean | undefined;
      rounded?: boolean | undefined;
    }
>) => {
  if (!tooltip) {
    if (Object.hasOwn(props, "aria-label")) {
      tooltip = props["aria-label"];
    } else if (Object.hasOwn(props, "title")) {
      tooltip = props.title;
    } else if (label) {
      tooltip = label;
    } else if (Object.hasOwn(props, "name")) {
      tooltip = props.name;
    }
  }

  if (!Object.hasOwn(props, "aria-label")) {
    if (label) {
      props["aria-label"] = label;
    } else if (tooltip) {
      props["aria-label"] = tooltip;
    }
  }

  if (Object.hasOwn(props, "title")) {
    props.title = undefined;
  }

  if (!Object.hasOwn(props, "variant")) {
    props.variant = "contained";
  }

  if (
    Object.hasOwn(props, "aria-label") &&
    label &&
    props["aria-label"] !== label
  ) {
    console.error(
      "Mismatched Label and Aria-Label, migrating for 508 compliance to Label value:",
      props["aria-label"],
      " !== ",
      label,
    );
    props["aria-label"] = label;
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

  if (!Object.hasOwn(props, "sx")) {
    props.sx = {};
  }

  if (rounded) {
    props.sx = { ...props.sx, ...{ borderRadius: "50px" } };
  }

  if (raised) {
    props.variant = "contained";
  }

  if (text) {
    props.variant = "text";
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
            <Tooltip title={tooltip} placement="bottom" arrow>
              <Box component="span">
                <Button {...{ ...props, ...{ disabled: true } }}>
                  {children}
                </Button>
              </Box>
            </Tooltip>
          )
        }
        renderAuthFailed={
          renderAuthFailed ?? (
            <Tooltip title={tooltip} placement="bottom" arrow>
              <Box component="span">
                <Button {...{ ...props, ...{ disabled: true } }}>
                  {children}
                </Button>
              </Box>
            </Tooltip>
          )
        }
      >
        <Tooltip title={tooltip} placement="bottom" arrow>
          <Box component="span">
            <Button {...props}>{children}</Button>
          </Box>
        </Tooltip>
      </HasAccess>
    );
  } else {
    return (
      <Tooltip title={tooltip} placement="bottom" arrow>
        <Box component="span">
          <Button {...props}>{children}</Button>
        </Box>
      </Tooltip>
    );
  }
};

export default AccessButton;
