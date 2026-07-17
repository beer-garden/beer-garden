import { Box } from "@mui/material";
import MenuItem from "@mui/material/MenuItem";
import TextField from "@mui/material/TextField";
import { validate as validateVersion } from "compare-versions";
import { ChangeEvent, useEffect, useState } from "react";

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
    } else if (
      commandList.length > 0 &&
      selectedCommand !== undefined &&
      !commandList.includes(selectedCommand)
    ) {
      setSelectedCommand(undefined);
    }

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
      {namespaces.length === 0 && (
        <TextField
          sx={{ width: "100%", m: 2 }}
          id={`select-namespace`}
          select
          disabled
          label="Namespace"
          placeholder="Select Namespace"
          slotProps={{
            input: { "aria-label": "Select Namespace" },
          }}
        />
      )}
      {namespaces.length > 0 && (
        <TextField
          sx={{ width: "100%", m: 2 }}
          id={`select-namespace`}
          select
          label="Namespace"
          value={selectedNamespace}
          onChange={(event: ChangeEvent<HTMLInputElement>) => {
            setSelectedNamespace(event.target.value);
          }}
          placeholder="Select Namespace"
          slotProps={{
            input: { "aria-label": "Select Namespace" },
          }}
        >
          {namespaces.map((option) => (
            <MenuItem key={option} value={option}>
              {option}
            </MenuItem>
          ))}
        </TextField>
      )}

      {systemNames.length === 0 && (
        <TextField
          sx={{ width: "100%", mr: 2, mt: 2, mb: 2 }}
          id={`select-system`}
          select
          label="System"
          placeholder="Select System"
          slotProps={{
            input: { "aria-label": "Select System" },
          }}
        />
      )}
      {systemNames.length > 0 && (
        <TextField
          sx={{ width: "100%", mr: 2, mt: 2, mb: 2 }}
          id={`select-system`}
          select
          label="System"
          value={selectedSystemName}
          onChange={(event: ChangeEvent<HTMLInputElement>) => {
            setSelectedSystemName(event.target.value);
          }}
          placeholder="Select System"
          slotProps={{
            input: { "aria-label": "Select System" },
          }}
        >
          {systemNames.map((option) => (
            <MenuItem key={option} value={option}>
              {option}
            </MenuItem>
          ))}
        </TextField>
      )}

      {versions.length === 0 && (
        <TextField
          sx={{ width: "100%", mr: 2, mt: 2, mb: 2 }}
          id={`select-version`}
          select
          label="Version"
          disabled
          placeholder="Select Version"
          slotProps={{
            input: { "aria-label": "Select Version" },
          }}
        />
      )}
      {versions.length > 0 && (
        <TextField
          sx={{ width: "100%", mr: 2, mt: 2, mb: 2 }}
          id={`select-version`}
          select
          label="Version"
          value={selectedVersion}
          onChange={(event: ChangeEvent<HTMLInputElement>) => {
            setSelectedVersion(event.target.value);
          }}
          placeholder="Select Version"
          slotProps={{
            input: { "aria-label": "Select Version" },
          }}
        >
          {versions.map((option) => (
            <MenuItem key={option} value={option}>
              {option}
            </MenuItem>
          ))}
        </TextField>
      )}

      {instances.length === 0 && (
        <TextField
          sx={{ width: "100%", mr: 2, mt: 2, mb: 2 }}
          id={`select-instance`}
          select
          label="Instance"
          disabled
          placeholder="Select Instance"
          slotProps={{
            input: { "aria-label": "Select Instance" },
          }}
        />
      )}
      {instances.length > 0 && (
        <TextField
          sx={{ width: "100%", mr: 2, mt: 2, mb: 2 }}
          id={`select-instance`}
          select
          label="Instance"
          value={selectedInstance}
          onChange={(event: ChangeEvent<HTMLInputElement>) => {
            setSelectedInstance(event.target.value);
          }}
          placeholder="Select Instance"
          slotProps={{
            input: { "aria-label": "Select Instance" },
          }}
        >
          {instances.map((option) => (
            <MenuItem key={option} value={option}>
              {option}
            </MenuItem>
          ))}
        </TextField>
      )}

      {commands.length === 0 && (
        <TextField
          sx={{ width: "100%", mr: 2, mt: 2, mb: 2 }}
          id={`select-command`}
          select
          disabled
          label="Command"
          placeholder="Select Command"
          slotProps={{
            input: { "aria-label": "Select Command" },
          }}
        />
      )}
      {commands.length > 0 && (
        <TextField
          sx={{ width: "100%", mr: 2, mt: 2, mb: 2 }}
          id={`select-command`}
          select
          label="Command"
          value={selectedCommand}
          onChange={(event: ChangeEvent<HTMLInputElement>) => {
            setSelectedCommand(event.target.value);
          }}
          placeholder="Select Command"
          slotProps={{
            input: { "aria-label": "Select Command" },
          }}
        >
          {commands.map((option) => (
            <MenuItem key={option} value={option}>
              {option}
            </MenuItem>
          ))}
        </TextField>
      )}
    </Box>
  );
}

export default CommandSelect;
