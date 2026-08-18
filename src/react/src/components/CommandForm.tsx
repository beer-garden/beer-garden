import {
  Alert,
  AlertTitle,
  Box,
  Divider,
  FormControl,
  FormLabel,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Tooltip,
} from "@mui/material";
import { ChangeEvent, useEffect, useRef, useState } from "react";

import {
  ChoicesValue,
  Connection,
  Garden,
  Request,
} from "../models/brewtils-types";
import { CommandFormProps, InputParam } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import { PostRequest } from "../services/request_service";
import { GetSystemList } from "../services/system_service";
import { CompareObjects } from "../services/util_service";
import CommandFormField from "./CommandFormField";

function CommandForm({
  command,
  disabled,
  request,
  setRequest,
  resetForm,
  setResetForm,
  setIsFormValid,
}: CommandFormProps) {
  disabled = disabled === undefined ? true : disabled;
  const [parametersFields, setParameterFields] = useState(
    [] as Array<InputParam>,
  );
  const altParametersFields = useRef<Array<InputParam>>([]);
  const showSnackbar = useSnackbar();

  const [initialized, setInitialized] = useState(false);

  const [loadingChoices, setLoadingChoices] = useState(
    [] as Array<{ key: string; timestamp: number }>,
  );
  const altLoadingChoices = useRef<Array<{ key: string; timestamp: number }>>(
    [],
  );

  const [errorMessages, setErrorMessages] = useState<
    Array<{
      summary: string;
      detail: string;
      severity: "error" | "info" | "success" | "warning";
    }>
  >([]);

  const clearMessages = () => setErrorMessages([]);
  const addMessage = (msg: {
    summary: string;
    detail: string;
    severity: "error" | "info" | "success" | "warning";
  }) => {
    setErrorMessages((prev) => [...prev, msg]);
  };

  const generateChoices = (
    parameter: InputParam,
    lookupParameters: Array<InputParam>,
  ) => {
    // Skip choice generation if disabled
    if (disabled) {
      return;
    }

    const timestamp = Date.now();

    const mapChoices = (
      values:
        | Array<{ text: string; value: string } | string>
        | { [key: string]: Array<{ text: string; value: string } | string> },
    ): Promise<Array<{ label: string; value: string | number }>> => {
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
      choice: string | { text: string; value: string } | number,
    ): { label: string; value: string | number } => {
      if (choice !== null && choice !== undefined) {
        if (typeof choice === "number") {
          return { label: choice.toString(), value: choice };
        }

        if (
          typeof choice === "object" &&
          "text" in choice &&
          "value" in choice
        ) {
          return {
            label: choice.text,
            value: choice.value,
          };
        }
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

    if (parameter.choices && parameter.choices.type === "static") {
      mapChoices(
        parameter.choices.value as
          | Array<{ text: string; value: string } | string>
          | { [key: string]: Array<{ text: string; value: string } | string> },
      )
        .then((options) => resolveOptions(options))
        .catch((error) => {
          console.error("Error fetching choices:", error);
          showSnackbar({
            severity: "error",
            summary: "Error",
            detail: `Error fetching choices: ${error}`,
            life: 3000,
          });
          resolveOptions([], `Error fetching choices: ${error}`);
        });
    }

    const parameterArgs = {} as any;

    parameter?.choices?.details?.args?.forEach((arg) => {
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
      const missingArgs = [] as Array<string>;
      parameter?.choices?.details?.args?.forEach((arg) => {
        if (!Object.keys(parameterArgs).includes(arg[0])) {
          missingArgs.push(arg[1]);
        }
      });
      resolveOptions(
        [],
        `Unable to find all Dynamic Arg Values, unpopulated or missing fields: ${missingArgs.toString()}`,
      );
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
              showSnackbar({
                severity: "error",
                summary: "Error",
                detail: `Error fetching choices: ${error}`,
                life: 3000,
              });
              resolveOptions([], `Error fetching choices: ${error}`);
            });
        })
        .catch((error) => {
          console.error("Error fetching choices:", error);
          showSnackbar({
            severity: "error",
            summary: "Error",
            detail: `Error fetching choices: ${error}`,
            life: 3000,
          });
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
                showSnackbar({
                  severity: "error",
                  summary: "Error",
                  detail: `Error fetching choices: ${error}`,
                  life: 3000,
                });
                resolveOptions([], `Error fetching choices: ${error}`);
              });
          } else {
            resolveOptions([]);
          }
        })
        .catch((error) => {
          console.error("Error fetching choices:", error);
          showSnackbar({
            severity: "error",
            summary: "Error",
            detail: `Error fetching choices: ${error}`,
            life: 3000,
          });
          resolveOptions([], `Error fetching choices: ${error}`);
        });
    }
  };

  const buildDefaults = (mapRequest = true) => {
    const prepareDefaultValues = Array<InputParam>();

    if (command && command !== null) {
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
              return value ? new Date(value).getTime() : value;
            });
          } else {
            newParam.value = newParam.value
              ? new Date(newParam.value).getTime()
              : newParam.value;
          }
        }

        if (param.type === "Date") {
          if (param.multi) {
            newParam.value = (newParam.value as Array<any>).map((value) => {
              return value ? new Date(value).getTime() : value;
            });
          } else {
            newParam.value = newParam.value
              ? new Date(newParam.value).getTime()
              : newParam.value;
          }
        }

        if (param.type === "Boolean" && !param.nullable && !param.optional) {
          if (param.multi) {
            newParam.value = (newParam.value as Array<any>).map((value) => {
              return value === undefined || value === null ? false : value;
            });
          } else {
            newParam.value =
              newParam.value === undefined || newParam.value === null
                ? false
                : newParam.value;
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

  const isMissingValue = (value: any) => {
    if (Array.isArray(value)) {
      return (
        value.length === 0 ||
        value.some(
          (entry) => entry === null || entry === undefined || entry === "",
        )
      );
    }
    return value === null || value === undefined || value === "";
  };

  const validateForm = () => {
    let valid = true;
    for (const parameter of altParametersFields.current) {
      if (
        isMissingValue(parameter.value) &&
        (parameter.optional === undefined || !parameter.optional)
      ) {
        valid = false;
        break;
      }
      if (parameter.type === "Dictionary") {
        if (parameter.multi) {
          for (const param of parameter.value) {
            try {
              JSON.parse(param);
            } catch {
              valid = false;
              break;
            }
          }
          if (!valid) {
            break;
          }
        } else {
          try {
            JSON.parse(parameter.value);
          } catch {
            valid = false;
            break;
          }
        }
      }
    }
    setIsFormValid(valid);
  };

  const validateGardenRouting = (garden_name: string) => {
    const rootGarden = sessionStorage.getItem("rootGarden")
      ? JSON.parse(sessionStorage.getItem("rootGarden") || "")
      : undefined;

    if (rootGarden && rootGarden.name !== garden_name) {
      const validateChildren = (
        garden: Garden,
        gardenName: string,
      ): boolean => {
        if (garden.name === gardenName) {
          if (
            garden.publishing_connections.length > 0 &&
            garden.receiving_connections.length > 0
          ) {
            if (
              garden.publishing_connections.some(
                (connection: Connection) => connection.status === "PUBLISHING",
              ) &&
              garden.receiving_connections.some(
                (connection: Connection) => connection.status === "RECEIVING",
              )
            ) {
              return true;
            } else {
              return false;
            }
          }
        }
        if (
          garden.children &&
          garden.children.some((child: Garden) =>
            validateChildren(child, gardenName),
          )
        ) {
          return true;
        }
        return false;
      };

      if (!validateChildren(rootGarden, garden_name)) {
        clearMessages();
        addMessage({
          severity: "error",
          summary: "Garden Check",
          detail: "Target Garden for command is not routable",
        });
      }
    }
  };

  const validateRouting = () => {
    GetSystemList()
      .then((systems) => {
        const targetSystem = systems.find(
          (system) =>
            system.name === request?.system &&
            system.namespace === request?.namespace &&
            system.version === request?.system_version &&
            system.instances &&
            system.instances.some(
              (instance) => instance.name === request?.instance_name,
            ),
        );

        if (targetSystem === undefined) {
          clearMessages();
          addMessage({
            severity: "error",
            summary: "System Check",
            detail:
              "Unable to find target system for command, unable to validate routing",
          });
        } else if (
          targetSystem.instances?.some(
            (instance) => "RUNNING" !== instance.status,
          )
        ) {
          const targetInstance = targetSystem.instances?.find(
            (instance) => instance.name === request?.instance_name,
          );
          clearMessages();
          addMessage({
            severity: "error",
            summary: "System Check",
            detail: `Target System has a status of ${targetInstance?.status}`,
          });
        } else {
          // Validate Garden Routing
          if (request?.target_garden) {
            validateGardenRouting(request.target_garden);
          } else if (targetSystem?.garden_name) {
            validateGardenRouting(targetSystem.garden_name);
          } else {
            clearMessages();
            addMessage({
              severity: "error",
              summary: "Garden Check",
              detail:
                "Unable to find target Garden for command, unable to validate routing",
            });
          }
        }
      })
      .catch((error: any) => {
        clearMessages();
        addMessage({
          severity: "error",
          summary: "Command Check",
          detail: `Error validating command routing: ${error}`,
        });
      });
  };

  useEffect(() => {
    if (!initialized) {
      buildDefaults();
      validateRouting();

      return;
    }
    if (resetForm) {
      setResetForm(false);
      buildDefaults(false);
      return;
    }
    let updated = false;

    if (
      request &&
      (request?.command_type === undefined || request.command_type.length === 0)
    ) {
      updated = true;
      if (
        command?.command_type === undefined ||
        command?.command_type === null
      ) {
        request.command_type = "ACTION";
      } else {
        request.command_type = command?.command_type;
      }
    }

    const changedFields = [] as Array<string>;
    parametersFields.forEach((inputParameter) => {
      if (inputParameter.key === null || inputParameter.key === undefined) {
        return;
      }
      let parameterValue = inputParameter.value;

      if (inputParameter.type === "Dictionary") {
        try {
          parameterValue = JSON.parse(inputParameter.value);
        } catch {
          parameterValue = undefined;
          console.log("Failed Parsing JSON");
        }
      }

      if (
        request &&
        request.parameters &&
        inputParameter.key in request.parameters
      ) {
        if (parameterValue === null || parameterValue === undefined) {
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
      if (parameterValue === null || parameterValue === undefined) {
        return;
      }

      if (request && request.parameters) {
        if (
          inputParameter.key in request.parameters &&
          CompareObjects(request.parameters[inputParameter.key], parameterValue)
        ) {
          return;
        }

        request.parameters[inputParameter.key] = parameterValue;
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
              shouldUpdate ||
              (parameter.options === undefined &&
                !altLoadingChoices.current.some(
                  (loading) => loading.key === parameter.key,
                ))
            ) {
              generateChoices(parameter, parametersFields);
            }
          }
        }
      });
    }

    validateForm();
  }, [parametersFields, initialized, request, setRequest, resetForm]);

  const handleChange = (name: any, value: any) => {
    altParametersFields.current = altParametersFields.current.map((param) =>
      param.key === name ? { ...param, value: value } : param,
    );
    setParameterFields([...altParametersFields.current]);
  };

  const renderInputLabel = (parameter: InputParam) => {
    return (
      <FormLabel htmlFor={parameter.key} sx={{ fontWeight: "bold" }}>
        {parameter.key}
      </FormLabel>
    );
  };

  return (
    <Box
      key={`${request?.namespace}.${request?.system}.${request?.system_version}.${request?.instance_name}.${request?.command}`}
      sx={{ mt: 4, mb: 4 }}
    >
      <Box sx={{ mb: 2 }}>
        {errorMessages.map((msg, index) => (
          <Alert key={index} severity={msg.severity} sx={{ mb: 1 }}>
            <AlertTitle>{msg.summary}</AlertTitle>
            {msg.detail}
          </Alert>
        ))}
      </Box>
      <Stack divider={<Divider flexItem />} spacing={1}>
        {request && request.command_type && (
          <Grid
            container
            key={`${request?.namespace}.${request?.system}.${request?.system_version}.${request?.instance_name}.${request?.command}_COMMAND_TYPE`}
          >
            <Grid size="grow">
              <FormLabel
                id="command-type-label"
                htmlFor="COMMAND_TYPE"
                sx={{ fontWeight: "bold" }}
              >
                Command Type
              </FormLabel>
            </Grid>

            <Grid size="grow">
              <FormControl fullWidth>
                <InputLabel id="command-type-label-select">
                  Command Type
                </InputLabel>
                <Select
                  labelId="command-type-label-select"
                  id="COMMAND_TYPE"
                  label="Command Type"
                  value={request?.command_type}
                  onChange={(e) =>
                    setRequest({ ...request, command_type: e.target.value })
                  }
                  disabled={disabled}
                  size="small"
                >
                  {["ACTION", "INFO", "TEMP"].map((status: any) => (
                    <MenuItem key={status} value={status}>
                      {status}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        )}

        {parametersFields &&
          parametersFields?.map((parameter: InputParam) => (
            <Grid
              container
              key={`${request?.namespace}.${request?.system}.${request?.system_version}.${request?.instance_name}.${request?.command}.${parameter.key}`}
            >
              <Grid size="grow">{renderInputLabel(parameter)}</Grid>
              <Grid size="grow">
                <CommandFormField
                  parameter={parameter}
                  disabled={disabled}
                  parametersFields={parametersFields}
                  loadingChoices={loadingChoices}
                  handleChange={handleChange}
                  resetForm={resetForm}
                />
              </Grid>
            </Grid>
          ))}

        {(() => {
          const commentId = `${request?.namespace}.${request?.system}.${request?.system_version}.${request?.instance_name}.${request?.command}_COMMENT`;
          return (
            <Box
              key={`${commentId}-box`}
              sx={{ display: "flex", justifyContent: "flex-end", m: 1 }}
            >
              <Tooltip title={`Add Comment`}>
                <TextField
                  id={`${commentId}-value`}
                  value={request?.comment}
                  helperText="Add Comment"
                  variant="outlined"
                  onChange={(event: ChangeEvent<HTMLInputElement>) => {
                    setRequest({ ...request, comment: event.target.value });
                  }}
                  fullWidth
                  multiline
                  disabled={disabled}
                  autoComplete="off"
                />
              </Tooltip>
            </Box>
          );
        })()}
      </Stack>
    </Box>
  );
}

export default CommandForm;
