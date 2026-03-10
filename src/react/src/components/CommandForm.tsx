import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "primereact/button";
import { Calendar } from "primereact/calendar";
import { Checkbox } from "primereact/checkbox";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { Dialog } from "primereact/dialog";
import { Dropdown } from "primereact/dropdown";
import { FileUpload, FileUploadFile } from "primereact/fileupload";
import { InputNumber } from "primereact/inputnumber";
import { InputText } from "primereact/inputtext";
import { InputTextarea } from "primereact/inputtextarea";
import { MultiSelect } from "primereact/multiselect";
import { ProgressBar } from "primereact/progressbar";
import { TriStateCheckbox } from "primereact/tristatecheckbox";
import { classNames } from "primereact/utils";
import { useEffect, useRef, useState } from "react";

import { Command, Parameter } from "../models/brewtils-types"; // Assuming this is the correct path
import { Request } from "../models/brewtils-types";
import { uploadFile } from "../services/file_service";

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

  const [visibleCodeExample, setVisibleCodeExample] = useState<boolean>(false);

  disabled = disabled === undefined ? true : disabled;

  const buildDefaults = (mapRequest = true): Array<InputParam> => {
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

        prepareDefaultValues.push(newParam);
      }
    }
    return prepareDefaultValues;
  };
  const [parametersFields, setParameterFields] = useState(buildDefaults());

  const [resetForm, setResetForm] = useState(false);

  const resetRequest = () => {
    // Doesn't matter the value, just invert it to trigger the useEffect
    setResetForm(!resetForm);
    setParameterFields(buildDefaults(false));
  };

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
      default:
        return null;
    }
  };

  const CodeBlock = (codeType: string) => {
    const getHostName = () => {
      return window.location.hostname;
    };

    const getPort = () => {
      return window.location.port;
    };

    const getPrefix = () => {
      const path = window.location.pathname;

      for (const knownPaths of ["/create", "/recreate"]) {
        const index = path.indexOf(knownPaths);
        if (index > 0) {
          return path.slice(1, index) + "/";
        }
      }

      return "";
    };

    const getSslEnabled = () => {
      return window.location.protocol === "https:" ? "True" : "False";
    };

    const wgetCode = () => {
      return `
  wget --method=POST -O- \\
    --body-data='${JSON.stringify(request)}' \\
    --header=Content-Type:application/json \\
    ${getHostName()}:${getPort()}${getPrefix()}/api/v1/requests?blocking=true
  `;
    };

    const curlCode = () => {
      return `
  curl -X POST ${getHostName()}:${getPort()}${getPrefix()}/api/v1/requests?blocking=true \\
    -H "Content-Type: application/json" \\
    -d '${JSON.stringify(request)}'
  `;
    };

    const pythonCode = () => {
      const generateParams = () => {
        if (request?.parameters) {
          const printParams = [] as Array<string>;

          for (const [key, value] of Object.entries(
            request?.parameters || {},
          )) {
            if (value && value !== undefined && value !== null) {
              if (typeof value === "string") {
                printParams.push(key + '="' + value + '"');
              } else if (typeof value === "boolean") {
                printParams.push(key + "=" + (value ? "True" : "False"));
              } else {
                printParams.push(key + "=" + value);
              }
            }
          }

          return printParams.join(", ");
        }
        return "";
      };

      return `
  from brewtils import SystemClient
  
  request = SystemClient(
    system_name = '${request?.system}',
    system_namespace = '${request?.namespace}',
    version_constraint = '${request?.system_version}',
    default_instance = '${request?.instance_name}',
    bg_host = '${getHostName()}',
    bg_url_prefix = '${getPrefix()}',
    bg_port = ${getPort()},
    blocking = True,
    ssl_enabled = ${getSslEnabled()},
    ca_cert = None,
    ca_verify = None,
    client_cert = None).${request?.command ? request?.command : "command"}(${generateParams()})
  
  print(request)
  `;
    };

    const code = () => {
      if (codeType === "Python") {
        return pythonCode();
      }
      if (codeType === "cURL") {
        return curlCode();
      }
      if (codeType === "Wget") {
        return wgetCode();
      }

      if (codeType === "JSON") {
        return JSON.stringify(request, null, 2);
      }

      return "";
    };
    const copyToClipboard = () => {
      navigator.clipboard.writeText(code()).catch((error) => {
        console.error("Error copying to clipboard:", error);
      });
    };

    return (
      <div style={{ position: "relative" }}>
        <h3>{codeType}</h3>
        <Button
          className="p-button-rounded p-button-text"
          onClick={copyToClipboard}
          style={{ position: "absolute", top: "0.5rem", right: "0.5rem" }}
        >
          <FontAwesomeIcon icon="copy" />
        </Button>
        <pre>
          <code
            style={{
              whiteSpace: "pre-wrap",
              overflowWrap: "break-word",
              overflowX: "auto",
            }}
          >
            {code()}
          </code>
        </pre>
      </div>
    );
  };

  return (
    <div>
      <DataTable
        value={parametersFields}
        showHeaders={false}
        tableStyle={{ minWidth: "60rem" }}
      >
        <Column header="Field" body={renderInputLabel}></Column>
        <Column header="Value" body={renderInputField}></Column>
        <Column header="Description" field="description"></Column>
      </DataTable>
      <Dialog
        header={"Code Examples"}
        visible={visibleCodeExample}
        onHide={() => {
          if (!visibleCodeExample) return;
          setVisibleCodeExample(false);
        }}
        style={{ width: "50vw" }}
      >
        <div>
          Bytes and Base64 parameters are not supported in code examples.
        </div>
        {CodeBlock("Python")}

        {CodeBlock("cURL")}

        {CodeBlock("Wget")}

        {CodeBlock("JSON")}
      </Dialog>
      <Button
        label="Reset Form"
        severity="warning"
        icon="pi pi-arrow-right"
        onClick={resetRequest}
      />
      <Button
        label="Code Examples"
        severity="info"
        icon="pi pi-arrow-right"
        onClick={() => setVisibleCodeExample(true)}
      />
    </div>
  );
}

export default CommandForm;
