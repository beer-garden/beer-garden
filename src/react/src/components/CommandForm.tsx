import { AutoComplete } from "primereact/autocomplete";
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
import { Skeleton } from "primereact/skeleton";
import { TriStateCheckbox } from "primereact/tristatecheckbox";
import { classNames } from "primereact/utils";
import { useEffect, useState } from "react";

import { ChoicesValue, Command, Parameter } from "../models/brewtils-types"; // Assuming this is the correct path
import { Request } from "../models/brewtils-types";
import { PostRequest } from "../services/request_service";

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
    options: Array<{ label: string; value: any }> | undefined;
  }

  disabled = disabled === undefined ? true : disabled;

  const generateChoices = (
    parameter: InputParam,
    lookupParameters: Array<InputParam>,
  ): Promise<Array<{ label: string; value: any }> | undefined> => {
    return new Promise((resolve) => {
      if (
        parameter.choices &&
        parameter.choices.type === "static" &&
        Array.isArray(parameter.choices.value)
      ) {
        const options = parameter.choices.value.map((choice) => ({
          label: choice,
          value: choice,
        }));
        resolve(options);
      }

      const parameterArgs = {} as any;

      parameter?.choices?.details?.args?.forEach((arg) => {
        if (arg[1] === parameter.key) {
          // Parameter cannot depend on itself, don't load request response
          return;
        }
        const paramField =
          lookupParameters.find((p) => p.key === arg[1])?.value || null;
        if (paramField !== null && paramField !== undefined) {
          parameterArgs[arg[0]] = paramField;
        }
      });

      if (
        parameter?.choices?.details?.args &&
        Object.keys(parameterArgs).length !==
          parameter.choices.details.args.length
      ) {
        resolve(undefined);
        return;
      }

      if (
        parameter.choices &&
        parameter.choices.type === "url" &&
        parameter.choices.details &&
        parameter.choices.details.address
      ) {
        if (parameter.key) {
          setLoadingChoices([...loadingChoices, parameter.key]);
        }
        const url = new URL(parameter.choices.details.address);
        url.search = new URLSearchParams(parameterArgs).toString();

        fetch(url)
          .then((response) => {
            if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
          })
          .then((data) => {
            const choices = data.map((item: any) => ({
              label: item,
              value: item,
            }));
            resolve(choices);
          })
          .catch((error) => {
            console.error("Error fetching choices:", error);
            resolve(undefined);
          });
      } else if (
        parameter.choices &&
        parameter.choices.type === "command" &&
        parameter.choices.details &&
        parameter.choices.details.name
      ) {
        if (parameter.key) {
          setLoadingChoices([...loadingChoices, parameter.key]);
        }
        const paramRequest = {
          command: parameter.choices.details.name,
          parameters: parameterArgs,
          namespace: request?.namespace,
          system: request?.system,
          system_version: request?.system_version,
          instance_name: request?.instance_name,
        } as Request;

        if (
          parameter.choices.value !== null &&
          parameter.choices.value !== undefined &&
          typeof parameter.choices.value === "object"
        ) {
          if ((parameter.choices.value as ChoicesValue).namespace) {
            paramRequest.namespace = (
              parameter.choices.value as ChoicesValue
            ).namespace;
          }
          if ((parameter.choices.value as ChoicesValue).instance_name) {
            paramRequest.instance_name = (
              parameter.choices.value as ChoicesValue
            ).instance_name;
          }
          if ((parameter.choices.value as ChoicesValue).system_version) {
            paramRequest.system_version = (
              parameter.choices.value as ChoicesValue
            ).system_version;
          }
          if ((parameter.choices.value as ChoicesValue).system) {
            paramRequest.system = (
              parameter.choices.value as ChoicesValue
            ).system;
          }
        }

        PostRequest(paramRequest, {}, true)
          .then((response) => {
            if (response.output) {
              const parsedOutput = JSON.parse(response.output);
              const choices = parsedOutput.map((item: any) => ({
                label: item,
                value: item,
              }));
              resolve(choices);
            } else {
              resolve([]);
            }
          })
          .catch((error) => {
            console.error("Error fetching choices:", error);
            resolve(undefined);
          });
      }
    });
  };

  const buildDefaults = async (
    mapRequest = true,
  ): Promise<Array<InputParam>> => {
    const prepareDefaultValues = Array<InputParam>();

    if (command !== null) {
      for (const param of command.parameters || []) {
        const newParam = { ...param } as InputParam;
        if (
          mapRequest &&
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

        if (param.choices && param.choices.details) {
          newParam.options = [];
          if (
            param.choices.details.args === null ||
            param.choices.details.args === undefined ||
            (Array.isArray(param.choices.details.args) &&
              param.choices.details.args.length === 0)
          ) {
            newParam.options = await generateChoices(
              newParam,
              prepareDefaultValues,
            );
          }
        }

        prepareDefaultValues.push(newParam);
      }
    }
    return prepareDefaultValues;
  };
  const [parametersFields, setParameterFields] = useState(
    [] as Array<InputParam>,
  );
  const [initialized, setInitialized] = useState(false);
  const [loadingChoices, setLoadingChoices] = useState([] as Array<string>);

  const resetRequest = () => {
    buildDefaults(false)
      .then((preparedParams) => {
        setParameterFields(preparedParams);
        setLoadingChoices([]);
      })
      .catch((error) => {
        console.error("Error building default values:", error);
        setLoadingChoices([]);
      });
  };

  useEffect(() => {
    if (!initialized) {
      buildDefaults()
        .then((preparedParams) => {
          setParameterFields(preparedParams);
          setInitialized(true);
          setLoadingChoices([]);
        })
        .catch((error) => {
          console.error("Error building default values:", error);
        });
      return;
    }
    let updated = false;
    const changedFields = [] as Array<string>;
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
          changedFields.push(inputParameter.key);
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
        changedFields.push(inputParameter.key);
      }
    });
    if (updated) {
      setRequest({ ...request });
      // Update dynamic options
      // let updatedOptions = false;
      parametersFields.forEach((parameter: InputParam) => {
        if (parameter?.key && parameter.choices) {
          if (parameter.choices?.details?.args) {
            const updatedKeys = parameter.choices.details.args.map(
              (arg) => arg[1],
            );
            const shouldUpdate = changedFields.some((field) =>
              updatedKeys.includes(field),
            );
            if (
              !updatedKeys.includes(parameter.key) &&
              (shouldUpdate || parameter.options === undefined)
            ) {
              generateChoices(parameter, parametersFields).then(
                (options: any) => {
                  const updatedParameterFields = parametersFields.map((p) => {
                    if (p.key === parameter.key) {
                      p.options = options;
                    }
                    return p;
                  });
                  setParameterFields([...updatedParameterFields]);
                  setLoadingChoices(
                    loadingChoices.filter((key) => key !== parameter.key),
                  );
                },
              );
            }
          }
        }
      });
    }
  }, [parametersFields]);

  const handleChange = (name: any, value: any) => {
    setParameterFields((prevParams) =>
      prevParams.map((param) =>
        param.key === name ? { ...param, value: value } : param,
      ),
    );
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
                parameter.options.length === 0
              }
            />
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
              parameter.options.length === 0
            }
          />
        </div>
      );
    } else if (
      parameter.choices &&
      parameter.choices?.display === "typeahead"
    ) {
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
            disabled={disabled}
            multiple={parameter.multi}
            dropdown
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
    <div>
      {loadingChoices.length === 0 && (
        <DataTable
          value={parametersFields}
          showHeaders={false}
          tableStyle={{ minWidth: "60rem" }}
        >
          <Column header="Field" body={renderInputLabel}></Column>
          <Column header="Value" body={renderInputField}></Column>
          <Column header="Description" field="description"></Column>
        </DataTable>
      )}
      {loadingChoices.length > 0 && (
        <Skeleton width="100%" height="150px"></Skeleton>
      )}
      <Button
        label="Reset Form"
        severity="warning"
        icon="pi pi-arrow-right"
        iconPos="right"
        onClick={resetRequest}
      />
    </div>
  );
}

export default CommandForm;
