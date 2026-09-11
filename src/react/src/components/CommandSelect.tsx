import { Box } from "@mui/material";
import Autocomplete from "@mui/material/Autocomplete";
import TextField from "@mui/material/TextField";
import { validate as validateVersion } from "compare-versions";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { Command, Instance, System } from "../models/brewtils-types";
import { RequestCommand } from "../models/models";
import { DetermineLatestSystemVersion } from "../services/system_service";
import { CompareObjects } from "../services/util_service";

interface CommandSelectProps {
  systems: Array<System> | null;
  setSelectedSystem: (system: System | undefined) => void;
  requestCommand: RequestCommand | undefined;
  setRequestCommand: (requestCommand: RequestCommand) => void;
  validCommand: boolean;
  setValidCommand: (valid: boolean) => void;
}

function CommandSelect({
  systems,
  setSelectedSystem,
  requestCommand,
  setRequestCommand,
  validCommand,
  setValidCommand,
}: CommandSelectProps) {
  const [namespaces, setNamespaces] = useState<Array<string>>([]);
  const [systemNames, setSystemNames] = useState<Array<string>>([]);
  const [versions, setVersions] = useState<Array<string>>([]);
  const [instances, setInstances] = useState<Array<string>>([]);
  const [commands, setCommands] = useState<Array<string>>([]);

  const [selectedNamespace, setSelectedNamespace] = useState<
    string | undefined
  >(requestCommand?.namespace ?? undefined);
  const [selectedSystemName, setSelectedSystemName] = useState<
    string | undefined
  >(requestCommand?.systemName ?? undefined);
  const [selectedVersion, setSelectedVersion] = useState<string | undefined>(
    requestCommand?.version ?? undefined,
  );
  const [selectedInstance, setSelectedInstance] = useState<string | undefined>(
    requestCommand?.instance ?? undefined,
  );
  const [selectedCommand, setSelectedCommand] = useState<string | undefined>(
    requestCommand?.command ?? undefined,
  );

  const [_searchParams, setSearchParams] = useSearchParams();

  useEffect(() => {
    const namespaceList: Array<string> = [];
    const systemNameList: Array<string> = [];
    const systemVersionList: Array<string> = [];
    const instanceList: Array<string> = [];
    const commandList: Array<string> = [];

    if (systems) {
      systems.forEach((system: System) => {
        if (!namespaceList.includes(system.namespace as string)) {
          namespaceList.push(system.namespace as string);
        }

        if (system.name !== null && system.namespace === selectedNamespace) {
          if (!systemNameList.includes(system.name as string)) {
            systemNameList.push(system.name as string);
          }
          if (system.version !== null && system.name === selectedSystemName) {
            if (!systemVersionList.includes(system.version as string)) {
              systemVersionList.push(system.version as string);
            }

            if (
              system.version === selectedVersion ||
              (selectedVersion?.toLowerCase() === "latest" &&
                DetermineLatestSystemVersion(
                  systems,
                  selectedSystemName,
                  selectedNamespace,
                  selectedVersion,
                ).version === system.version)
            ) {
              if (system.instances) {
                system.instances.forEach((instance: Instance) => {
                  if (instance.name && !instanceList.includes(instance.name)) {
                    instanceList.push(instance.name);
                  }
                });
              }
              if (system.commands) {
                system.commands.forEach((command: Command) => {
                  if (command.name && !commandList.includes(command.name)) {
                    commandList.push(command.name);
                  }
                });
              }
            }
          }
        }
      });
    }

    // Check if change
    if (!CompareObjects(namespaces, namespaceList)) {
      setNamespaces(
        namespaceList.sort((a: string, b: string) => a.localeCompare(b)),
      );
    }

    if (!CompareObjects(systemNames, systemNameList)) {
      setSystemNames(
        systemNameList.sort((a: string, b: string) => a.localeCompare(b)),
      );
    }

    const generateLatestSystemVersions = (
      versions: Array<string>,
    ): Array<string> => {
      if (
        versions.some(
          (version) =>
            validateVersion(version) ||
            validateVersion(version.replace(".dev", "-dev")),
        )
      ) {
        return [...systemVersionList, "latest"];
      }
      return versions;
    };

    if (
      !CompareObjects(versions, generateLatestSystemVersions(systemVersionList))
    ) {
      if (systemVersionList.includes("latest")) {
        setVersions(
          systemVersionList.sort((a: string, b: string) => a.localeCompare(b)),
        );
      } else {
        setVersions(
          generateLatestSystemVersions(systemVersionList).sort(
            (a: string, b: string) => a.localeCompare(b),
          ),
        );
      }
    }

    if (!CompareObjects(instances, instanceList)) {
      setInstances(
        instanceList.sort((a: string, b: string) => a.localeCompare(b)),
      );
    }

    if (!CompareObjects(commands, commandList)) {
      setCommands(
        commandList.sort((a: string, b: string) => a.localeCompare(b)),
      );
    }

    if (namespaceList.length === 1 && selectedNamespace !== namespaceList[0]) {
      setSelectedNamespace(namespaceList[0]);
      setSearchParams((params) => {
        params.set("namespace", namespaceList[0]);
        return params;
      });
    } else if (
      namespaceList.length > 0 &&
      selectedNamespace !== undefined &&
      !namespaceList.includes(selectedNamespace)
    ) {
      setSelectedNamespace(undefined);
    }

    if (
      systemNameList.length === 1 &&
      selectedSystemName !== systemNameList[0]
    ) {
      setSelectedSystemName(systemNameList[0]);
      setSearchParams((params) => {
        if (selectedNamespace) {
          params.set("namespace", selectedNamespace);
        }
        params.set("system", systemNameList[0]);
        return params;
      });
    } else if (
      systemNameList.length > 0 &&
      selectedSystemName !== undefined &&
      !systemNameList.includes(selectedSystemName)
    ) {
      setSelectedSystemName(undefined);
    }

    if (
      selectedVersion !== "latest" &&
      (selectedVersion === undefined ||
        !systemVersionList.includes(selectedVersion)) &&
      ((systemVersionList.length === 2 && systemVersionList[1] === "latest") ||
        systemVersionList.length === 1)
    ) {
      setSelectedVersion(systemVersionList[0]);
      setSearchParams((params) => {
        if (selectedNamespace) {
          params.set("namespace", selectedNamespace);
        }
        if (selectedSystemName) {
          params.set("system", selectedSystemName);
        }
        params.set("version", systemVersionList[0]);
        return params;
      });
    } else if (
      selectedVersion !== undefined &&
      selectedVersion !== "latest" &&
      !systemVersionList.includes(selectedVersion)
    ) {
      setSelectedVersion(undefined);
    }

    if (instanceList.length === 1 && selectedInstance !== instanceList[0]) {
      setSelectedInstance(instanceList[0]);
    } else if (
      instanceList.length > 0 &&
      selectedInstance !== undefined &&
      !instanceList.includes(selectedInstance)
    ) {
      setSelectedInstance(undefined);
    }

    if (commandList.length === 1 && selectedCommand !== commandList[0]) {
      setSelectedCommand(commandList[0]);
      setSearchParams((params) => {
        if (selectedNamespace) {
          params.set("namespace", selectedNamespace);
        }
        if (selectedSystemName) {
          params.set("system", selectedSystemName);
        }
        if (selectedVersion) {
          params.set("version", selectedVersion);
        }
        if (selectedInstance) {
          params.set("instance", selectedInstance);
        }
        params.set("command", commandList[0]);
        return params;
      });
    } else if (
      commandList.length > 0 &&
      selectedCommand !== undefined &&
      !commandList.includes(selectedCommand)
    ) {
      setSelectedCommand(undefined);
    }

    setSearchParams((params) => {
      if (selectedNamespace) {
        params.set("namespace", selectedNamespace);
      } else {
        params.delete("namespace");
      }
      if (selectedSystemName) {
        params.set("system", selectedSystemName);
      } else {
        params.delete("system");
      }
      if (selectedVersion) {
        params.set("version", selectedVersion);
      } else {
        params.delete("version");
      }
      if (selectedInstance) {
        params.set("instance", selectedInstance);
      } else {
        params.delete("instance");
      }
      if (selectedCommand) {
        params.set("command", selectedCommand);
      } else {
        params.delete("command");
      }
      return params;
    });

    if (
      requestCommand?.namespace !== selectedNamespace ||
      requestCommand?.systemName !== selectedSystemName ||
      requestCommand?.version !== selectedVersion ||
      requestCommand?.instance !== selectedInstance ||
      requestCommand?.command !== selectedCommand
    ) {
      if (
        !requestCommand?.command ||
        !commands ||
        commands.length === 0 ||
        !commands.includes(requestCommand.command)
      ) {
        if (validCommand) {
          setValidCommand(false);
        }
      } else if (
        !requestCommand?.instance ||
        !instances ||
        instances.length === 0 ||
        !instances.includes(requestCommand.instance)
      ) {
        if (validCommand) {
          setValidCommand(false);
        }
      } else if (
        !requestCommand?.version ||
        !versions ||
        versions.length === 0 ||
        !versions.includes(requestCommand.version)
      ) {
        if (validCommand) {
          setValidCommand(false);
        }
      } else if (
        !requestCommand?.systemName ||
        !systemNames ||
        systemNames.length === 0 ||
        !systemNames.includes(requestCommand.systemName)
      ) {
        if (validCommand) {
          setValidCommand(false);
        }
      } else if (
        !requestCommand?.namespace ||
        !namespaces ||
        namespaces.length === 0 ||
        !namespaces.includes(requestCommand.namespace)
      ) {
        if (validCommand) {
          setValidCommand(false);
        }
      } else {
        if (!validCommand) {
          setValidCommand(true);
        }
      }
      setRequestCommand({
        namespace: selectedNamespace,
        systemName: selectedSystemName,
        version: selectedVersion,
        instance: selectedInstance,
        command: selectedCommand,
      });
      setSelectedSystem(
        systems?.find(
          (system) =>
            system.name === selectedSystemName &&
            system.version === selectedVersion &&
            system.namespace === selectedNamespace,
        ),
      );
    }
  }, [
    systems,
    requestCommand,
    commands,
    instances,
    versions,
    systemNames,
    namespaces,
    selectedNamespace,
    selectedSystemName,
    selectedVersion,
    selectedInstance,
    selectedCommand,
    validCommand,
    setValidCommand,
    setRequestCommand,
  ]);

  return (
    <Box
      sx={{
        display: "flex",
        mb: 2,
        border: "2px dashed grey",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Autocomplete
        sx={{ width: "100%", m: 2 }}
        id={`select-namespace`}
        disabled={namespaces && namespaces.length === 0}
        options={namespaces}
        value={selectedNamespace ?? null}
        onChange={(_event: any, newValue: string | null) => {
          setSelectedNamespace(newValue === null ? undefined : newValue);
        }}
        renderInput={(params) => <TextField {...params} label="Namespace" />}
      />
      <Autocomplete
        sx={{ width: "100%", m: 2 }}
        id={`select-system`}
        disabled={systemNames && systemNames.length === 0}
        options={systemNames}
        value={selectedSystemName ?? null}
        onChange={(_event: any, newValue: string | null) => {
          setSelectedSystemName(newValue === null ? undefined : newValue);
        }}
        renderInput={(params) => <TextField {...params} label="System" />}
      />
      <Autocomplete
        sx={{ width: "100%", m: 2 }}
        id={`select-version`}
        options={versions}
        value={selectedVersion ?? null}
        onChange={(_event: any, newValue: string | null) => {
          setSelectedVersion(newValue === null ? undefined : newValue);
        }}
        disabled={versions && versions.length === 0}
        renderInput={(params) => <TextField {...params} label="Version" />}
      />
      <Autocomplete
        sx={{ width: "100%", m: 2 }}
        id={`select-instance`}
        options={instances}
        value={selectedInstance ?? null}
        onChange={(_event: any, newValue: string | null) => {
          setSelectedInstance(newValue === null ? undefined : newValue);
        }}
        disabled={instances && instances.length === 0}
        renderInput={(params) => <TextField {...params} label="Instance" />}
      />
      <Autocomplete
        sx={{ width: "100%", m: 2 }}
        id={`select-command`}
        options={commands}
        value={selectedCommand ?? null}
        onChange={(_event: any, newValue: string | null) => {
          setSelectedCommand(newValue === null ? undefined : newValue);
        }}
        disabled={commands && commands.length === 0}
        renderInput={(params) => <TextField {...params} label="Command" />}
      />
    </Box>
  );
}

export default CommandSelect;
