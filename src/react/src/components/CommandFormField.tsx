import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  Box,
  Checkbox,
  Container,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import Autocomplete from "@mui/material/Autocomplete";
import { Calendar } from "primereact/calendar";
import { Dropdown } from "primereact/dropdown";
import { FileUpload, FileUploadFile } from "primereact/fileupload";
import { MultiSelect } from "primereact/multiselect";
import { ProgressBar } from "primereact/progressbar";
import { ProgressSpinner } from "primereact/progressspinner";
import { ChangeEvent, useEffect, useRef, useState } from "react";
import { v4 as uuidv4 } from "uuid";

import { InputParam } from "../models/models";
import { uploadFile } from "../services/file_service";
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
  const fileUploadRef = useRef<FileUpload>(null);

  // Bytes Stateful Objects
  const bytesUploadRef = useRef<FileUpload>(null);

  // Bytes and Base64 Triggers
  useEffect(() => {
    if (bytesUploadRef && bytesUploadRef.current) {
      bytesUploadRef.current.clear();
    }

    if (uploadPercentage !== 0) {
      setUploadPercentage(0);
    }
    if (fileUploadRef && fileUploadRef.current) {
      fileUploadRef.current.clear();
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
        <div key={parameter.key} className="p-field">
          <MultiSelect
            id={parameter.key}
            value={parameter.value}
            options={parameter.options}
            invalid={
              (!disabled &&
                !parameter.optional &&
                (parameter.value === undefined ||
                  parameter.value === null ||
                  parameter.value === "")) ||
              undefined
            }
            onChange={(e) =>
              handleChange(
                e.target.id,
                e.value.filter((option: string) =>
                  parameter.options?.some((opt) => opt.value === option),
                ),
              )
            }
            placeholder={`Select ${parameter.key}`}
            selectAllLabel={`Select all options for ${parameter.display_name ?? parameter.key}`}
            tooltip={`${inputAreaAriaLabel}: Multi Select`}
            disabled={
              disabled ||
              parameter.options === undefined ||
              parameter.options.length === 0 ||
              loadingChoices.some((loading) => loading.key === parameter.key) ||
              parameter.error
            }
            pt={{
              checkbox: (data: any) => {
                if (
                  data?.context?.index &&
                  parameter.options &&
                  parameter.options[data.context.index]
                ) {
                  return {
                    input: {
                      "aria-label": `${inputAreaAriaLabel}: Multiselect Option Checkbox: ${parameter.options[data.context.index].label}`,
                    },
                  };
                } else {
                  return {
                    input: {
                      "aria-label": `${inputAreaAriaLabel}: Multiselect Option Checkbox with random UUID generated ${uuidv4()}`,
                    },
                  };
                }
              },
            }}
          />
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
        </div>
      );
    }
    return (
      <div key={parameter.key} className="p-field">
        <datalist id={`select${parameter.key}Dropdown`} aria-hidden="true">
          {parameter.options?.map((status: any) => (
            <option key={status.label} value={status.value} />
          ))}
        </datalist>
        <Dropdown
          id={parameter.key}
          value={parameter.value}
          options={parameter.options}
          invalid={
            (!disabled &&
              !parameter.optional &&
              (parameter.value === undefined ||
                parameter.value === null ||
                parameter.value === "")) ||
            undefined
          }
          onChange={(e) => handleChange(e.target.id, e.value)}
          placeholder={`Select ${parameter.key}`}
          tooltip={`${inputAreaAriaLabel}: Dropdown Select`}
          disabled={
            disabled ||
            parameter.options === undefined ||
            parameter.options.length === 0 ||
            loadingChoices.some((loading) => loading.key === parameter.key)
          }
          pt={{
            select: {
              "aria-controls": `select${parameter.key}Dropdown`,
            },
          }}
        />
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
      </div>
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
              <Box key={`${parameter.key}-${index}`} sx={{ m: 1 }}>
                <Box sx={{ display: "flex", justifyContent: "flex-end", m: 1 }}>
                  <Tooltip
                    title={`${inputAreaAriaLabel} Index ${index}: String`}
                  >
                    <TextField
                      id={`${parameter.key}-${index}`}
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
                </Box>
                <Box sx={{ display: "flex", justifyContent: "flex-end", m: 1 }}>
                  <AccessButton
                    label="Remove"
                    color="warning"
                    onClick={() => removeMultiItem(parameter.key, index)}
                    disabled={disabled}
                    tooltip={`${removeInputAriaLabel} Index ${index}`}
                  >
                    <Typography variant="button">Remove</Typography>
                  </AccessButton>
                </Box>
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
              <Box key={`${parameter.key}-${index}`} sx={{ m: 1 }}>
                <Box sx={{ display: "flex", justifyContent: "flex-end", m: 1 }}>
                  <Tooltip
                    title={`${inputAreaAriaLabel} Index ${index}: Dictionary`}
                  >
                    <TextField
                      id={`${parameter.key}-${index}`}
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
                </Box>
                <Box sx={{ display: "flex", justifyContent: "flex-end", m: 1 }}>
                  <AccessButton
                    label="Remove"
                    color="warning"
                    onClick={() => removeMultiItem(parameter.key, index)}
                    disabled={disabled}
                    tooltip={`${removeInputAriaLabel} Index ${index}`}
                  >
                    <Typography variant="button">Remove</Typography>
                  </AccessButton>
                </Box>
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
              <Box key={`${parameter.key}-${index}`} sx={{ m: 1 }}>
                <Box sx={{ display: "flex", justifyContent: "flex-end", m: 1 }}>
                  <Tooltip
                    title={`${inputAreaAriaLabel} Index ${index}: Integer ${parameter.maximum ? `Max Value=${parameter.maximum}` : ""} ${parameter.minimum ? `Max Value=${parameter.minimum}` : ""}`}
                  >
                    <NumberField
                      id={`${parameter.key}-${index}`}
                      value={
                        getMultiValue(parameter.key, index) ?? parameter.default
                      }
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
                </Box>
                <Box sx={{ display: "flex", justifyContent: "flex-end", m: 1 }}>
                  <AccessButton
                    label="Remove"
                    color="warning"
                    onClick={() => removeMultiItem(parameter.key, index)}
                    disabled={disabled}
                    tooltip={`${removeInputAriaLabel} Index ${index}`}
                  >
                    <Typography variant="button">Remove</Typography>
                  </AccessButton>
                </Box>
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
              <Box key={`${parameter.key}-${index}`} sx={{ m: 1 }}>
                <Box sx={{ display: "flex", justifyContent: "flex-end", m: 1 }}>
                  <Tooltip
                    title={`${inputAreaAriaLabel} Index ${index}: Float ${parameter.maximum ? `Max Value=${parameter.maximum}` : ""} ${parameter.minimum ? `Max Value=${parameter.minimum}` : ""}`}
                  >
                    <NumberField
                      id={`${parameter.key}-${index}`}
                      value={
                        getMultiValue(parameter.key, index) ?? parameter.default
                      }
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
                </Box>
                <Box sx={{ display: "flex", justifyContent: "flex-end", m: 1 }}>
                  <AccessButton
                    label="Remove"
                    color="warning"
                    onClick={() => removeMultiItem(parameter.key, index)}
                    disabled={disabled}
                    tooltip={`${removeInputAriaLabel} Index ${index}`}
                  >
                    <Typography variant="button">Remove</Typography>
                  </AccessButton>
                </Box>
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
              <Box key={`${parameter.key}-${index}`} sx={{ m: 1 }}>
                <Box sx={{ display: "flex", justifyContent: "flex-end", m: 1 }}>
                  <Tooltip
                    title={`${inputAreaAriaLabel} Boolean ${index}: String`}
                  >
                    <Checkbox
                      id={`${parameter.key}-${index}`}
                      checked={item}
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
                  </Tooltip>
                </Box>
                <Box sx={{ display: "flex", justifyContent: "flex-end", m: 1 }}>
                  <AccessButton
                    label="Remove"
                    color="warning"
                    onClick={() => removeMultiItem(parameter.key, index)}
                    disabled={disabled}
                    tooltip={`${removeInputAriaLabel} Index ${index}`}
                  >
                    <Typography variant="button">Remove</Typography>
                  </AccessButton>
                </Box>
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
            <Checkbox
              id={parameter.key}
              checked={parameter.value}
              indeterminate={
                parameter.value === undefined
                  ? parameter.nullable || parameter.optional
                  : false
              }
              onChange={(e) => handleChange(parameter.key, e.target.checked)}
              disabled={disabled}
            />
          </Tooltip>
        </Box>
      );
    }
    case "Date": {
      if (parameter.multi) {
        return (
          <div id={parameter.key} key={parameter.key} className="p-field">
            <div className="container">
              {parameter.value?.map((item: any, index: any) => (
                <div key={`${parameter.key}-${index}`} className="dynamic-item">
                  <Calendar
                    id={`${parameter.key}-${index}`}
                    value={item}
                    invalid={
                      (!disabled &&
                        !parameter.optional &&
                        (item === undefined || item === null || item === "")) ||
                      undefined
                    }
                    hourFormat="24"
                    onChange={(e) =>
                      handleMultiChange(parameter.key, e.value, index)
                    }
                    disabled={disabled}
                    tooltip={`${inputAreaAriaLabel} Index ${index}: Date`}
                  />
                  <AccessButton
                    label="Remove"
                    severity="danger"
                    onClick={() => removeMultiItem(parameter.key, index)}
                    disabled={disabled}
                    tooltip={`${removeInputAriaLabel} Index ${index}`}
                  />
                </div>
              ))}
              <AccessButton
                label="Add"
                onClick={() => addMultiItem(parameter.key, parameter.default)}
                disabled={disabled}
                tooltip={addInputAriaLabel}
              />
            </div>
          </div>
        );
      }
      return (
        <div key={parameter.key} className="p-field">
          <Calendar
            id={parameter.key}
            value={parameter.value || ""}
            invalid={
              (!disabled &&
                !parameter.optional &&
                (parameter.value === undefined ||
                  parameter.value === null ||
                  parameter.value === "")) ||
              undefined
            }
            hourFormat="24"
            onChange={(e: any) => handleChange(e.target.id, e.value)}
            disabled={disabled}
            tooltip={`${inputAreaAriaLabel}: Date`}
          />
        </div>
      );
    }
    case "DateTime": {
      if (parameter.multi) {
        return (
          <div id={parameter.key} key={parameter.key} className="p-field">
            <div className="container">
              {parameter.value?.map((item: any, index: any) => (
                <div key={`${parameter.key}-${index}`} className="dynamic-item">
                  <Calendar
                    id={`${parameter.key}-${index}`}
                    value={item ?? parameter.default}
                    invalid={
                      (!disabled &&
                        !parameter.optional &&
                        (item === undefined || item === null || item === "")) ||
                      undefined
                    }
                    showTime
                    hourFormat="24"
                    onChange={(e) =>
                      handleMultiChange(parameter.key, e.value, index)
                    }
                    disabled={disabled}
                    tooltip={`${inputAreaAriaLabel} Index ${index}: DateTime`}
                  />
                  <AccessButton
                    label="Remove"
                    severity="danger"
                    onClick={() => removeMultiItem(parameter.key, index)}
                    disabled={disabled}
                    tooltip={`${removeInputAriaLabel} Index ${index}`}
                  />
                </div>
              ))}
              <AccessButton
                label="Add"
                onClick={() => addMultiItem(parameter.key, parameter.default)}
                disabled={disabled}
                tooltip={addInputAriaLabel}
              />
            </div>
          </div>
        );
      }
      return (
        <div key={parameter.key} className="p-field">
          <Calendar
            id={parameter.key}
            value={parameter.value}
            showTime
            hourFormat="24"
            invalid={
              (!disabled &&
                !parameter.optional &&
                (parameter.value === undefined ||
                  parameter.value === null ||
                  parameter.value === "")) ||
              undefined
            }
            onChange={(e: any) => handleChange(e.target.id, e.value)}
            disabled={disabled}
            tooltip={`${inputAreaAriaLabel}: DateTime`}
          />
        </div>
      );
    }
    case "Bytes": {
      const customBytesUploader = (event: any) => {
        const file = event.files[0];
        handleChange(parameter.key, file as FileUploadFile);
      };

      return (
        <div id={parameter.key} key={parameter.key} className="p-field">
          <FileUpload
            id={parameter.key}
            ref={bytesUploadRef}
            mode="basic"
            customUpload
            onSelect={customBytesUploader}
            disabled={disabled}
          />
        </div>
      );
    }
    case "Base64": {
      const customBase64Uploader = async (event: any) => {
        if (fileUploadRef && fileUploadRef.current) {
          fileUploadRef.current.setUploadedFiles([]);
        }
        const file = event.files[0];

        const fileUploadResult = await uploadFile(file, setUploadPercentage);

        handleChange(parameter.key, fileUploadResult);
        if (fileUploadRef && fileUploadRef.current) {
          fileUploadRef.current.clear();
          fileUploadRef.current.setUploadedFiles([file]);
        }
        setUploadPercentage(100);
      };

      const removeFile = () => {
        handleChange(parameter.key, null);
        setUploadPercentage(0);
        if (fileUploadRef && fileUploadRef.current) {
          fileUploadRef.current.clear();
        }
      };

      return (
        <div id={parameter.key} key={parameter.key} className="p-field">
          <FileUpload
            id={parameter.key}
            ref={fileUploadRef}
            // mode="basic"
            customUpload
            auto
            uploadHandler={customBase64Uploader}
            onRemove={removeFile}
            disabled={disabled}
            progressBarTemplate={
              <ProgressBar
                value={uploadPercentage}
                displayValueTemplate={() => `${uploadPercentage}%`}
              />
            }
          />
        </div>
      );
    }
    default: {
      return null;
    }
  }
}

export default CommandFormField;
