import { Button } from "primereact/button";
import { Calendar } from "primereact/calendar";
import { Checkbox } from "primereact/checkbox";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { Dropdown } from "primereact/dropdown";
import { FileUpload } from "primereact/fileupload";
import { InputNumber } from "primereact/inputnumber";
import { InputText } from "primereact/inputtext";
import { InputTextarea } from "primereact/inputtextarea";
import { MultiSelect } from "primereact/multiselect";
import { TriStateCheckbox } from "primereact/tristatecheckbox";
import { classNames } from "primereact/utils";
import { useEffect, useState } from "react";

import { Command, Parameter } from "../models/brewtils-types"; // Assuming this is the correct path
import { Request } from "../models/brewtils-types";

interface CommandFormProps {
  command: Command | null;
  disabled?: boolean;
  request?: Request | null | undefined;
  setRequest: (request: Request) => void;
}

function CommandForm({
  command,
  disabled,
  request,
  setRequest,
}: CommandFormProps) {
  interface InputParam extends Parameter {
    value?: any;
    isInvalid: boolean;
  }

  // const command = commandFormProps.command;
  disabled = disabled === undefined ? true : disabled;
  // const request = commandFormProps.request;

  const prepareDefaultValues = Array<InputParam>();

  if (command !== null) {
    for (const param of command.parameters || []) {
      const newParam = { ...param } as InputParam;
      if (
        request &&
        request.parameters &&
        param.key &&
        param.key in request.parameters
      ) {
        newParam.value = request.parameters[param.key];
      } else {
        newParam.value = param.default;
      }

      newParam.isInvalid =
        newParam.value !== undefined ||
        param.optional === undefined ||
        param.optional;

      if (
        (newParam.value === undefined || newParam.value === null) &&
        param.multi
      ) {
        newParam.value = [null];
      } else if (param.multi && !Array.isArray(newParam.value)) {
        newParam.value = [newParam.value];
      }

      if (param.type === "Dictionary") {
        if (param.multi) {
          newParam.value = (newParam.value as Array<any>).map((value) => {
            return JSON.stringify(value);
          });
        } else {
          newParam.value = JSON.stringify(newParam.value);
        }
      }

      if (param.type === "DateTime") {
        if (param.multi) {
          newParam.value = (newParam.value as Array<any>).map((value) => {
            return new Date(value);
          });
        } else {
          newParam.value = new Date(newParam.value);
        }
      }

      if (param.type === "Date") {
        if (param.multi) {
          newParam.value = (newParam.value as Array<any>).map((value) => {
            return new Date(value);
          });
        } else {
          newParam.value = new Date(newParam.value);
        }
      }

      prepareDefaultValues.push(newParam);
    }
  }
  const [parametersFields, setParameterFields] = useState(prepareDefaultValues);

  useEffect(() => {
    let updated = false;
    parametersFields.forEach((inputParameter) => {
      if (inputParameter.key === null || inputParameter.key === undefined) {
        return;
      }
      if (
        request &&
        request.parameters &&
        inputParameter.key in request.parameters
      ) {
        if (
          inputParameter.value === null ||
          inputParameter.value === undefined
        ) {
          delete request.parameters[inputParameter.key];
          updated = true;
          return;
        }
      }
      if (request && !request.parameters) {
        request.parameters = {};
        updated = true;
      }
      if (request && request.parameters) {
        if (
          inputParameter.key in request.parameters &&
          request.parameters[inputParameter.key] === inputParameter.value
        ) {
          return;
        }

        request.parameters[inputParameter.key] = inputParameter.value;
        updated = true;
      }
    });
    if (updated) {
      setRequest({ ...request });
    }
  }, [parametersFields]);

  const handleChange = (name: any, value: any) => {
    setParameterFields((prevParams) =>
      prevParams.map((param) =>
        param.key === name ? { ...param, value: value } : param,
      ),
    );
  };

  const handleMultiChange = (key: any, index: number, value: any) => {
    parametersFields.forEach((param: InputParam) => {
      if (param.key === key) {
        param.value[index] = value;
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

  const renderInputLabel = (parameter: InputParam) => {
    return <label htmlFor={parameter.key}>{parameter.key}</label>;
  };

  const renderInputField = (parameter: InputParam) => {
    if (!parameter.key) return null;

    if (parameter.multi && !Array.isArray(parameter.default)) {
      parameter.default = [parameter.default];
    }

    if (parameter.multi && !Array.isArray(parameter.value)) {
      parameter.value = [parameter.value];
    }

    if (
      parameter.choices &&
      parameter.choices.type === "static" &&
      parameter.choices.strict &&
      Array.isArray(parameter.choices.value)
    ) {
      const options = parameter.choices.value.map((choice) => ({
        label: choice,
        value: choice,
      }));
      if (parameter.multi) {
        return (
          <div key={parameter.key} className="p-field">
            <MultiSelect
              id={parameter.key}
              value={parameter.value}
              options={options || []}
              invalid={(!disabled && parameter.optional) || undefined}
              onChange={(e) => handleChange(e.target.id, e.value)}
              placeholder={`Select ${parameter.key}`}
              disabled={disabled}
            />
          </div>
        );
      }
      return (
        <div key={parameter.key} className="p-field">
          <Dropdown
            id={parameter.key}
            value={parameter.value}
            options={options || []}
            invalid={(!disabled && parameter.optional) || undefined}
            onChange={(e) => handleChange(e.target.id, e.value)}
            placeholder={`Select ${parameter.key}`}
            disabled={disabled}
          />
        </div>
      );
    }

    switch (parameter.type) {
      case "String":
        if (parameter.multi) {
          return (
            <div key={parameter.key} className="p-field">
              <div className="container">
                {parameter.value?.map((item: any, index: any) => (
                  <div
                    key={`${parameter.key}-${index}`}
                    className="dynamic-item"
                  >
                    <InputText
                      id={`${parameter.key}-${index}`}
                      value={item ?? ""}
                      invalid={(!disabled && parameter.optional) || undefined}
                      onChange={(e) =>
                        handleMultiChange(parameter.key, index, e.target.value)
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
      case "Dictionary":
        if (parameter.multi) {
          return (
            <div key={parameter.key} className="p-field">
              <div className="container">
                {parameter.value?.map((item: any, index: any) => (
                  <div
                    key={`${parameter.key}-${index}`}
                    className="dynamic-item"
                  >
                    <InputTextarea
                      id={`${parameter.key}-${index}`}
                      value={item ?? ""}
                      invalid={(!disabled && parameter.optional) || undefined}
                      onChange={(e) =>
                        handleMultiChange(parameter.key, index, e.target.value)
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
      case "Integer":
        if (parameter.multi) {
          return (
            <div key={parameter.key} className="p-field">
              <div className="container">
                {parameter.value?.map((item: any, index: any) => (
                  <div
                    key={`${parameter.key}-${index}`}
                    className="dynamic-item"
                  >
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
                        handleMultiChange(parameter.key, index, e.value)
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
      case "Float":
        if (parameter.multi) {
          return (
            <div key={parameter.key} className="p-field">
              <div className="container">
                {parameter.value?.map((item: any, index: any) => (
                  <div
                    key={`${parameter.key}-${index}`}
                    className="dynamic-item"
                  >
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
                        handleMultiChange(parameter.key, index, e.value)
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
      case "Boolean":
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
                          handleMultiChange(parameter.key, index, e.value)
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
                    onClick={() =>
                      addMultiItem(parameter.key, parameter.default)
                    }
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
                  <div
                    key={`${parameter.key}-${index}`}
                    className="dynamic-item"
                  >
                    <Checkbox
                      id={`${parameter.key}-${index}`}
                      invalid={(!disabled && parameter.optional) || undefined}
                      checked={item}
                      onChange={(e) =>
                        handleMultiChange(parameter.key, index, e.checked)
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
      case "Date":
        if (parameter.multi) {
          return (
            <div key={parameter.key} className="p-field">
              <div className="container">
                {parameter.value?.map((item: any, index: any) => (
                  <div
                    key={`${parameter.key}-${index}`}
                    className="dynamic-item"
                  >
                    <Calendar
                      id={`${parameter.key}-${index}`}
                      value={item}
                      invalid={(!disabled && parameter.optional) || undefined}
                      hourFormat="24"
                      onChange={(e) =>
                        handleMultiChange(parameter.key, index, e.value)
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
      case "DateTime":
        if (parameter.multi) {
          return (
            <div key={parameter.key} className="p-field">
              <div className="container">
                {parameter.value?.map((item: any, index: any) => (
                  <div
                    key={`${parameter.key}-${index}`}
                    className="dynamic-item"
                  >
                    <Calendar
                      id={`${parameter.key}-${index}`}
                      value={item ?? parameter.default}
                      invalid={(!disabled && parameter.optional) || undefined}
                      showTime
                      hourFormat="24"
                      onChange={(e) =>
                        handleMultiChange(parameter.key, index, e.value)
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
      case "Bytes":
        const customBytesUploader = async (event: any) => {
          // convert file to bytes encoded
          const file = event.files[0];
          const reader = new FileReader();
          const blob = await fetch(file.objectURL).then((r) => r.blob()); //blob:url

          reader.readAsDataURL(blob);

          reader.onloadend = function () {
            const base64data = reader.result;
            // Run Upload
          };
        };
        return (
          <div key={parameter.key} className="p-field">
            <FileUpload
              id={parameter.key}
              mode="basic"
              customUpload
              uploadHandler={customBytesUploader}
              disabled={disabled}
            />
          </div>
        );
      case "Base64":
        const customBase64Uploader = async (event: any) => {
          // convert file to base64 encoded
          const file = event.files[0];
          const reader = new FileReader();
          const blob = await fetch(file.objectURL).then((r) => r.blob()); //blob:url

          reader.readAsDataURL(blob);

          reader.onloadend = function () {
            const base64data = reader.result;
            // Run Upload
          };
        };
        return (
          <div key={parameter.key} className="p-field">
            <FileUpload
              id={parameter.key}
              mode="basic"
              customUpload
              uploadHandler={customBase64Uploader}
              disabled={disabled}
            />
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <DataTable
      value={parametersFields}
      showHeaders={false}
      tableStyle={{ minWidth: "60rem" }}
    >
      <Column header="Field" body={renderInputLabel}></Column>
      <Column header="Value" body={renderInputField}></Column>
      <Column header="Description" field="description"></Column>
    </DataTable>
  );
}

export default CommandForm;
