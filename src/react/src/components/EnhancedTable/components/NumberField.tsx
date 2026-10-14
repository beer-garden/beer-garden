import { NumberField as BaseNumberField } from "@base-ui/react/number-field";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import FormControl from "@mui/material/FormControl";
import FormHelperText from "@mui/material/FormHelperText";
import IconButton from "@mui/material/IconButton";
import InputAdornment from "@mui/material/InputAdornment";
import InputLabel from "@mui/material/InputLabel";
import OutlinedInput from "@mui/material/OutlinedInput";
import Tooltip from "@mui/material/Tooltip";
import * as React from "react";

/**
 * This is a near copy of the base example provided by MUI Number Field
 * Modifications are to use Font Awsome and provide helper text
 */

/**
 * This component is a placeholder for FormControl to correctly set the shrink label state on SSR.
 */
function SSRInitialFilled(_: BaseNumberField.Root.Props) {
  return null;
}
SSRInitialFilled.muiName = "Input";

interface CustomInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  tooltipTitle?: string;
}

const TooltippedInput = React.forwardRef<HTMLInputElement, CustomInputProps>(
  ({ tooltipTitle, ...props }, ref) => {
    return (
      <Tooltip title={tooltipTitle} disableHoverListener={!tooltipTitle}>
        <input ref={ref} {...props} />
      </Tooltip>
    );
  },
);

export default React.forwardRef(function NumberField(
  {
    id: idProp,
    label,
    helperText,
    error,
    size = "medium",
    title,
    ...other
  }: BaseNumberField.Root.Props & {
    label?: React.ReactNode;
    helperText?: string;
    size?: "small" | "medium";
    error?: boolean;
    title?: React.ReactNode;
  },
  ref: React.Ref<any>,
) {
  let id = React.useId();
  if (idProp) {
    id = idProp;
  }

  return (
    <BaseNumberField.Root
      {...other}
      ref={ref}
      render={(props, state) => (
        <FormControl
          size={size}
          ref={props.ref}
          disabled={state.disabled}
          required={state.required}
          error={error}
          variant="outlined"
        >
          {props.children}
        </FormControl>
      )}
    >
      <SSRInitialFilled {...other} />
      <InputLabel htmlFor={id}>{label}</InputLabel>
      <BaseNumberField.Input
        id={id}
        render={(props, state) => (
          <OutlinedInput
            aria-describedby={`${id}-helper-text`}
            label={label}
            inputRef={props.ref}
            value={state.inputValue}
            onBlur={props.onBlur}
            onChange={props.onChange}
            onKeyUp={props.onKeyUp}
            onKeyDown={props.onKeyDown}
            onFocus={props.onFocus}
            slotProps={{
              input: props,
            }}
            inputProps={{ tooltipTitle: title }}
            inputComponent={TooltippedInput as any}
            endAdornment={
              <InputAdornment
                position="end"
                sx={{
                  flexDirection: "column",
                  maxHeight: "unset",
                  alignSelf: "stretch",
                  borderLeft: "1px solid",
                  borderColor: "divider",
                  ml: 0,
                  "& button": {
                    py: 0,
                    flex: 1,
                    borderRadius: 0.5,
                  },
                }}
              >
                <Tooltip title={`Increase ${title}`}>
                  <BaseNumberField.Increment
                    render={
                      <IconButton
                        size={size}
                        aria-label={`Increase ${title}`}
                      />
                    }
                  >
                    <FontAwesomeIcon icon="angle-up" />
                  </BaseNumberField.Increment>
                </Tooltip>
                <Tooltip title={`Decrease ${title}`}>
                  <BaseNumberField.Decrement
                    render={
                      <IconButton
                        size={size}
                        aria-label={`Decrease ${title}`}
                      />
                    }
                  >
                    <FontAwesomeIcon icon="angle-down" />
                  </BaseNumberField.Decrement>
                </Tooltip>
              </InputAdornment>
            }
            sx={{ pr: 0 }}
          />
        )}
      />
      <FormHelperText
        id={`${id}-helper-text`}
        sx={{ ml: 0, "&:empty": { mt: 0 } }}
      >
        {helperText}
      </FormHelperText>
    </BaseNumberField.Root>
  );
});
