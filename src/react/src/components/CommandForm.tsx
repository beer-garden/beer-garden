import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "primereact/button";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { Dialog } from "primereact/dialog";
import { useEffect, useRef, useState } from "react";

import { ChoicesValue, Command, Request } from "../models/brewtils-types";
import { InputParam } from "../models/models";
import { PostRequest } from "../services/request_service";
import CommandFormField from "./CommandFormField";

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
  disabled = disabled === undefined ? true : disabled;
  const [parametersFields, setParameterFields] = useState(
    [] as Array<InputParam>,
  );
  const altParametersFields = useRef<Array<InputParam>>([]);

  const [initialized, setInitialized] = useState(false);

  const [loadingChoices, setLoadingChoices] = useState(
    [] as Array<{ key: string; timestamp: number }>,
  );
  const altLoadingChoices = useRef<Array<{ key: string; timestamp: number }>>(
    [],
  );
  const [visibleCodeExample, setVisibleCodeExample] = useState<boolean>(false);
  const [resetForm, setResetForm] = useState(false);

  const generateChoices = (
    parameter: InputParam,
    lookupParameters: Array<InputParam>,
  ) => {
    const timestamp = Date.now();

    const mapChoices = (
      values:
        | Array<{ text: string; value: string } | string>
        | { [key: string]: Array<{ text: string; value: string } | string> },
    ): Promise<Array<{ label: string; value: string }>> => {
      return new Promise((resolve, reject) => {
        if (values === null || values === undefined) {
          resolve([]);
        }

        if (Array.isArray(values)) {
          if (values.length === 0) {
            resolve([]);
          }
          resolve(values.map((choice) => mapChoice(choice)));
        }

        if (parameter?.choices?.details?.key_reference) {
          for (const populatedField of lookupParameters) {
            if (
              populatedField.key === parameter.choices?.details?.key_reference
            ) {
              if (
                // Not Defined Yet
                populatedField.value === null ||
                populatedField.value === undefined ||
                // Selected Null but it wasn't defined as an input
                (typeof populatedField.value !== "string" &&
                  "value" in populatedField.value &&
                  (populatedField.value.value === null ||
                    populatedField.value.value === undefined))
              ) {
                if ("null" in values) {
                  resolve(values["null"].map((choice) => mapChoice(choice)));
                }
                reject(
                  Error(`Dependant Key ${populatedField.key} is not populated`),
                );
              }
              if (
                typeof populatedField.value === "string" &&
                populatedField.value in values
              ) {
                resolve(
                  (
                    values as {
                      [key: string]: Array<
                        { text: string; value: string } | string
                      >;
                    }
                  )[populatedField.value].map((choice) => mapChoice(choice)),
                );
              }
              reject(
                Error(
                  `Dependant Key ${populatedField.key} does not have mapping values`,
                ),
              );
            }
          }
          reject(
            Error(
              `Dependant Key ${parameter.choices?.details?.key_reference} is not found in form`,
            ),
          );
        }

        resolve([]);
      });
    };

    const mapChoice = (
      choice: string | { text: string; value: string },
    ): { label: string; value: string } => {
      if (
        choice !== null &&
        choice !== undefined &&
        typeof choice !== "string" &&
        "text" in choice &&
        "value" in choice
      ) {
        return {
          label: choice.text,
          value: choice.value,
        };
      }
      return {
        label: choice,
        value: choice,
      };
    };

    const resolveOptions = (
      options: Array<{ label: string; value: any }> | undefined,
      errorMsd?: string,
    ) => {
      if (
        parameter.key &&
        altLoadingChoices.current.some(
          (loading) =>
            loading.key === parameter.key && loading.timestamp === timestamp,
        )
      ) {
        const matchingLoading = altLoadingChoices.current.filter(
          (loading) => loading.key === parameter.key,
        );

        if (
          matchingLoading.reduce(
            (max, item) => (item.timestamp > max.timestamp ? item : max),
            matchingLoading[0],
          ).timestamp === timestamp
        ) {
          const updatedParameterFields = altParametersFields.current.map(
            (p) => {
              if (p.key === parameter.key) {
                p.options = options;
                p.error = errorMsd !== undefined;
                p.errorMsg = errorMsd;
              }
              return p;
            },
          );

          altParametersFields.current = updatedParameterFields;
          setParameterFields([...altParametersFields.current]);
          removeLoadingChoice(parameter.key);
        } else {
          removeLoadingChoice(parameter.key, timestamp);
        }
      }
    };

    if (parameter.key) {
      addLoadingChoice(parameter.key, timestamp);
    }

    if (
      parameter.choices &&
      parameter.choices.type === "static"
      // Array.isArray(parameter.choices.value)
    ) {
      mapChoices(
        parameter.choices.value as
          | Array<{ text: string; value: string } | string>
          | { [key: string]: Array<{ text: string; value: string } | string> },
      )
        .then((options) => resolveOptions(options))
        .catch((error) => {
          console.error("Error fetching choices:", error);
          resolveOptions([], `Error fetching choices: ${error}`);
        });
    }

    const parameterArgs = {} as any;

    parameter?.choices?.details?.args?.forEach((arg) => {
      if (arg[1] === parameter.key) {
        // Parameter cannot depend on itself, don't load request response
        removeLoadingChoice(parameter.key, timestamp);
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
      resolveOptions([], "Unable to find all Dynamic Arg Values");
      return;
    }

    if (
      parameter.choices &&
      parameter.choices.type === "url" &&
      parameter.choices.details &&
      parameter.choices.details.address
    ) {
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
          mapChoices(data)
            .then((choices) => resolveOptions(choices))
            .catch((error) => {
              console.error("Error fetching choices:", error);
              resolveOptions([], `Error fetching choices: ${error}`);
            });
        })
        .catch((error) => {
          console.error("Error fetching choices:", error);
          resolveOptions([], `Error fetching choices: ${error}`);
        });
    } else if (
      parameter.choices &&
      parameter.choices.type === "command" &&
      parameter.choices.details &&
      parameter.choices.details.name
    ) {
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
            mapChoices(parsedOutput)
              .then((choices) => resolveOptions(choices))
              .catch((error) => {
                console.error("Error fetching choices:", error);
                resolveOptions([], `Error fetching choices: ${error}`);
              });
          } else {
            resolveOptions([]);
          }
        })
        .catch((error) => {
          console.error("Error fetching choices:", error);
          resolveOptions([], `Error fetching choices: ${error}`);
        });
    }
  };

  const buildDefaults = (mapRequest = true) => {
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
    altParametersFields.current = prepareDefaultValues;
    setParameterFields([...altParametersFields.current]);
    setInitialized(true);
    altLoadingChoices.current = [];
    setLoadingChoices([]);

    for (const param of prepareDefaultValues || []) {
      generateChoices(param, prepareDefaultValues);
    }
  };

  const addLoadingChoice = (addKey: string, timestamp: number) => {
    const newLoadingChoices = [
      ...altLoadingChoices.current,
      { key: addKey, timestamp: timestamp },
    ];

    altLoadingChoices.current = newLoadingChoices;
    setLoadingChoices([...altLoadingChoices.current]);
  };

  const removeLoadingChoice = (removeKey: string, timestamp?: number) => {
    const newLoadingChoices = [] as Array<{ key: string; timestamp: number }>;

    for (const keyObject of altLoadingChoices.current) {
      if (removeKey !== keyObject.key) {
        newLoadingChoices.push(keyObject);
      } else if (timestamp && keyObject.timestamp !== timestamp) {
        newLoadingChoices.push(keyObject);
      }
    }

    altLoadingChoices.current = newLoadingChoices;
    setLoadingChoices([...altLoadingChoices.current]);
  };

  const resetRequest = () => {
    setResetForm(!resetForm);
    buildDefaults(false);
  };

  useEffect(() => {
    if (!initialized) {
      buildDefaults();
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
      if (inputParameter.value === null || inputParameter.value === undefined) {
        return;
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
      parametersFields.forEach((parameter: InputParam) => {
        if (parameter?.key && parameter.choices) {
          const updatedKeys = [] as Array<string>;

          if (parameter.choices?.details?.args) {
            for (const arg of parameter.choices.details.args) {
              updatedKeys.push(arg[1]);
            }
          }

          if (parameter.choices?.details?.key_reference) {
            updatedKeys.push(parameter.choices?.details?.key_reference);
          }
          if (updatedKeys.length > 0) {
            const shouldUpdate = changedFields.some((field) =>
              updatedKeys.includes(field),
            );
            // Update if input value changed
            // Skip load if parameters is undefined but currently being loading
            if (
              !updatedKeys.includes(parameter.key) &&
              (shouldUpdate ||
                (parameter.options === undefined &&
                  !altLoadingChoices.current.some(
                    (loading) => loading.key === parameter.key,
                  )))
            ) {
              generateChoices(parameter, parametersFields);
            }
          }
        }
      });
    }
  }, [parametersFields]);

  const handleChange = (name: any, value: any) => {
    altParametersFields.current = altParametersFields.current.map((param) =>
      param.key === name ? { ...param, value: value } : param,
    );
    setParameterFields([...altParametersFields.current]);
  };

  const renderInputLabel = (parameter: InputParam) => {
    return <label htmlFor={parameter.key}>{parameter.key}</label>;
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

  // Need to find a better way to handle states of dynamic options loading instead of
  // checking if loading choices has items and rendering two tables
  return (
    <div>
      {parametersFields && (
        <div key={loadingChoices.length}>
          <DataTable
            value={parametersFields}
            showHeaders={false}
            tableStyle={{ minWidth: "60rem" }}
          >
            <Column header="Field" body={renderInputLabel}></Column>
            <Column
              header="Value"
              body={(parameter) =>
                CommandFormField({
                  parameter: parameter,
                  disabled: disabled,
                  parametersFields: parametersFields,
                  loadingChoices: loadingChoices,
                  handleChange: handleChange,
                  resetForm: resetForm,
                })
              }
            ></Column>
            <Column header="Description" field="description"></Column>
          </DataTable>
        </div>
      )}
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
