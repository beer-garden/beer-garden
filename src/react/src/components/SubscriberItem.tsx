import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  Autocomplete,
  Box,
  FilterOptionsState,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { grey } from "@mui/material/colors";
import React, { useEffect, useRef } from "react";

import { Subscriber, System } from "../models/brewtils-types";
import { useSnackbar } from "../providers/SnackbarProvider";
import { GetSystemList } from "../services/system_service";
import AccessButton from "./AccessButton";

interface SubscriberItemProps {
  subscriberList: Array<Subscriber>;
  setSubscriberList: React.Dispatch<React.SetStateAction<Array<Subscriber>>>;
  isEdit: boolean;
}

function SubscriberItem({
  subscriberList,
  setSubscriberList,
  isEdit,
}: SubscriberItemProps) {
  const allSystems = useRef<Array<System>>([]);

  const showSnackbar = useSnackbar();

  useEffect(() => {
    GetSystemList()
      .then((data) => {
        allSystems.current = data;
      })
      .catch((error) => {
        console.error("Error fetching system list:", error);
        showSnackbar({
          severity: "error",
          summary: "Error",
          detail: `Error fetching system list: ${error}`,
          life: 3000,
        });
      });
  }, []);

  function handleClose(indexToRemove: number) {
    setSubscriberList((currentList) => {
      return [
        ...currentList.slice(0, indexToRemove),
        ...currentList.slice(indexToRemove + 1),
      ];
    });
  }

  function handleAddSubscriber() {
    setSubscriberList([
      ...subscriberList,
      {
        namespace: "",
        garden: "",
        system: "",
        version: "",
        instance: "",
        command: "",
      } as Subscriber,
    ]);
  }

  function handleUpdateSubscriber(
    inputKey:
      | "namespace"
      | "garden"
      | "system"
      | "version"
      | "instance"
      | "command",
    inputValue: any,
    inputIndex: number,
  ) {
    if (inputValue.trim()) {
      setSubscriberList((currentList) => {
        const newList = currentList.map((subscriber, index) => {
          if (index == inputIndex) {
            subscriber[inputKey] = inputValue;
            if (inputKey == "garden") {
              subscriber["namespace"] = "";
            }
            if (inputKey == "garden" || inputKey == "namespace") {
              subscriber["system"] = "";
            }
            if (
              inputKey == "garden" ||
              inputKey == "namespace" ||
              inputKey == "system"
            ) {
              subscriber["version"] = "";
              subscriber["instance"] = "";
              subscriber["command"] = "";
            }
          }
          return subscriber;
        });
        return newList;
      });
    }
  }

  const escapeRegExp = (patternString: string) => {
    // 1. Escape special regex characters except the dot and star
    const escaped = patternString.replace(/[-/\\^$+[\]{}()|?]/g, "\\$&");

    // 2. Un-escape the '.*' combination specifically so it stays active
    const regexString = escaped.replace(/\\\.\\\*/g, ".*");

    // 3. Return the compiled RegExp object
    return new RegExp(regexString);
  };

  return (
    <Box sx={{ my: 1 }}>
      {!isEdit && (
        <Typography sx={{ fontWeight: "bold" }}>Subscribers</Typography>
      )}
      {subscriberList.map((subscriber, index) => (
        <Box
          key={index}
          sx={{
            border: "1px solid",
            borderColor: grey[300],
            borderRadius: 2,
            p: 2,
          }}
        >
          <Box
            sx={{
              display: "flex",
              justifyContent: "flex-end",
              width: "100%",
            }}
          >
            {!isEdit && (
              <AccessButton
                tooltip="Remove"
                onClick={() => handleClose(index)}
                sx={{ my: 1 }}
              >
                <FontAwesomeIcon icon="close" />
              </AccessButton>
            )}
          </Box>
          <Stack spacing={1}>
            <Autocomplete
              id={`garden-${index}`}
              value={subscriber.garden}
              options={[]}
              onChange={(_, newValue: any) => {
                handleUpdateSubscriber("garden", newValue, index);
              }}
              filterOptions={(_, state: FilterOptionsState<string>) => {
                const options = [] as string[];
                for (const system of allSystems.current) {
                  const matchValue = system?.garden_name;
                  if (
                    // Check Ref Value
                    matchValue !== undefined &&
                    !options.includes(matchValue) &&
                    // Regex Check
                    (matchValue.includes(state.inputValue) ||
                      matchValue.match(escapeRegExp(state.inputValue)))
                  ) {
                    options.push(matchValue);
                  }
                }
                return options;
              }}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Garden Name"
                  variant="outlined"
                  placeholder="Garden Name"
                />
              )}
            />

            <Autocomplete
              id={`namespace-${index}`}
              value={subscriber.namespace}
              options={[]}
              onChange={(_, newValue: any) => {
                handleUpdateSubscriber("namespace", newValue, index);
              }}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Namespace"
                  variant="outlined"
                  placeholder="Namespace"
                />
              )}
              filterOptions={(_, state: FilterOptionsState<string>) => {
                const options = [] as string[];
                for (const system of allSystems.current) {
                  const matchValue = system?.namespace;

                  if (
                    // Check Ref Value
                    matchValue !== undefined &&
                    !options.includes(matchValue) &&
                    // Regex Check
                    (matchValue.includes(state.inputValue) ||
                      matchValue.match(escapeRegExp(state.inputValue))) &&
                    // Check Garden Mapping
                    (subscriber.garden === undefined ||
                      (system.garden_name !== undefined &&
                        (system.garden_name.includes(subscriber.garden) ||
                          system.garden_name.match(
                            escapeRegExp(subscriber.garden),
                          ))))
                  ) {
                    options.push(matchValue);
                  }
                }
                return options;
              }}
            />

            <Autocomplete
              id={`system-${index}`}
              value={subscriber.system}
              options={[]}
              onChange={(_, newValue: any) => {
                handleUpdateSubscriber("system", newValue, index);
              }}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="System Name"
                  variant="outlined"
                  placeholder="System Name"
                />
              )}
              filterOptions={(_, state: FilterOptionsState<string>) => {
                const options = [] as string[];
                for (const system of allSystems.current) {
                  const matchValue = system?.name;

                  if (
                    // Check Ref Value
                    matchValue !== undefined &&
                    !options.includes(matchValue) &&
                    // Regex Check
                    (matchValue.includes(state.inputValue) ||
                      matchValue.match(escapeRegExp(state.inputValue))) &&
                    // Check Garden Mapping
                    (subscriber.garden === undefined ||
                      (system.garden_name !== undefined &&
                        (system.garden_name.includes(subscriber.garden) ||
                          system.garden_name.match(
                            escapeRegExp(subscriber.garden),
                          )))) &&
                    // Check Namespace Mapping
                    (subscriber.namespace === undefined ||
                      (system.namespace !== undefined &&
                        (system.namespace.includes(subscriber.namespace) ||
                          system.namespace.match(
                            escapeRegExp(subscriber.namespace),
                          ))))
                  ) {
                    options.push(matchValue);
                  }
                }
                return options;
              }}
            />

            <Autocomplete
              id={`version-${index}`}
              value={subscriber.version}
              options={[]}
              onChange={(_, newValue: any) =>
                handleUpdateSubscriber("version", newValue, index)
              }
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="System Version"
                  variant="outlined"
                  placeholder="System Version"
                />
              )}
              filterOptions={(_, state: FilterOptionsState<string>) => {
                const options = [] as string[];
                for (const system of allSystems.current) {
                  const matchValue = system?.version;

                  if (
                    // Check Ref Value
                    matchValue !== undefined &&
                    !options.includes(matchValue) &&
                    // Regex Check
                    (matchValue.includes(state.inputValue) ||
                      matchValue.match(escapeRegExp(state.inputValue))) &&
                    // Check Garden Mapping
                    (subscriber.garden === undefined ||
                      (system.garden_name !== undefined &&
                        (system.garden_name.includes(subscriber.garden) ||
                          system.garden_name.match(
                            escapeRegExp(subscriber.garden),
                          )))) &&
                    // Check Namespace Mapping
                    (subscriber.namespace === undefined ||
                      (system.namespace !== undefined &&
                        (system.namespace.includes(subscriber.namespace) ||
                          system.namespace.match(
                            escapeRegExp(subscriber.namespace),
                          )))) &&
                    // Check Name Mapping
                    (subscriber.system === undefined ||
                      (system.name !== undefined &&
                        (system.name.includes(subscriber.system) ||
                          system.name.match(escapeRegExp(subscriber.system)))))
                  ) {
                    options.push(matchValue);
                  }
                }
                return options;
              }}
            />

            <Autocomplete
              id={`instance-${index}`}
              value={subscriber.instance}
              options={[]}
              onChange={(_, newValue: any) =>
                handleUpdateSubscriber("instance", newValue, index)
              }
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="System Instance"
                  variant="outlined"
                  placeholder="System Instance"
                />
              )}
              filterOptions={(_, state: FilterOptionsState<string>) => {
                const options = [] as string[];

                for (const system of allSystems.current) {
                  if (
                    // Check Ref Value
                    system.instances !== undefined &&
                    system.instances.length > 0 &&
                    // Check Garden Mapping
                    (subscriber.garden === undefined ||
                      (system.garden_name !== undefined &&
                        (system.garden_name.includes(subscriber.garden) ||
                          system.garden_name.match(
                            escapeRegExp(subscriber.garden),
                          )))) &&
                    // Check Namespace Mapping
                    (subscriber.namespace === undefined ||
                      (system.namespace !== undefined &&
                        (system.namespace.includes(subscriber.namespace) ||
                          system.namespace.match(
                            escapeRegExp(subscriber.namespace),
                          )))) &&
                    // Check Name Mapping
                    (subscriber.system === undefined ||
                      (system.name !== undefined &&
                        (system.name.includes(subscriber.system) ||
                          system.name.match(
                            escapeRegExp(subscriber.system),
                          )))) &&
                    // Check Version Mapping
                    (subscriber.version === undefined ||
                      (system.version !== undefined &&
                        (system.version.includes(subscriber.version) ||
                          system.version.match(
                            escapeRegExp(subscriber.version),
                          ))))
                  ) {
                    for (const instanceValue of system.instances) {
                      const matchValue = instanceValue.name;
                      if (
                        matchValue !== undefined &&
                        !options.includes(matchValue) &&
                        // Regex Check
                        (matchValue.includes(state.inputValue) ||
                          matchValue.match(escapeRegExp(state.inputValue)))
                      ) {
                        options.push(matchValue);
                      }
                    }
                  }
                }
                return options;
              }}
            />

            <Autocomplete
              id={`command-${index}`}
              value={subscriber.command}
              options={[]}
              onChange={(_, newValue: any) =>
                handleUpdateSubscriber("command", newValue, index)
              }
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Command Name"
                  variant="outlined"
                  placeholder="Command Name"
                />
              )}
              filterOptions={(_, state: FilterOptionsState<string>) => {
                const options = [] as string[];

                for (const system of allSystems.current) {
                  if (
                    // Check Ref Value
                    system.commands !== undefined &&
                    system.commands.length > 0 &&
                    // Check Garden Mapping
                    (subscriber.garden === undefined ||
                      (system.garden_name !== undefined &&
                        (system.garden_name.includes(subscriber.garden) ||
                          system.garden_name.match(
                            escapeRegExp(subscriber.garden),
                          )))) &&
                    // Check Namespace Mapping
                    (subscriber.namespace === undefined ||
                      (system.namespace !== undefined &&
                        (system.namespace.includes(subscriber.namespace) ||
                          system.namespace.match(
                            escapeRegExp(subscriber.namespace),
                          )))) &&
                    // Check Name Mapping
                    (subscriber.system === undefined ||
                      (system.name !== undefined &&
                        (system.name.includes(subscriber.system) ||
                          system.name.match(
                            escapeRegExp(subscriber.system),
                          )))) &&
                    // Check Version Mapping
                    (subscriber.version === undefined ||
                      (system.version !== undefined &&
                        (system.version.includes(subscriber.version) ||
                          system.version.match(
                            escapeRegExp(subscriber.version),
                          )))) &&
                    // Check Instance Mapping
                    (subscriber.instance === undefined ||
                      (system.instances !== undefined &&
                        system.instances.some(
                          (instanceValue) =>
                            subscriber.instance !== undefined &&
                            instanceValue.name !== undefined &&
                            (instanceValue.name.includes(subscriber.instance) ||
                              instanceValue.name.match(
                                escapeRegExp(subscriber.instance),
                              )),
                        )))
                  ) {
                    for (const commandValue of system.commands) {
                      const matchValue = commandValue.name;
                      if (
                        matchValue !== undefined &&
                        !options.includes(matchValue) &&
                        // Regex Check
                        (matchValue.includes(state.inputValue) ||
                          matchValue.match(escapeRegExp(state.inputValue)))
                      ) {
                        options.push(matchValue);
                      }
                    }
                  }
                }
                return options;
              }}
            />
          </Stack>
        </Box>
      ))}
      {!isEdit && (
        <AccessButton
          sx={{ my: 1 }}
          label={"Add subscriber"}
          onClick={handleAddSubscriber}
        >
          Add subscriber
        </AccessButton>
      )}
    </Box>
  );
}

export default SubscriberItem;
