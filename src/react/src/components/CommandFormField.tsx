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
import { ProgressSpinner } from "primereact/progressspinner";
import { ChangeEvent, useEffect, useState } from "react";

import { InputParam } from "../models/models";
import { uploadFile } from "../services/file_service";
import { FAIcon } from "../services/util_service";
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

  const getMultiValue = (key: any, index: any) => {
    parametersFields.forEach((param: InputParam) => {
      if (param.key === key) {
        if (param.value[index]) {
          return param.value[index];
        }
        if (param.default) {
          return param.default;
        }
      }
    });
    return undefined;
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

  const inputAreaAriaLabel = `Parameter Input ${parameter.display_name ?? parameter.key}`;

  const addInputAriaLabel = `Add new value to List for Parameter ${parameter.display_name ?? parameter.key}`;

  const removeInputAriaLabel = `Remove value from List for Parameter ${parameter.display_name ?? parameter.key}`;

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
        <Box
          key={parameter.key}
          sx={{ display: "flex", justifyContent: "flex-end", m: 2 }}
        >
          <Tooltip title={`${inputAreaAriaLabel}: Multi Select`}>
            <span>
              <Select
                id={parameter.key}
                value={parameter.value}
                aria-describedby={`${parameter.key}-helper-text`}
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
                error={
                  !disabled &&
                  !parameter.optional &&
                  (parameter.value === undefined ||
                    parameter.value === null ||
                    parameter.value === "")
                }
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
              <FormHelperText id={`${parameter.key}-helper-text`}>
                {parameter.description}
              </FormHelperText>
            </span>
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
            />
          )}
        </Box>
      );
    }
    return (
      <Box
        key={parameter.key}
        sx={{ display: "flex", justifyContent: "flex-end", m: 2 }}
      >
        <Tooltip title={`${inputAreaAriaLabel}: Dropdown Select`}>
          <span>
            <Select
              id={parameter.key}
              value={parameter.value}
              aria-describedby={`${parameter.key}-helper-text`}
              disabled={
                disabled ||
                parameter.options === undefined ||
                parameter.options.length === 0 ||
                loadingChoices.some(
                  (loading) => loading.key === parameter.key,
                ) ||
                parameter.error
              }
              error={
                !disabled &&
                !parameter.optional &&
                (parameter.value === undefined ||
                  parameter.value === null ||
                  parameter.value === "")
              }
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
            <FormHelperText id={`${parameter.key}-helper-text`}>
              {parameter.description}
            </FormHelperText>
          </span>
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
          />
        )}
      </Box>
    );
  } else if (parameter.choices && parameter.choices?.display === "typeahead") {
    return (
      <Box
        key={parameter.key}
        sx={{ display: "flex", justifyContent: "flex-end", m: 2 }}
      >
        <Autocomplete
          sx={{ width: "100%" }}
          id={parameter.key}
          aria-describedby={`${parameter.key}-helper-text`}
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
          disabled={disabled}
          multiple={parameter?.multi === true}
          renderInput={(params) => (
            <TextField
              {...params}
              variant="outlined"
              placeholder={parameter.display_name}
              error={
                !disabled &&
                !parameter.optional &&
                (parameter.value === undefined ||
                  parameter.value === null ||
                  parameter.value === "")
              }
            />
          )}
        />
        <FormHelperText id={`${parameter.key}-helper-text`}>
          {parameter.description}
        </FormHelperText>
        {loadingChoices &&
          loadingChoices.some((loading) => loading.key === parameter.key) && (
            <ProgressSpinner style={{ width: "34px", height: "34px" }} />
          )}
        {parameter.error && (
          <FontAwesomeIcon
            icon="triangle-exclamation"
            title={parameter.errorMsg ?? "ERROR"}
          />
        )}
      </Box>
    );
  }

  switch (parameter.type) {
    case "Any":
    case "String": {
      if (parameter.multi) {
        return (
          <Container id={parameter.key} key={parameter.key}>
            {parameter.value?.map((item: any, index: any) => (
              <Box
                key={`${parameter.key}-${index}`}
                sx={{ display: "flex", justifyContent: "flex-end", m: 1 }}
              >
                <Tooltip title={`${inputAreaAriaLabel} Index ${index}: String`}>
                  <TextField
                    id={`${parameter.key}-${index}`}
                    helperText={parameter.description}
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
                    error={
                      !disabled &&
                      !parameter.optional &&
                      (item === undefined || item === null || item === "")
                    }
                  />
                </Tooltip>
                <Tooltip title={removeInputAriaLabel}>
                  <IconButton
                    onClick={() => removeMultiItem(parameter.key, index)}
                    disabled={disabled}
                  >
                    <FAIcon icon="xmark" />
                  </IconButton>
                </Tooltip>
              </Box>
            ))}
            <Box sx={{ display: "flex", justifyContent: "flex-end", mr: 2 }}>
              <AccessButton
                label="Add"
                onClick={() => addMultiItem(parameter.key, parameter.default)}
                disabled={disabled}
                tooltip={addInputAriaLabel}
              >
                <Typography variant="button">
                  Add {parameter.display_name ?? parameter.key}
                </Typography>
              </AccessButton>
            </Box>
          </Container>
        );
      }
      return (
        <Box
          key={parameter.key}
          sx={{ display: "flex", justifyContent: "flex-end", m: 2 }}
        >
          <Tooltip title={`${inputAreaAriaLabel}: String`}>
            <TextField
              id={parameter.key}
              value={parameter.value}
              helperText={parameter.description}
              variant="outlined"
              onChange={(event: ChangeEvent<HTMLInputElement>) => {
                handleChange(parameter.key, event.target.value);
              }}
              fullWidth
              disabled={disabled}
              error={
                !disabled &&
                !parameter.optional &&
                (parameter.value === undefined ||
                  parameter.value === null ||
                  parameter.value === "")
              }
            />
          </Tooltip>
        </Box>
      );
    }
    case "Dictionary": {
      const canParseJSON = (str: string) => {
        try {
          JSON.parse(str);
          return true;
        } catch {
          return false;
        }
      };
      if (parameter.multi) {
        return (
          <Container id={parameter.key} key={parameter.key}>
            {parameter.value?.map((item: any, index: any) => (
              <Box
                key={`${parameter.key}-${index}`}
                sx={{ display: "flex", justifyContent: "flex-end", m: 1 }}
              >
                <Tooltip
                  title={`${inputAreaAriaLabel} Index ${index}: Dictionary`}
                >
                  <TextField
                    id={`${parameter.key}-${index}`}
                    value={item}
                    helperText={parameter.description}
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
                    error={
                      !disabled &&
                      !parameter.optional &&
                      (item === undefined ||
                        item === null ||
                        item === "" ||
                        !canParseJSON(item))
                    }
                  />
                </Tooltip>
                <Tooltip title={removeInputAriaLabel}>
                  <IconButton
                    onClick={() => removeMultiItem(parameter.key, index)}
                    disabled={disabled}
                  >
                    <FAIcon icon="xmark" />
                  </IconButton>
                </Tooltip>
              </Box>
            ))}
            <Box sx={{ display: "flex", justifyContent: "flex-end", mr: 2 }}>
              <AccessButton
                label="Add"
                onClick={() => addMultiItem(parameter.key, parameter.default)}
                disabled={disabled}
                tooltip={addInputAriaLabel}
              >
                <Typography variant="button">
                  Add {parameter.display_name ?? parameter.key}
                </Typography>
              </AccessButton>
            </Box>
          </Container>
        );
      }
      return (
        <Box
          key={parameter.key}
          sx={{ display: "flex", justifyContent: "flex-end", m: 2 }}
        >
          <Tooltip title={`${inputAreaAriaLabel}: Dictionary`}>
            <TextField
              id={parameter.key}
              value={parameter.value}
              helperText={parameter.description}
              variant="outlined"
              onChange={(event: ChangeEvent<HTMLInputElement>) => {
                handleChange(parameter.key, event.target.value);
              }}
              fullWidth
              disabled={disabled}
              multiline
              error={
                !disabled &&
                !parameter.optional &&
                (parameter.value === undefined ||
                  parameter.value === null ||
                  parameter.value === "" ||
                  !canParseJSON(parameter.value))
              }
            />
          </Tooltip>
        </Box>
      );
    }
    case "Integer": {
      if (parameter.multi) {
        return (
          <Container id={parameter.key} key={parameter.key}>
            {parameter.value?.map((item: any, index: any) => (
              <Box
                key={`${parameter.key}-${index}`}
                sx={{ display: "flex", justifyContent: "flex-end", m: 1 }}
              >
                <Tooltip
                  title={`${inputAreaAriaLabel} Index ${index}: Integer ${parameter.maximum ? `Max Value=${parameter.maximum}` : ""} ${parameter.minimum ? `Max Value=${parameter.minimum}` : ""}`}
                >
                  <NumberField
                    id={`${parameter.key}-${index}`}
                    value={
                      getMultiValue(parameter.key, index) ?? parameter.default
                    }
                    helperText={parameter.description}
                    disabled={disabled}
                    onValueChange={(value) =>
                      handleMultiChange(parameter.key, value, index)
                    }
                    error={
                      !disabled &&
                      !parameter.optional &&
                      (item === undefined || item === null || item === "")
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
                </Tooltip>
                <Tooltip title={removeInputAriaLabel}>
                  <IconButton
                    onClick={() => removeMultiItem(parameter.key, index)}
                    disabled={disabled}
                  >
                    <FAIcon icon="xmark" />
                  </IconButton>
                </Tooltip>
              </Box>
            ))}
            <Box sx={{ display: "flex", justifyContent: "flex-end", mr: 2 }}>
              <AccessButton
                label="Add"
                onClick={() => addMultiItem(parameter.key, parameter.default)}
                disabled={disabled}
                tooltip={addInputAriaLabel}
              >
                <Typography variant="button">
                  Add {parameter.display_name ?? parameter.key}
                </Typography>
              </AccessButton>
            </Box>
          </Container>
        );
      }
      return (
        <Box
          key={parameter.key}
          sx={{ display: "flex", justifyContent: "flex-end", m: 2 }}
        >
          <Tooltip
            title={`${inputAreaAriaLabel}: Integer ${parameter.maximum ? `Max Value=${parameter.maximum}` : ""} ${parameter.minimum ? `Max Value=${parameter.minimum}` : ""}`}
          >
            <NumberField
              id={parameter.key}
              value={parameter.value}
              helperText={parameter.description}
              disabled={disabled}
              onValueChange={(value) => handleChange(parameter.key, value)}
              error={
                !disabled &&
                !parameter.optional &&
                (parameter.value === undefined ||
                  parameter.value === null ||
                  parameter.value === "")
              }
              max={
                parameter.maximum !== undefined ? parameter.maximum : undefined
              }
              min={
                parameter.minimum !== undefined ? parameter.minimum : undefined
              }
            />
          </Tooltip>
        </Box>
      );
    }
    case "Float": {
      if (parameter.multi) {
        return (
          <Container id={parameter.key} key={parameter.key}>
            {parameter.value?.map((item: any, index: any) => (
              <Box
                key={`${parameter.key}-${index}`}
                sx={{ display: "flex", justifyContent: "flex-end", m: 1 }}
              >
                <Tooltip
                  title={`${inputAreaAriaLabel} Index ${index}: Float ${parameter.maximum ? `Max Value=${parameter.maximum}` : ""} ${parameter.minimum ? `Max Value=${parameter.minimum}` : ""}`}
                >
                  <NumberField
                    id={`${parameter.key}-${index}`}
                    value={
                      getMultiValue(parameter.key, index) ?? parameter.default
                    }
                    helperText={parameter.description}
                    disabled={disabled}
                    onValueChange={(value) =>
                      handleMultiChange(parameter.key, value, index)
                    }
                    error={
                      !disabled &&
                      !parameter.optional &&
                      (item === undefined || item === null || item === "")
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
                </Tooltip>
                <Tooltip title={removeInputAriaLabel}>
                  <IconButton
                    onClick={() => removeMultiItem(parameter.key, index)}
                    disabled={disabled}
                  >
                    <FAIcon icon="xmark" />
                  </IconButton>
                </Tooltip>
              </Box>
            ))}
            <Box sx={{ display: "flex", justifyContent: "flex-end", mr: 2 }}>
              <AccessButton
                label="Add"
                onClick={() => addMultiItem(parameter.key, parameter.default)}
                disabled={disabled}
                tooltip={addInputAriaLabel}
              >
                <Typography variant="button">
                  Add {parameter.display_name ?? parameter.key}
                </Typography>
              </AccessButton>
            </Box>
          </Container>
        );
      }
      return (
        <Box
          key={parameter.key}
          sx={{ display: "flex", justifyContent: "flex-end", m: 2 }}
        >
          <Tooltip
            title={`${inputAreaAriaLabel}: Float ${parameter.maximum ? `Max Value=${parameter.maximum}` : ""} ${parameter.minimum ? `Max Value=${parameter.minimum}` : ""}`}
          >
            <NumberField
              id={parameter.key}
              value={parameter.value}
              helperText={parameter.description}
              disabled={disabled}
              onValueChange={(value) => handleChange(parameter.key, value)}
              error={
                !disabled &&
                !parameter.optional &&
                (parameter.value === undefined ||
                  parameter.value === null ||
                  parameter.value === "")
              }
              max={
                parameter.maximum !== undefined ? parameter.maximum : undefined
              }
              min={
                parameter.minimum !== undefined ? parameter.minimum : undefined
              }
              step={0.01}
            />
          </Tooltip>
        </Box>
      );
    }
    case "Boolean": {
      if (parameter.multi) {
        return (
          <Container id={parameter.key} key={parameter.key}>
            {parameter.value?.map((item: any, index: any) => (
              <Box
                key={`${parameter.key}-${index}`}
                sx={{ display: "flex", justifyContent: "flex-end", m: 1 }}
              >
                <Tooltip
                  title={`${inputAreaAriaLabel} Boolean ${index}: String`}
                >
                  <span>
                    <Checkbox
                      id={`${parameter.key}-${index}`}
                      checked={item}
                      aria-describedby={`${parameter.key}-${index}-helper-text`}
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
                    <FormHelperText
                      id={`${parameter.key}-${index}-helper-text`}
                    >
                      {parameter.description}
                    </FormHelperText>
                  </span>
                </Tooltip>
                <Tooltip title={removeInputAriaLabel}>
                  <IconButton
                    onClick={() => removeMultiItem(parameter.key, index)}
                    disabled={disabled}
                  >
                    <FAIcon icon="xmark" />
                  </IconButton>
                </Tooltip>
              </Box>
            ))}
            <Box sx={{ display: "flex", justifyContent: "flex-end", mr: 2 }}>
              <AccessButton
                label="Add"
                onClick={() => addMultiItem(parameter.key, parameter.default)}
                disabled={disabled}
                tooltip={addInputAriaLabel}
              >
                <Typography variant="button">
                  Add {parameter.display_name ?? parameter.key}
                </Typography>
              </AccessButton>
            </Box>
          </Container>
        );
      }
      return (
        <Box
          key={parameter.key}
          sx={{ display: "flex", justifyContent: "flex-end", m: 2 }}
        >
          <Tooltip title={`${inputAreaAriaLabel}: Boolean`}>
            <span>
              <Checkbox
                id={parameter.key}
                checked={parameter.value}
                aria-describedby={`${parameter.key}-helper-text`}
                indeterminate={
                  parameter.value === undefined
                    ? parameter.nullable || parameter.optional
                    : false
                }
                onChange={(e) => handleChange(parameter.key, e.target.checked)}
                disabled={disabled}
              />
              <FormHelperText id={`${parameter.key}-helper-text`}>
                {parameter.description}
              </FormHelperText>
            </span>
          </Tooltip>
        </Box>
      );
    }
    case "Date": {
      if (parameter.multi) {
        return (
          <Container id={parameter.key} key={parameter.key}>
            {parameter.value?.map((item: any, index: any) => (
              <Box
                key={`${parameter.key}-${index}`}
                sx={{ display: "flex", justifyContent: "flex-end", m: 1 }}
              >
                <Tooltip title={`${inputAreaAriaLabel} Index ${index}: Date`}>
                  <span>
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
                            id: parameter.key,
                            error:
                              !disabled &&
                              !parameter.optional &&
                              (item === undefined ||
                                item === null ||
                                item === ""),
                          },
                        }}
                      />
                    </LocalizationProvider>
                    <FormHelperText id={`${parameter.key}-helper-text`}>
                      {parameter.description}
                    </FormHelperText>
                  </span>
                </Tooltip>
                <Tooltip title={removeInputAriaLabel}>
                  <IconButton
                    onClick={() => removeMultiItem(parameter.key, index)}
                    disabled={disabled}
                  >
                    <FAIcon icon="xmark" />
                  </IconButton>
                </Tooltip>
              </Box>
            ))}
            <Box sx={{ display: "flex", justifyContent: "flex-end", mr: 2 }}>
              <AccessButton
                label="Add"
                onClick={() => addMultiItem(parameter.key, parameter.default)}
                disabled={disabled}
                tooltip={addInputAriaLabel}
              >
                <Typography variant="button">
                  Add {parameter.display_name ?? parameter.key}
                </Typography>
              </AccessButton>
            </Box>
          </Container>
        );
      }
      return (
        <Box
          key={parameter.key}
          sx={{ display: "flex", justifyContent: "flex-end", m: 2 }}
        >
          <Tooltip title={`${inputAreaAriaLabel}: Date`}>
            <span>
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
                      id: parameter.key,
                      error:
                        !disabled &&
                        !parameter.optional &&
                        (parameter.value === undefined ||
                          parameter.value === null ||
                          parameter.value === ""),
                    },
                  }}
                />
              </LocalizationProvider>
              <FormHelperText id={`${parameter.key}-helper-text`}>
                {parameter.description}
              </FormHelperText>
            </span>
          </Tooltip>
        </Box>
      );
    }
    case "DateTime": {
      if (parameter.multi) {
        return (
          <Container id={parameter.key} key={parameter.key}>
            {parameter.value?.map((item: any, index: any) => (
              <Box
                key={`${parameter.key}-${index}`}
                sx={{ display: "flex", justifyContent: "flex-end", m: 1 }}
              >
                <Tooltip
                  title={`${inputAreaAriaLabel} Index ${index}: DateTime`}
                >
                  <span>
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
                            id: parameter.key,

                            error:
                              !disabled &&
                              !parameter.optional &&
                              (item === undefined ||
                                item === null ||
                                item === ""),
                          },
                        }}
                      />
                    </LocalizationProvider>
                    <FormHelperText id={`${parameter.key}-helper-text`}>
                      {parameter.description}
                    </FormHelperText>
                  </span>
                </Tooltip>
                <Tooltip title={removeInputAriaLabel}>
                  <IconButton
                    onClick={() => removeMultiItem(parameter.key, index)}
                    disabled={disabled}
                  >
                    <FAIcon icon="xmark" />
                  </IconButton>
                </Tooltip>
              </Box>
            ))}
            <Box sx={{ display: "flex", justifyContent: "flex-end", mr: 2 }}>
              <AccessButton
                label="Add"
                onClick={() => addMultiItem(parameter.key, parameter.default)}
                disabled={disabled}
                tooltip={addInputAriaLabel}
              >
                <Typography variant="button">
                  Add {parameter.display_name ?? parameter.key}
                </Typography>
              </AccessButton>
            </Box>
          </Container>
        );
      }
      return (
        <Box
          key={parameter.key}
          sx={{ display: "flex", justifyContent: "flex-end", m: 2 }}
        >
          <Tooltip title={`${inputAreaAriaLabel}: DateTime`}>
            <span>
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
                      id: parameter.key,
                      error:
                        !disabled &&
                        !parameter.optional &&
                        (parameter.value === undefined ||
                          parameter.value === null ||
                          parameter.value === ""),
                    },
                  }}
                />
              </LocalizationProvider>
              <FormHelperText id={`${parameter.key}-helper-text`}>
                {parameter.description}
              </FormHelperText>
            </span>
          </Tooltip>
        </Box>
      );
    }
    case "Bytes": {
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

      return (
        <Box
          key={parameter.key}
          sx={{ display: "flex", justifyContent: "flex-end", m: 2 }}
        >
          {parameter?.value?.name && (
            <IconButton onClick={() => handleChange(parameter.key, undefined)}>
              <Typography variant="caption">
                {parameter?.value?.name}
              </Typography>
              <FAIcon icon="xmark" sx={{ ml: 1 }} />
            </IconButton>
          )}
          <Tooltip title={`${inputAreaAriaLabel}: Bytes`}>
            <span>
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
              <FormHelperText id={`${parameter.key}-helper-text`}>
                {parameter.description}
              </FormHelperText>
            </span>
          </Tooltip>
        </Box>
      );
    }
    case "Base64": {
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

      return (
        <Box
          key={parameter.key}
          sx={{ display: "flex", justifyContent: "flex-end", m: 2 }}
        >
          {uploadPercentage === 100 && (
            <IconButton onClick={removeFile}>
              <Typography variant="caption">
                {parameter?.value?.details?.file_name}
              </Typography>
              <FAIcon icon="xmark" sx={{ ml: 1 }} />
            </IconButton>
          )}
          <Tooltip title={`${inputAreaAriaLabel}: Base64`}>
            <span>
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
              <FormHelperText id={`${parameter.key}-helper-text`}>
                {parameter.description}
              </FormHelperText>
            </span>
          </Tooltip>
        </Box>
      );
    }
    default: {
      return null;
    }
  }
}

export default CommandFormField;
