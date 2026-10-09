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

  const [error, setError] = useState(false);
  const [errorIndex, setErrorIndex] = useState<number[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | undefined>(
    undefined,
  );

  // Bytes and Base64 Triggers
  useEffect(() => {
    if (uploadPercentage !== 0) {
      setUploadPercentage(0);
    }
  }, [resetForm]);

  useEffect(() => {
    updateError();
  }, [parameter]);

  const canParseJSON = (str: string) => {
    try {
      JSON.parse(str);
      return true;
    } catch {
      return false;
    }
  };

  const updateError = () => {
    if (disabled || parameter.optional) {
      setError(false);
      setErrorMessage(undefined);
      return;
    }

    const isList = Array.isArray(parameter.value);

    let updatedErrorMessage = undefined as string | undefined;
    const updatedInvalidIndexes = [] as number[];

    if (
      parameter.value === undefined ||
      parameter.value === null ||
      parameter.value === ""
    ) {
      updatedErrorMessage = "Missing Value";
    }

    if (updatedErrorMessage === undefined) {
      if (
        parameter.choices &&
        (parameter.choices.display === undefined ||
          parameter.choices.display === "select")
      ) {
        // skip
      } else if (
        parameter.choices &&
        parameter.choices?.display === "typeahead"
      ) {
        if (parameter.options === undefined) {
          updatedErrorMessage = "Missing Options";
        } else if (
          !parameter.options.some((option) => option.value === parameter.value)
        ) {
          updatedErrorMessage = "Mismatch value from valid Options";
        }
      } else if (parameter.type === "Dictionary") {
        if (isList) {
          if (
            parameter?.value.some(
              (item: any) => item === "null" || !canParseJSON(item),
            )
          ) {
            const invalidIndexes = [] as string[];
            parameter?.value.map((value: any, index: number) => {
              if (
                value === undefined ||
                value === null ||
                value === "" ||
                value === "null"
              ) {
                invalidIndexes.push(`Index ${index} Missing`);
                updatedInvalidIndexes.push(index);
              } else if (!canParseJSON(value)) {
                invalidIndexes.push(`Index ${index} Invalid JSON`);
                updatedInvalidIndexes.push(index);
              }
            });
            updatedErrorMessage = `Invalid Values: ${invalidIndexes.join(", ")}`;
          }
        } else {
          if (parameter.value === "null") {
            updatedErrorMessage = "Missing Value";
          } else if (!canParseJSON(parameter.value)) {
            updatedErrorMessage = "Invalid JSON";
          }
        }
      }
    }

    if (isList && updatedErrorMessage === undefined) {
      if (parameter.value.length === 0) {
        updatedErrorMessage = "Missing Value";
      } else if (
        parameter.value.some(
          (value: any) => value === undefined || value === null || value === "",
        )
      ) {
        const invalidIndexes = [] as string[];
        parameter?.value.map((value: any, index: number) => {
          if (value === undefined || value === null || value === "") {
            invalidIndexes.push(`Index ${index} Missing`);
            updatedInvalidIndexes.push(index);
          }
        });
        updatedErrorMessage = `Invalid Values: ${invalidIndexes.join(", ")}`;
      }
    }

    setError(updatedErrorMessage !== undefined);
    setErrorMessage(updatedErrorMessage);
    setErrorIndex(updatedInvalidIndexes);
  };

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
        newItems.push(param_default || null);
        handleChange(key, newItems);
      }
    });
  };

  const inputAreaAriaLabel = `${parameter.optional ? "Optional: " : ""}Parameter Input ${parameter.display_name ?? parameter.key}`;

  const addInputAriaLabel = `Add new value to List for Parameter ${parameter.display_name ?? parameter.key}`;

  const removeInputAriaLabel = `Remove value from List for Parameter ${parameter.display_name ?? parameter.key}`;

  // Multi Item Formatting
  const inputDisplayContainerStyling = {
    mx: 1,
  };

  const inputDisplayItemStyling = {
    display: "flex",
    justifyContent: "flex-end",
    my: 1,
  };

  const inputAddButtonStyling = {
    display: "flex",
    justifyContent: "flex-end",
  };

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
                error={error}
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
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
              <FormHelperText
                key={`${parameter.key}-helper-text`}
                aria-live="polite"
                error={error}
              >
                {errorMessage
                  ? `${parameter.optional ? "Optional: " : ""}${parameter.description}: ${errorMessage}`
                  : `${parameter.optional ? "Optional: " : ""}${parameter.description}`}
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
              error={error}
              inputProps={{
                "aria-label": inputAreaAriaLabel,
              }}
              onChange={(event) => {
                handleChange(parameter.key, event.target.value);
              }}
            >
              {parameter.options?.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
            <FormHelperText
              key={`${parameter.key}-helper-text`}
              aria-live="polite"
              error={error}
            >
              {errorMessage
                ? `${parameter.optional ? "Optional: " : ""}${parameter.description}: ${errorMessage}`
                : `${parameter.optional ? "Optional: " : ""}${parameter.description}`}
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
                  error={error}
                  autoComplete="off"
                />
              </Box>
            </Tooltip>
          )}
        />

        <FormHelperText
          key={`${parameter.key}-helper-text`}
          aria-live="polite"
          error={error}
        >
          {errorMessage
            ? `${parameter.optional ? "Optional: " : ""}${parameter.description}: ${errorMessage}`
            : `${parameter.optional ? "Optional: " : ""}${parameter.description}`}
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
      <Container
        key={parameter.key}
        id={parameter.key}
        sx={inputDisplayContainerStyling}
      >
        {parameter.value?.map((item: any, index: any) => (
          <Box key={`${parameter.key}-${index}`} sx={inputDisplayItemStyling}>
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
                    fullWidth
                    disabled={disabled}
                    error={error && errorIndex && errorIndex.includes(index)}
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
                    fullWidth
                    multiline
                    disabled={disabled}
                    error={error && errorIndex && errorIndex.includes(index)}
                    autoComplete="off"
                  />
                )}

                {parameter?.type === "Integer" && (
                  <NumberField
                    id={`${parameter.key}-${index}-input-id`}
                    value={item ?? parameter.default}
                    title={`${inputAreaAriaLabel} Index ${index}: Integer ${parameter.maximum ? `Max Value=${parameter.maximum}` : ""} ${parameter.minimum ? `Max Value=${parameter.minimum}` : ""}`}
                    disabled={disabled}
                    onValueChange={(value) =>
                      handleMultiChange(parameter.key, value, index)
                    }
                    error={error && errorIndex && errorIndex.includes(index)}
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
                    value={item ?? parameter.default}
                    disabled={disabled}
                    title={`${inputAreaAriaLabel} Index ${index}: Float ${parameter.maximum ? `Max Value=${parameter.maximum}` : ""} ${parameter.minimum ? `Max Value=${parameter.minimum}` : ""}`}
                    onValueChange={(value) =>
                      handleMultiChange(parameter.key, value, index)
                    }
                    error={error && errorIndex && errorIndex.includes(index)}
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
                      handleMultiChange(parameter.key, e.target.checked, index)
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
                            error && errorIndex && errorIndex.includes(index),
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
                            error && errorIndex && errorIndex.includes(index),
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
        ))}
        <FormHelperText
          key={`${parameter.key}-helper-text`}
          aria-live="polite"
          error={error}
          sx={inputDisplayStyling}
        >
          {errorMessage
            ? `${parameter.optional ? "Optional: " : ""}${parameter.description}: ${errorMessage}`
            : `${parameter.optional ? "Optional: " : ""}${parameter.description}`}
        </FormHelperText>
        <Box sx={inputAddButtonStyling}>
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
                  fullWidth
                  disabled={disabled}
                  error={error}
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
                  fullWidth
                  disabled={disabled}
                  multiline
                  error={error}
                  autoComplete="off"
                />
              )}

              {parameter?.type === "Integer" && (
                <NumberField
                  id={`${parameter.key}-input-id`}
                  value={parameter.value}
                  title={`${inputAreaAriaLabel}: Integer ${parameter.maximum ? `Max Value=${parameter.maximum}` : ""} ${parameter.minimum ? `Max Value=${parameter.minimum}` : ""}`}
                  disabled={disabled}
                  onValueChange={(value) => handleChange(parameter.key, value)}
                  error={error}
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
                  title={`${inputAreaAriaLabel}: Float ${parameter.maximum ? `Max Value=${parameter.maximum}` : ""} ${parameter.minimum ? `Max Value=${parameter.minimum}` : ""}`}
                  onValueChange={(value) => handleChange(parameter.key, value)}
                  error={error}
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
                        error: error,
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
                        error: error,
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
            aria-live="polite"
            error={error}
          >
            {errorMessage
              ? `${parameter.optional ? "Optional: " : ""}${parameter.description}: ${errorMessage}`
              : `${parameter.optional ? "Optional: " : ""}${parameter.description}`}
          </FormHelperText>
        </Box>
      </Box>
    );
  }
}

export default CommandFormField;
