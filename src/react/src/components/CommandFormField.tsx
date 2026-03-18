import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { AutoComplete } from "primereact/autocomplete";
import { Button } from "primereact/button";
import { Calendar } from "primereact/calendar";
import { Checkbox } from "primereact/checkbox";
import { Dropdown } from "primereact/dropdown";
import { FileUpload, FileUploadFile } from "primereact/fileupload";
import { InputNumber } from "primereact/inputnumber";
import { InputText } from "primereact/inputtext";
import { InputTextarea } from "primereact/inputtextarea";
import { MultiSelect } from "primereact/multiselect";
import { ProgressBar } from "primereact/progressbar";
import { ProgressSpinner } from "primereact/progressspinner";
import { TriStateCheckbox } from "primereact/tristatecheckbox";
import { classNames } from "primereact/utils";
import { useEffect, useRef, useState } from "react";

import { InputParam } from "../models/models";
import { uploadFile } from "../services/file_service";

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

  if (!parameter.key) return null;

  if (parameter.multi && !Array.isArray(parameter.default)) {
    parameter.default = [parameter.default];
  }

  if (parameter.multi && !Array.isArray(parameter.value)) {
    parameter.value = [parameter.value];
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
            invalid={(!disabled && parameter.optional) || undefined}
            onChange={(e) => handleChange(e.target.id, e.value)}
            placeholder={`Select ${parameter.key}`}
            disabled={
              disabled ||
              parameter.options === undefined ||
              parameter.options.length === 0 ||
              loadingChoices.some((loading) => loading.key === parameter.key) ||
              parameter.error
            }
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
        <Dropdown
          id={parameter.key}
          value={parameter.value}
          options={parameter.options}
          invalid={(!disabled && parameter.optional) || undefined}
          onChange={(e) => handleChange(e.target.id, e.value)}
          placeholder={`Select ${parameter.key}`}
          disabled={
            disabled ||
            parameter.options === undefined ||
            parameter.options.length === 0 ||
            loadingChoices.some((loading) => loading.key === parameter.key)
          }
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
    const [items, setItems] = useState([] as Array<string>);
    const searchItems = (event: any) => {
      if (parameter.options) {
        const filteredItems = parameter.options.filter((option) =>
          option.label.toLowerCase().includes(event.query),
        );

        setItems(filteredItems?.map((option) => option.value));
      }
    };
    return (
      <div key={parameter.key} className="p-field">
        <AutoComplete
          id={parameter.key}
          value={parameter.value}
          suggestions={items}
          completeMethod={searchItems}
          invalid={(!disabled && parameter.optional) || undefined}
          onChange={(e) => handleChange(e.target.id, e.target.value)}
          disabled={
            disabled ||
            loadingChoices.some((loading) => loading.key === parameter.key)
          }
          multiple={parameter.multi}
          dropdown
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

  switch (parameter.type) {
    case "Any":
    case "String": {
      if (parameter.multi) {
        return (
          <div key={parameter.key} className="p-field">
            <div className="container">
              {parameter.value?.map((item: any, index: any) => (
                <div key={`${parameter.key}-${index}`} className="dynamic-item">
                  <InputText
                    id={`${parameter.key}-${index}`}
                    value={item ?? ""}
                    invalid={(!disabled && parameter.optional) || undefined}
                    onChange={(e) =>
                      handleMultiChange(parameter.key, e.target.value, index)
                    }
                    disabled={disabled}
                  />
                  <Button
                    label="Remove"
                    severity="danger"
                    onClick={() => removeMultiItem(parameter.key, index)}
                    disabled={disabled}
                  />
                </div>
              ))}
              <Button
                label="Add"
                onClick={() => addMultiItem(parameter.key, parameter.default)}
                disabled={disabled}
              />
            </div>
          </div>
        );
      }
      return (
        <div key={parameter.key} className="p-field">
          <InputText
            id={parameter.key}
            value={parameter.value}
            invalid={(!disabled && parameter.optional) || undefined}
            onChange={(e) => handleChange(e.target.id, e.target.value)}
            disabled={disabled}
          />
        </div>
      );
    }
    case "Dictionary": {
      if (parameter.multi) {
        return (
          <div key={parameter.key} className="p-field">
            <div className="container">
              {parameter.value?.map((item: any, index: any) => (
                <div key={`${parameter.key}-${index}`} className="dynamic-item">
                  <InputTextarea
                    id={`${parameter.key}-${index}`}
                    value={item ?? ""}
                    invalid={(!disabled && parameter.optional) || undefined}
                    onChange={(e) =>
                      handleMultiChange(parameter.key, e.target.value, index)
                    }
                    disabled={disabled}
                  />
                  <Button
                    label="Remove"
                    severity="danger"
                    onClick={() => removeMultiItem(parameter.key, index)}
                    disabled={disabled}
                  />
                </div>
              ))}
              <Button
                label="Add"
                onClick={() => addMultiItem(parameter.key, parameter.default)}
                disabled={disabled}
              />
            </div>
          </div>
        );
      }
      return (
        <div key={parameter.key} className="p-field">
          <InputTextarea
            id={parameter.key}
            value={parameter.value}
            invalid={(!disabled && parameter.optional) || undefined}
            onChange={(e) => handleChange(e.target.id, e.target.value)}
            disabled={disabled}
            className={classNames({ "p-invalid": parameter.isInvalid })}
          />
        </div>
      );
    }
    case "Integer": {
      if (parameter.multi) {
        return (
          <div key={parameter.key} className="p-field">
            <div className="container">
              {parameter.value?.map((item: any, index: any) => (
                <div key={`${parameter.key}-${index}`} className="dynamic-item">
                  <InputNumber
                    id={`${parameter.key}-${index}`}
                    value={item ?? parameter.default}
                    invalid={(!disabled && parameter.optional) || undefined}
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
                    onChange={(e) =>
                      handleMultiChange(parameter.key, e.value, index)
                    }
                    disabled={disabled}
                  />
                  <Button
                    label="Remove"
                    severity="danger"
                    onClick={() => removeMultiItem(parameter.key, index)}
                    disabled={disabled}
                  />
                </div>
              ))}
              <Button
                label="Add"
                onClick={() => addMultiItem(parameter.key, parameter.default)}
                disabled={disabled}
              />
            </div>
          </div>
        );
      }
      return (
        <div key={parameter.key} className="p-field">
          <InputNumber
            id={parameter.key}
            value={parameter.value}
            invalid={(!disabled && parameter.optional) || undefined}
            max={
              parameter.maximum !== undefined ? parameter.maximum : undefined
            }
            min={
              parameter.minimum !== undefined ? parameter.minimum : undefined
            }
            onValueChange={(e) => handleChange(e.target.id, e.target.value)}
            disabled={disabled}
          />
        </div>
      );
    }
    case "Float": {
      if (parameter.multi) {
        return (
          <div key={parameter.key} className="p-field">
            <div className="container">
              {parameter.value?.map((item: any, index: any) => (
                <div key={`${parameter.key}-${index}`} className="dynamic-item">
                  <InputNumber
                    id={`${parameter.key}-${index}`}
                    value={item ?? parameter.default}
                    invalid={(!disabled && parameter.optional) || undefined}
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
                    minFractionDigits={2}
                    onChange={(e) =>
                      handleMultiChange(parameter.key, e.value, index)
                    }
                    disabled={disabled}
                  />
                  <Button
                    label="Remove"
                    severity="danger"
                    onClick={() => removeMultiItem(parameter.key, index)}
                    disabled={disabled}
                  />
                </div>
              ))}
              <Button
                label="Add"
                onClick={() => addMultiItem(parameter.key, parameter.default)}
                disabled={disabled}
              />
            </div>
          </div>
        );
      }
      return (
        <div key={parameter.key} className="p-field">
          <InputNumber
            id={parameter.key}
            value={parameter.value}
            invalid={(!disabled && parameter.optional) || undefined}
            max={
              parameter.maximum !== undefined ? parameter.maximum : undefined
            }
            min={
              parameter.minimum !== undefined ? parameter.minimum : undefined
            }
            minFractionDigits={2}
            onValueChange={(e) => handleChange(e.target.id, e.target.value)}
            disabled={disabled}
          />
        </div>
      );
    }
    case "Boolean": {
      if (parameter.multi) {
        if (parameter.nullable) {
          return (
            <div key={parameter.key} className="p-field">
              <div className="container">
                {parameter.value?.map((item: any, index: any) => (
                  <div
                    key={`${parameter.key}-${index}`}
                    className="dynamic-item"
                  >
                    <TriStateCheckbox
                      id={`${parameter.key}-${index}`}
                      invalid={(!disabled && parameter.optional) || undefined}
                      value={item}
                      onChange={(e) =>
                        handleMultiChange(parameter.key, e.value, index)
                      }
                      disabled={disabled}
                    />

                    <Button
                      label="Remove"
                      severity="danger"
                      onClick={() => removeMultiItem(parameter.key, index)}
                      disabled={disabled}
                    />
                  </div>
                ))}
                <Button
                  label="Add"
                  onClick={() => addMultiItem(parameter.key, parameter.default)}
                  disabled={disabled}
                />
              </div>
            </div>
          );
        }
        return (
          <div key={parameter.key} className="p-field">
            <div className="container">
              {parameter.value?.map((item: any, index: any) => (
                <div key={`${parameter.key}-${index}`} className="dynamic-item">
                  <Checkbox
                    id={`${parameter.key}-${index}`}
                    invalid={(!disabled && parameter.optional) || undefined}
                    checked={item}
                    onChange={(e) =>
                      handleMultiChange(parameter.key, e.checked, index)
                    }
                    disabled={disabled}
                  />

                  <Button
                    label="Remove"
                    severity="danger"
                    onClick={() => removeMultiItem(parameter.key, index)}
                    disabled={disabled}
                  />
                </div>
              ))}
              <Button
                label="Add"
                onClick={() => addMultiItem(parameter.key, parameter.default)}
                disabled={disabled}
              />
            </div>
          </div>
        );
      }
      if (parameter.nullable) {
        return (
          <div key={parameter.key} className="p-field-checkbox">
            <TriStateCheckbox
              id={parameter.key}
              invalid={(!disabled && parameter.optional) || undefined}
              value={parameter.value}
              onChange={(e) => handleChange(e.target.id, e.value)}
              disabled={disabled}
            />
          </div>
        );
      }
      return (
        <div key={parameter.key} className="p-field-checkbox">
          <Checkbox
            id={parameter.key}
            invalid={(!disabled && parameter.optional) || undefined}
            checked={parameter.value}
            onChange={(e) => handleChange(e.target.id, e.checked)}
            disabled={disabled}
          />
        </div>
      );
    }
    case "Date": {
      if (parameter.multi) {
        return (
          <div key={parameter.key} className="p-field">
            <div className="container">
              {parameter.value?.map((item: any, index: any) => (
                <div key={`${parameter.key}-${index}`} className="dynamic-item">
                  <Calendar
                    id={`${parameter.key}-${index}`}
                    value={item}
                    invalid={(!disabled && parameter.optional) || undefined}
                    hourFormat="24"
                    onChange={(e) =>
                      handleMultiChange(parameter.key, e.value, index)
                    }
                    disabled={disabled}
                  />
                  <Button
                    label="Remove"
                    severity="danger"
                    onClick={() => removeMultiItem(parameter.key, index)}
                    disabled={disabled}
                  />
                </div>
              ))}
              <Button
                label="Add"
                onClick={() => addMultiItem(parameter.key, parameter.default)}
                disabled={disabled}
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
            invalid={(!disabled && parameter.optional) || undefined}
            hourFormat="24"
            onChange={(e: any) => handleChange(e.target.id, e.value)}
            disabled={disabled}
          />
        </div>
      );
    }
    case "DateTime": {
      if (parameter.multi) {
        return (
          <div key={parameter.key} className="p-field">
            <div className="container">
              {parameter.value?.map((item: any, index: any) => (
                <div key={`${parameter.key}-${index}`} className="dynamic-item">
                  <Calendar
                    id={`${parameter.key}-${index}`}
                    value={item ?? parameter.default}
                    invalid={(!disabled && parameter.optional) || undefined}
                    showTime
                    hourFormat="24"
                    onChange={(e) =>
                      handleMultiChange(parameter.key, e.value, index)
                    }
                    disabled={disabled}
                  />
                  <Button
                    label="Remove"
                    severity="danger"
                    onClick={() => removeMultiItem(parameter.key, index)}
                    disabled={disabled}
                  />
                </div>
              ))}
              <Button
                label="Add"
                onClick={() => addMultiItem(parameter.key, parameter.default)}
                disabled={disabled}
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
            invalid={(!disabled && parameter.optional) || undefined}
            onChange={(e: any) => handleChange(e.target.id, e.value)}
            disabled={disabled}
          />
        </div>
      );
    }
    case "Bytes": {
      const customBytesUploader = (event: any) => {
        const file = event.files[0];
        handleChange(parameter.key, file as FileUploadFile);
      };
      const bytesUploadRef = useRef<FileUpload>(null);

      useEffect(() => {
        if (bytesUploadRef && bytesUploadRef.current) {
          bytesUploadRef.current.clear();
        }
      }, [resetForm]);

      return (
        <div key={parameter.key} className="p-field">
          <FileUpload
            ref={bytesUploadRef}
            id={parameter.key}
            mode="basic"
            customUpload
            onSelect={customBytesUploader}
            disabled={disabled}
          />
        </div>
      );
    }
    case "Base64": {
      const [uploadPercentage, setUploadPercentage] = useState(0);
      const fileUploadRef = useRef<FileUpload>(null);

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

      useEffect(() => {
        setUploadPercentage(0);
        if (fileUploadRef && fileUploadRef.current) {
          fileUploadRef.current.clear();
        }
      }, [resetForm]);

      return (
        <div key={parameter.key} className="p-field">
          <FileUpload
            ref={fileUploadRef}
            id={parameter.key}
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
