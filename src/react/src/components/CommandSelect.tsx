import { validate as validateVersion } from "compare-versions";
import { Dropdown } from "primereact/dropdown";
import { useEffect, useState } from "react";

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
    <div className="border-2 border-dashed surface-border border-round surface-ground flex-auto flex justify-content-center align-items-center font-medium">
      <div>
        <datalist id="selectNamespaceDropdown" aria-hidden="true">
          {namespaces?.map((value: string) => (
            <option key={value} value={value} />
          ))}
        </datalist>
        <Dropdown
          value={selectedNamespace}
          onChange={(e) => {
            setSelectedNamespace(e.value);
          }}
          options={namespaces}
          filter
          optionLabel="Namespace"
          placeholder="Select Namespace"
          aria-label="Select Namespace"
          pt={{
            select: {
              "aria-controls": "selectNamespaceDropdown",
            },
          }}
        />
        <datalist id="selectSystemDropdown" aria-hidden="true">
          {systemNames?.map((value: string) => (
            <option key={value} value={value} />
          ))}
        </datalist>
        <Dropdown
          value={selectedSystemName}
          onChange={(e) => {
            setSelectedSystemName(e.value);
          }}
          options={systemNames}
          filter
          optionLabel="System"
          placeholder="Select System"
          aria-label="Select System"
          pt={{
            select: {
              "aria-controls": "selectSystemDropdown",
            },
          }}
        />
        <datalist id="selectVersionDropdown" aria-hidden="true">
          {versions?.map((value: string) => (
            <option key={value} value={value} />
          ))}
        </datalist>
        <Dropdown
          value={selectedVersion}
          onChange={(e) => {
            setSelectedVersion(e.value);
          }}
          options={versions}
          filter
          optionLabel="Version"
          placeholder="Select Version"
          aria-label="Select Version"
          pt={{
            select: {
              "aria-controls": "selectVersionDropdown",
            },
          }}
        />
        <datalist id="selectInstanceDropdown" aria-hidden="true">
          {instances?.map((value: string) => (
            <option key={value} value={value} />
          ))}
        </datalist>
        <Dropdown
          value={selectedInstance}
          onChange={(e) => {
            setSelectedInstance(e.value);
          }}
          options={instances}
          filter
          optionLabel="Instance"
          placeholder="Select Instance"
          aria-label="Select Instance"
          pt={{
            select: {
              "aria-controls": "selectInstanceDropdown",
            },
          }}
        />
        <datalist id="selectCommandDropdown" aria-hidden="true">
          {commands?.map((value: string) => (
            <option key={value} value={value} />
          ))}
        </datalist>
        <Dropdown
          value={selectedCommand}
          onChange={(e) => {
            setSelectedCommand(e.value);
          }}
          options={commands}
          filter
          optionLabel="Command"
          placeholder="Select Command"
          aria-label="Select Command"
          pt={{
            select: {
              "aria-controls": "selectCommandDropdown",
            },
          }}
        />
      </div>
    </div>
  );
}

export default CommandSelect;
