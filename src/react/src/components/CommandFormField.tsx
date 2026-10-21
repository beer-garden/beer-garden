import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  Box,
  Checkbox,
  Container,
  FormHelperText,
  IconButton,
  LinearProgress,
  MenuItem,
  Select,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import Autocomplete from "@mui/material/Autocomplete";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import { styled } from "@mui/material/styles";
import { DatePicker } from "@mui/x-date-pickers";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { DateTimePicker } from "@mui/x-date-pickers/DateTimePicker";
import { PickerValue } from "@mui/x-date-pickers/internals";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import dayjs from "dayjs";
import { ChangeEvent, useEffect, useState } from "react";

import { InputParam } from "../models/models";
import { uploadFile } from "../services/file_service";
import { FAIcon } from "../services/util_service";
import { inputDisplayStyling } from "../styles/sharedStyles";
import AccessButton from "./AccessButton";
import NumberField from "./EnhancedTable/components/NumberField";

interface CommandFormFieldParams {
  parameter: InputParam;
  disabled: boolean;
  handleChange: (name: any, value: any) => void;
  parametersFields: Array<InputParam>;
  loadingChoices: Array<{ key: string; timestamp: number }>;
  resetForm: boolean;
}

function CommandFormField({
  parameter,
  disabled,
  handleChange,
  parametersFields,
  loadingChoices,
  resetForm,
}: CommandFormFieldParams) {
  // Base64 Stateful Objects
  const [uploadPercentage, setUploadPercentage] = useState(0);
  const [uploadPercentageBuffer, setUploadPercentageBuffer] = useState(0);

  // Bytes and Base64 Triggers
  useEffect(() => {
    if (uploadPercentage !== 0) {
      setUploadPercentage(0);
    }
  }, [resetForm]);

  const handleMultiChange = (key: any, value: any, index?: number) => {
    parametersFields.forEach((param: InputParam) => {
      if (param.key === key) {
        if (index === undefined) {
          param.value = value;
        } else {
          param.value[index] = value;
        }

        handleChange(key, param.value);
      }
    });
  };

  const removeMultiItem = (key: any, index: any) => {
    parametersFields.forEach((param: InputParam) => {
      if (param.key === key) {
        const newItems: any[] = [];
        param.value.forEach((param_value: any, param_index: any) => {
          if (param_index !== index) {
            newItems.push(param_value);
          }
        });
        handleChange(key, newItems);
      }
    });
  };

  const addMultiItem = (key: any, param_default: any) => {
    parametersFields.forEach((param: InputParam) => {
      if (param.key === key) {
        const newItems: any[] = [];
        param.value.forEach((param_value: any) => {
          newItems.push(param_value);
        });
        if (Array.isArray(param_default)) {
          if (param.default.length === 1) {
            newItems.push(param.default[0]);
          } else {
            newItems.push(null);
          }
        } else {
          newItems.push(param_default || null);
        }
        handleChange(key, newItems);
      }
    });
  };

  const parameterDisplayName =
    parameter.display_name === null ||
    parameter.display_name === undefined ||
    parameter.display_name.length === 0
      ? parameter.display_name
      : parameter.key;

  const inputAreaAriaLabel = `${parameter.optional ? "Optional: " : ""}Parameter Input ${parameterDisplayName}`;

  const addInputAriaLabel = `Add new value to List for Parameter ${parameterDisplayName}`;

  const removeInputAriaLabel = `Remove value from List for Parameter ${parameterDisplayName}`;

  if (!parameter.key) return null;

  if (parameter.multi && !Array.isArray(parameter.default)) {
    if (parameter.default === undefined || parameter.default === null) {
      parameter.default = [];
    } else {
      parameter.default = [parameter.default];
    }
  }

  if (parameter.multi && !Array.isArray(parameter.value)) {
    if (parameter.value === undefined || parameter.value === null) {
      parameter.value = [];
    } else {
      parameter.value = [parameter.value];
    }
  }

  // Choices = command, static, url
  if (
    parameter.choices &&
    (parameter.choices.display === undefined ||
      parameter.choices.display === "select")
  ) {
    if (parameter.multi) {
      return (
        <Box key={parameter.key} id={parameter.key} sx={inputDisplayStyling}>
          <Tooltip title={`${inputAreaAriaLabel}: Multi Select`}>
            <Box component="span" aria-label={undefined}>
              <Select
                id={parameter.key}
                value={parameter.value}
                aria-describedby={
                  parameter.error
                    ? `${parameter.key}-helper-text ${parameter.key}-error-text`
                    : `${parameter.key}-helper-text`
                }
                multiple
                disabled={
                  disabled ||
                  parameter.options === undefined ||
                  parameter.options.length === 0 ||
                  loadingChoices.some(
                    (loading) => loading.key === parameter.key,
                  ) ||
                  parameter.error
                }
                error={parameter.error}
                inputProps={{
                  "aria-label": inputAreaAriaLabel,
                }}
                onChange={(event) => {
                  const {
                    target: { value },
                  } = event;

                  handleChange(
                    parameter.key,
                    (typeof value === "string"
                      ? value.split(",")
                      : value
                    ).filter((option: string) =>
                      parameter.options?.some((opt) => opt.value === option),
                    ),
                  );
                }}
              >
                {parameter.options?.map((option) => (
                  <MenuItem
                    key={option.value}
                    value={option.value}
                    aria-label={`Select ${parameter.key} value ${option.value}`}
                  >
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
              <FormHelperText
                key={`${parameter.key}-helper-text`}
                id={`${parameter.key}-helper-text`}
                aria-live="polite"
                error={parameter.error}
              >
                {parameter.errorMsg
                  ? `${parameter.optional ? "Optional: " : ""}${parameter.description !== undefined && parameter.description !== null ? parameter.description : `Parameter Input ${parameterDisplayName}`}: ${parameter.errorMsg}`
                  : `${parameter.optional ? "Optional: " : ""}${parameter.description !== undefined && parameter.description !== null ? parameter.description : `Parameter Input ${parameterDisplayName}`}`}
              </FormHelperText>
            </Box>
          </Tooltip>
          {loadingChoices &&
            loadingChoices.some((loading) => loading.key === parameter.key) && (
              <CircularProgress
                aria-label="Loading…"
                sx={{ width: "34px", height: "34px" }}
              />
            )}
          {parameter.error && (
            <FontAwesomeIcon
              icon="triangle-exclamation"
              title={parameter.errorMsg ?? "ERROR"}
              aria-label={parameter.errorMsg ?? "ERROR"}
              role="img"
              key={`${parameter.key}-error-text`}
            />
          )}
        </Box>
      );
    }
    return (
      <Box key={parameter.key} id={parameter.key} sx={inputDisplayStyling}>
        <Tooltip title={`${inputAreaAriaLabel}: Dropdown Select`}>
          <Box component="span" aria-label={undefined}>
            <Select
              id={parameter.key}
              value={parameter.value}
              aria-describedby={
                parameter.error
                  ? `${parameter.key}-helper-text ${parameter.key}-error-text`
                  : `${parameter.key}-helper-text`
              }
              disabled={
                disabled ||
                parameter.options === undefined ||
                parameter.options.length === 0 ||
                loadingChoices.some(
                  (loading) => loading.key === parameter.key,
                ) ||
                parameter.error
              }
              error={parameter.error}
              inputProps={{
                "aria-label": inputAreaAriaLabel,
              }}
              onChange={(event) => {
                handleChange(parameter.key, event.target.value);
              }}
            >
              {parameter.options?.map((option) => (
                <MenuItem
                  key={option.value}
                  value={option.value}
                  aria-label={`Select ${parameter.key} value ${option.value}`}
                >
                  {option.label}
                </MenuItem>
              ))}
            </Select>
            <FormHelperText
              key={`${parameter.key}-helper-text`}
              id={`${parameter.key}-helper-text`}
              aria-live="polite"
              error={parameter.error}
            >
              {parameter.errorMsg
                ? `${parameter.optional ? "Optional: " : ""}${parameter.description !== undefined && parameter.description !== null ? parameter.description : `Parameter Input ${parameterDisplayName}`}: ${parameter.errorMsg}`
                : `${parameter.optional ? "Optional: " : ""}${parameter.description !== undefined && parameter.description !== null ? parameter.description : `Parameter Input ${parameterDisplayName}`}`}
            </FormHelperText>
          </Box>
        </Tooltip>

        {loadingChoices &&
          loadingChoices.some((loading) => loading.key === parameter.key) && (
            <CircularProgress
              aria-label="Loading…"
              sx={{ width: "34px", height: "34px" }}
            />
          )}
        {parameter.error && (
          <FontAwesomeIcon
            icon="triangle-exclamation"
            title={parameter.errorMsg ?? "ERROR"}
            aria-label={parameter.errorMsg ?? "ERROR"}
            role="img"
            key={`${parameter.key}-error-text`}
          />
        )}
      </Box>
    );
  } else if (parameter.choices && parameter.choices?.display === "typeahead") {
    return (
      <Box key={parameter.key} id={parameter.key} sx={inputDisplayStyling}>
        <Autocomplete
          sx={{ width: "100%" }}
          id={parameter.key}
          freeSolo
          aria-describedby={
            parameter.error
              ? `${parameter.key}-helper-text ${parameter.key}-error-text`
              : `${parameter.key}-helper-text`
          }
          value={
            parameter?.multi == true
              ? (parameter.value as string[])
              : (parameter.value as string)
          }
          options={
            parameter?.options
              ? parameter?.options?.map((option) => option.value as string)
              : []
          }
          onChange={(_event: any, newValue: any) => {
            handleChange(parameter.key, newValue);
          }}
          getOptionLabel={(option) =>
            typeof option === "object" ? String(option.label) : String(option)
          }
          disabled={disabled}
          multiple={parameter?.multi === true}
          renderInput={(params) => (
            <Tooltip
              title={`${inputAreaAriaLabel}: Typeahead, start typing input and press enter after typing to reload options`}
            >
              <Box aria-label={undefined}>
                <TextField
                  {...params}
                  variant="outlined"
                  placeholder={parameter.display_name}
                  label={parameter.display_name ?? parameter.key}
                  aria-label={inputAreaAriaLabel}
                  error={parameter.error}
                  autoComplete="off"
                />
              </Box>
            </Tooltip>
          )}
        />

        <FormHelperText
          key={`${parameter.key}-helper-text`}
          id={`${parameter.key}-helper-text`}
          aria-live="polite"
          error={parameter.error}
        >
          {parameter.errorMsg
            ? `${parameter.optional ? "Optional: " : ""}${parameter.description !== undefined && parameter.description !== null ? parameter.description : `Parameter Input ${parameterDisplayName}`}: ${parameter.errorMsg}`
            : `${parameter.optional ? "Optional: " : ""}${parameter.description !== undefined && parameter.description !== null ? parameter.description : `Parameter Input ${parameterDisplayName}`}`}
        </FormHelperText>
        {loadingChoices &&
          loadingChoices.some((loading) => loading.key === parameter.key) && (
            <CircularProgress
              aria-label="Loading…"
              style={{ width: "34px", height: "34px" }}
            />
          )}
        {parameter.error && (
          <FontAwesomeIcon
            icon="triangle-exclamation"
            title={parameter.errorMsg ?? "ERROR"}
            aria-label={parameter.errorMsg ?? "ERROR"}
            role="img"
            key={`${parameter.key}-error-text`}
          />
        )}
      </Box>
    );
  }

  const customBytesUploader = (event: any) => {
    if (event.target.files.length === 1) {
      const file = event.target.files[0];
      handleChange(parameter.key, file as File);
    } else {
      handleChange(parameter.key, undefined);
    }
  };
  const VisuallyHiddenInput = styled("input")({
    clip: "rect(0 0 0 0)",
    clipPath: "inset(50%)",
    height: 1,
    overflow: "hidden",
    position: "absolute",
    bottom: 0,
    left: 0,
    whiteSpace: "nowrap",
    width: 1,
  });

  const customBase64Uploader = async (event: any) => {
    const file = event.target.files[0];

    const fileUploadResult = await uploadFile(
      file,
      setUploadPercentage,
      setUploadPercentageBuffer,
    );

    handleChange(parameter.key, fileUploadResult);
    setUploadPercentage(100);
    setUploadPercentageBuffer(100);
  };

  const removeFile = () => {
    handleChange(parameter.key, null);
    setUploadPercentage(0);
    setUploadPercentageBuffer(0);
  };

  if (parameter.multi) {
    return (
      <Container key={parameter.key} id={parameter.key} sx={{ mx: 1 }}>
        {parameter.value?.map((item: any, index: any) => (
          <Box
            key={`${parameter.key}-${index}`}
            sx={{ justifyContent: "flex-end", my: 1 }}
          >
            <Box
              sx={{
                display: "flex",
                justifyContent: "flex-end",
              }}
            >
              <Tooltip
                title={`${inputAreaAriaLabel} Index ${index}: ${parameter?.type}`}
                open={
                  parameter?.type &&
                  ["Float", "Integer"].includes(parameter?.type)
                    ? false
                    : undefined
                }
              >
                <Box component="span" aria-label={undefined}>
                  {(parameter.type === undefined ||
                    parameter?.type === "String") && (
                    <TextField
                      id={`${parameter.key}-${index}-input-id`}
                      value={item}
                      variant="outlined"
                      onChange={(event: ChangeEvent<HTMLInputElement>) => {
                        handleMultiChange(
                          parameter.key,
                          event.target.value,
                          index,
                        );
                      }}
                      slotProps={{
                        input: {
                          "aria-describedby": `${parameter.key}-${index}-helper-text`,
                        },
                      }}
                      fullWidth
                      disabled={disabled}
                      error={
                        parameter.error &&
                        parameter.errorIndex &&
                        parameter.errorIndex.includes(index)
                      }
                      autoComplete="off"
                    />
                  )}

                  {parameter?.type === "Dictionary" && (
                    <TextField
                      id={`${parameter.key}-${index}-input-id`}
                      value={item}
                      variant="outlined"
                      onChange={(event: ChangeEvent<HTMLInputElement>) => {
                        handleMultiChange(
                          parameter.key,
                          event.target.value,
                          index,
                        );
                      }}
                      slotProps={{
                        input: {
                          "aria-describedby": `${parameter.key}-${index}-helper-text`,
                        },
                      }}
                      fullWidth
                      multiline
                      disabled={disabled}
                      error={
                        parameter.error &&
                        parameter.errorIndex &&
                        parameter.errorIndex.includes(index)
                      }
                      autoComplete="off"
                    />
                  )}

                  {parameter?.type === "Integer" && (
                    <NumberField
                      id={`${parameter.key}-${index}-input-id`}
                      value={item}
                      aria-describedby={`${parameter.key}-${index}-helper-text`}
                      title={`${inputAreaAriaLabel} Index ${index}: Integer ${parameter.maximum ? `Max Value=${parameter.maximum}` : ""} ${parameter.minimum ? `Max Value=${parameter.minimum}` : ""}`}
                      disabled={disabled}
                      onValueChange={(value) =>
                        handleMultiChange(parameter.key, value, index)
                      }
                      error={
                        parameter.error &&
                        parameter.errorIndex &&
                        parameter.errorIndex.includes(index)
                      }
                      max={
                        parameter.maximum !== undefined
                          ? parameter.maximum
                          : undefined
                      }
                      min={
                        parameter.minimum !== undefined
                          ? parameter.minimum
                          : undefined
                      }
                    />
                  )}

                  {parameter?.type === "Float" && (
                    <NumberField
                      id={`${parameter.key}-${index}-input-id`}
                      value={item}
                      disabled={disabled}
                      aria-describedby={`${parameter.key}-${index}-helper-text`}
                      title={`${inputAreaAriaLabel} Index ${index}: Float ${parameter.maximum ? `Max Value=${parameter.maximum}` : ""} ${parameter.minimum ? `Max Value=${parameter.minimum}` : ""}`}
                      onValueChange={(value) =>
                        handleMultiChange(parameter.key, value, index)
                      }
                      error={
                        parameter.error &&
                        parameter.errorIndex &&
                        parameter.errorIndex.includes(index)
                      }
                      max={
                        parameter.maximum !== undefined
                          ? parameter.maximum
                          : undefined
                      }
                      min={
                        parameter.minimum !== undefined
                          ? parameter.minimum
                          : undefined
                      }
                      step={0.01}
                    />
                  )}

                  {parameter?.type === "Boolean" && (
                    <Checkbox
                      id={`${parameter.key}-${index}-id`}
                      checked={item}
                      slotProps={{
                        input: {
                          "aria-label": `Parameter ${parameter.display_name ?? parameter.key} option ${index}`,
                          "aria-describedby": `${parameter.key}-${index}-helper-text`,
                        },
                      }}
                      indeterminate={
                        item === undefined
                          ? parameter.nullable || parameter.optional
                          : false
                      }
                      onChange={(e) =>
                        handleMultiChange(
                          parameter.key,
                          e.target.checked,
                          index,
                        )
                      }
                      disabled={disabled}
                    />
                  )}

                  {parameter?.type === "Date" && (
                    <LocalizationProvider dateAdapter={AdapterDayjs}>
                      <DatePicker
                        disabled={disabled}
                        value={item ? dayjs(item) : null}
                        aria-describedby={`${parameter.key}-helper-text`}
                        onChange={(newValue: PickerValue) => {
                          if (newValue && newValue.isValid()) {
                            handleMultiChange(
                              parameter.key,
                              newValue.valueOf(),
                              index,
                            );
                          } else {
                            handleMultiChange(parameter.key, undefined, index);
                          }
                        }}
                        slotProps={{
                          textField: {
                            id: `${parameter.key}-${index}-input-id`,
                            error:
                              parameter.error &&
                              parameter.errorIndex &&
                              parameter.errorIndex.includes(index),
                            slotProps: {
                              input: {
                                "aria-describedby": `${parameter.key}-${index}-helper-text`,
                              },
                            },
                          },
                        }}
                      />
                    </LocalizationProvider>
                  )}

                  {parameter?.type === "DateTime" && (
                    <LocalizationProvider dateAdapter={AdapterDayjs}>
                      <DateTimePicker
                        disabled={disabled}
                        value={item ? dayjs(item) : null}
                        aria-describedby={`${parameter.key}-helper-text`}
                        onChange={(newValue: PickerValue) => {
                          if (newValue && newValue.isValid()) {
                            handleMultiChange(
                              parameter.key,
                              newValue.valueOf(),
                              index,
                            );
                          } else {
                            handleMultiChange(parameter.key, undefined, index);
                          }
                        }}
                        slotProps={{
                          textField: {
                            id: `${parameter.key}-${index}-input-id`,
                            error:
                              parameter.error &&
                              parameter.errorIndex &&
                              parameter.errorIndex.includes(index),
                            slotProps: {
                              input: {
                                "aria-describedby": `${parameter.key}-${index}-helper-text`,
                              },
                            },
                          },
                        }}
                      />
                    </LocalizationProvider>
                  )}

                  {parameter?.type === "Bytes" && (
                    <Typography>Multi-File Upload Not Supported</Typography>
                  )}

                  {parameter?.type === "Base64" && (
                    <Typography>Multi-File Upload Not Supported</Typography>
                  )}
                </Box>
              </Tooltip>
              <Tooltip title={removeInputAriaLabel}>
                <Box component="span" aria-label={undefined}>
                  <IconButton
                    onClick={() => removeMultiItem(parameter.key, index)}
                    disabled={disabled}
                    aria-label={removeInputAriaLabel}
                  >
                    <FAIcon icon="xmark" />
                  </IconButton>
                </Box>
              </Tooltip>
            </Box>
            <FormHelperText
              key={`${parameter.key}-${index}-helper-text`}
              id={`${parameter.key}-${index}-helper-text`}
              aria-live="polite"
              error={parameter.error}
              sx={inputDisplayStyling}
            >
              {parameter.error &&
              parameter.errorIndex &&
              parameter.errorIndex.includes(index)
                ? `${parameter.optional ? "Optional: " : ""}${parameter.description !== undefined && parameter.description !== null ? parameter.description : `Parameter Input ${parameterDisplayName}`}: ${parameter.errorIndexMessage?.find((value) => value.index === index)?.msg}`
                : `${parameter.optional ? "Optional: " : ""}${parameter.description !== undefined && parameter.description !== null ? parameter.description : `Parameter Input ${parameterDisplayName}`}`}
            </FormHelperText>
          </Box>
        ))}

        <Box
          sx={{
            display: "flex",
            justifyContent: "flex-end",
          }}
        >
          <AccessButton
            onClick={() => addMultiItem(parameter.key, parameter.default)}
            disabled={disabled}
            tooltip={addInputAriaLabel}
            aria-label={addInputAriaLabel}
          >
            <Typography variant="button">
              Add {parameter.display_name ?? parameter.key}
            </Typography>
          </AccessButton>
        </Box>
      </Container>
    );
  } else {
    return (
      <Box key={parameter.key} id={parameter.key} sx={inputDisplayStyling}>
        <Box>
          {parameter?.type === "Bytes" && parameter?.value?.name && (
            <IconButton
              onClick={() => handleChange(parameter.key, undefined)}
              aria-label={`Clear selected file for ${parameter.display_name ?? parameter.key}`}
            >
              <Typography variant="caption">
                {parameter?.value?.name}
              </Typography>
              <FAIcon icon="xmark" sx={{ ml: 1 }} />
            </IconButton>
          )}

          {parameter?.type === "Base64" && uploadPercentage === 100 && (
            <IconButton
              onClick={removeFile}
              aria-label={`Clear uploaded file for ${parameter.display_name ?? parameter.key}`}
            >
              <Typography variant="caption">
                {parameter?.value?.details?.file_name}
              </Typography>
              <FAIcon icon="xmark" sx={{ ml: 1 }} />
            </IconButton>
          )}
          <Tooltip
            title={`${inputAreaAriaLabel}: ${parameter?.type}`}
            open={
              parameter?.type && ["Float", "Integer"].includes(parameter?.type)
                ? false
                : undefined
            }
          >
            <Box aria-label={undefined}>
              {(parameter.type === undefined ||
                parameter?.type === "String") && (
                <TextField
                  id={`${parameter.key}-input-id`}
                  value={parameter.value}
                  variant="outlined"
                  onChange={(event: ChangeEvent<HTMLInputElement>) => {
                    handleChange(parameter.key, event.target.value);
                  }}
                  slotProps={{
                    input: {
                      "aria-describedby": `${parameter.key}-helper-text`,
                    },
                  }}
                  fullWidth
                  disabled={disabled}
                  error={parameter.error}
                  autoComplete="off"
                />
              )}

              {parameter?.type === "Dictionary" && (
                <TextField
                  id={`${parameter.key}-input-id`}
                  value={parameter.value}
                  variant="outlined"
                  onChange={(event: ChangeEvent<HTMLInputElement>) => {
                    handleChange(parameter.key, event.target.value);
                  }}
                  slotProps={{
                    input: {
                      "aria-describedby": `${parameter.key}-helper-text`,
                    },
                  }}
                  fullWidth
                  disabled={disabled}
                  multiline
                  error={parameter.error}
                  autoComplete="off"
                />
              )}

              {parameter?.type === "Integer" && (
                <NumberField
                  id={`${parameter.key}-input-id`}
                  value={parameter.value}
                  aria-describedby={`${parameter.key}-helper-text`}
                  title={`${inputAreaAriaLabel}: Integer ${parameter.maximum ? `Max Value=${parameter.maximum}` : ""} ${parameter.minimum ? `Max Value=${parameter.minimum}` : ""}`}
                  disabled={disabled}
                  onValueChange={(value) => handleChange(parameter.key, value)}
                  error={parameter.error}
                  max={
                    parameter.maximum !== undefined
                      ? parameter.maximum
                      : undefined
                  }
                  min={
                    parameter.minimum !== undefined
                      ? parameter.minimum
                      : undefined
                  }
                />
              )}

              {parameter?.type === "Float" && (
                <NumberField
                  id={`${parameter.key}-input-id`}
                  value={parameter.value}
                  disabled={disabled}
                  aria-describedby={`${parameter.key}-helper-text`}
                  title={`${inputAreaAriaLabel}: Float ${parameter.maximum ? `Max Value=${parameter.maximum}` : ""} ${parameter.minimum ? `Max Value=${parameter.minimum}` : ""}`}
                  onValueChange={(value) => handleChange(parameter.key, value)}
                  error={parameter.error}
                  max={
                    parameter.maximum !== undefined
                      ? parameter.maximum
                      : undefined
                  }
                  min={
                    parameter.minimum !== undefined
                      ? parameter.minimum
                      : undefined
                  }
                  step={0.01}
                />
              )}

              {parameter?.type === "Boolean" && (
                <Checkbox
                  id={`${parameter.key}-input-id`}
                  checked={parameter.value}
                  slotProps={{
                    input: {
                      "aria-label": `Parameter ${parameter.display_name ?? parameter.key}`,
                      "aria-describedby": `${parameter.key}-helper-text`,
                    },
                  }}
                  indeterminate={
                    parameter.value === undefined
                      ? parameter.nullable || parameter.optional
                      : false
                  }
                  onChange={(e) =>
                    handleChange(parameter.key, e.target.checked)
                  }
                  disabled={disabled}
                />
              )}

              {parameter?.type === "Date" && (
                <LocalizationProvider dateAdapter={AdapterDayjs}>
                  <DatePicker
                    disabled={disabled}
                    value={parameter?.value ? dayjs(parameter.value) : null}
                    onChange={(newValue: PickerValue) => {
                      if (newValue && newValue.isValid()) {
                        handleChange(parameter.key, newValue.valueOf());
                      } else {
                        handleChange(parameter.key, undefined);
                      }
                    }}
                    slotProps={{
                      textField: {
                        id: `${parameter.key}-input-id`,
                        error: parameter.error,
                        slotProps: {
                          input: {
                            "aria-describedby": `${parameter.key}-helper-text`,
                          },
                        },
                      },
                    }}
                  />
                </LocalizationProvider>
              )}

              {parameter?.type === "DateTime" && (
                <LocalizationProvider dateAdapter={AdapterDayjs}>
                  <DateTimePicker
                    disabled={disabled}
                    value={parameter?.value ? dayjs(parameter.value) : null}
                    aria-describedby={`${parameter.key}-helper-text`}
                    onChange={(newValue: PickerValue) => {
                      if (newValue && newValue.isValid()) {
                        handleChange(parameter.key, newValue.valueOf());
                      } else {
                        handleChange(parameter.key, undefined);
                      }
                    }}
                    slotProps={{
                      textField: {
                        id: `${parameter.key}-input-id`,
                        error: parameter.error,
                        slotProps: {
                          input: {
                            "aria-describedby": `${parameter.key}-helper-text`,
                          },
                        },
                      },
                    }}
                  />
                </LocalizationProvider>
              )}

              {parameter?.type === "Bytes" && (
                <Button
                  component="label"
                  role={undefined}
                  disabled={disabled || parameter?.value?.name !== undefined}
                  variant="contained"
                  tabIndex={-1}
                  startIcon={<FAIcon icon="upload" />}
                  aria-describedby={`${parameter.key}-helper-text`}
                >
                  Upload Bytes
                  <VisuallyHiddenInput
                    type="file"
                    onChange={customBytesUploader}
                  />
                </Button>
              )}

              {parameter?.type === "Base64" && (
                <Button
                  component="label"
                  role={undefined}
                  variant="contained"
                  disabled={disabled || uploadPercentage > 0}
                  tabIndex={-1}
                  startIcon={<FAIcon icon="upload" />}
                  aria-describedby={`${parameter.key}-helper-text`}
                >
                  <VisuallyHiddenInput
                    type="file"
                    onChange={customBase64Uploader}
                  />
                  <Stack>
                    <Stack>Upload Base64</Stack>
                    <Stack>
                      {uploadPercentage > 0 && (
                        <LinearProgress
                          variant="buffer"
                          color="secondary"
                          value={uploadPercentage}
                          valueBuffer={uploadPercentageBuffer}
                          aria-label="Uploading File..."
                          sx={{ width: "100%" }}
                        />
                      )}
                    </Stack>
                  </Stack>
                </Button>
              )}
            </Box>
          </Tooltip>
          <FormHelperText
            key={`${parameter.key}-helper-text`}
            id={`${parameter.key}-helper-text`}
            aria-live="polite"
            error={parameter.error}
          >
            {parameter.errorMsg
              ? `${parameter.optional ? "Optional: " : ""}${parameter.description !== undefined && parameter.description !== null ? parameter.description : `Parameter Input ${parameterDisplayName}`}: ${parameter.errorMsg}`
              : `${parameter.optional ? "Optional: " : ""}${parameter.description !== undefined && parameter.description !== null ? parameter.description : `Parameter Input ${parameterDisplayName}`}`}
          </FormHelperText>
        </Box>
      </Box>
    );
  }
}

export default CommandFormField;
