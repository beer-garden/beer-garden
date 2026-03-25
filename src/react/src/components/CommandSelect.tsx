import { validate as validateVersion } from "compare-versions";
import { Dropdown } from "primereact/dropdown";
import { useEffect, useState } from "react";

import { Command, Instance, System } from "../models/brewtils-types";
import { DetermineLatestSystemVersion } from "../services/system_service";
import { CompareObjects } from "../services/util_service";

interface RequestCommand {
  namespace: string | null;
  systemName: string | null;
  version: string | null;
  instance: string | null;
  command: string | null;
}

interface CommandSelectProps {
  systems: Array<System> | null;
  requestCommand: RequestCommand | null;
  setRequestCommand: (request: RequestCommand) => void;
  validCommand: boolean;
  setValidCommand: (valid: boolean) => void;
}

function CommandSelect({
  systems,
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

  const [selectedNamespace, setSelectedNamespace] = useState<string | null>(
    requestCommand?.namespace ?? null,
  );
  const [selectedSystemName, setSelectedSystemName] = useState<string | null>(
    requestCommand?.systemName ?? null,
  );
  const [selectedVersion, setSelectedVersion] = useState<string | null>(
    requestCommand?.version ?? null,
  );
  const [selectedInstance, setSelectedInstance] = useState<string | null>(
    requestCommand?.instance ?? null,
  );
  const [selectedCommand, setSelectedCommand] = useState<string | null>(
    requestCommand?.command ?? null,
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
      setNamespaces(namespaceList);
    }

    if (!CompareObjects(systemNames, systemNameList)) {
      setSystemNames(systemNameList);
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
        setVersions(systemVersionList);
      } else {
        setVersions(generateLatestSystemVersions(systemVersionList));
      }
    }

    if (!CompareObjects(instances, instanceList)) {
      setInstances(instanceList);
    }

    if (!CompareObjects(commands, commandList)) {
      setCommands(commandList);
    }

    if (namespaceList.length === 1 && selectedNamespace !== namespaceList[0]) {
      setSelectedNamespace(namespaceList[0]);
    } else if (
      namespaceList.length > 0 &&
      selectedNamespace !== null &&
      !namespaceList.includes(selectedNamespace)
    ) {
      setSelectedNamespace(null);
    }

    if (
      systemNameList.length === 1 &&
      selectedSystemName !== systemNameList[0]
    ) {
      setSelectedSystemName(systemNameList[0]);
    } else if (
      systemNameList.length > 0 &&
      selectedSystemName !== null &&
      !systemNameList.includes(selectedSystemName)
    ) {
      setSelectedSystemName(null);
    }

    if (
      selectedVersion !== "latest" &&
      (selectedVersion === null ||
        !systemVersionList.includes(selectedVersion)) &&
      ((systemVersionList.length === 2 && systemVersionList[1] === "latest") ||
        systemVersionList.length === 1)
    ) {
      setSelectedVersion(systemVersionList[0]);
    } else if (
      selectedVersion !== null &&
      selectedVersion !== "latest" &&
      !systemVersionList.includes(selectedVersion)
    ) {
      setSelectedVersion(null);
    }

    if (instanceList.length === 1 && selectedInstance !== instanceList[0]) {
      setSelectedInstance(instanceList[0]);
    } else if (
      instanceList.length > 0 &&
      selectedInstance !== null &&
      !instanceList.includes(selectedInstance)
    ) {
      setSelectedInstance(null);
    }

    if (commandList.length === 1 && selectedCommand !== commandList[0]) {
      setSelectedCommand(commandList[0]);
    } else if (
      commandList.length > 0 &&
      selectedCommand !== null &&
      !commandList.includes(selectedCommand)
    ) {
      setSelectedCommand(null);
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
      <Dropdown
        value={selectedNamespace}
        onChange={(e) => setSelectedNamespace(e.value)}
        options={namespaces}
        filter
        optionLabel="Namespace"
        placeholder="Select Namespace"
      />  
      <Dropdown
        value={selectedSystemName}
        onChange={(e) => setSelectedSystemName(e.value)}
        options={systemNames}
        filter
        optionLabel="System"
        placeholder="Select System"
      />
      <Dropdown
        value={selectedVersion}
        onChange={(e) => setSelectedVersion(e.value)}
        options={versions}
        filter
        optionLabel="Version"
        placeholder="Select Version"
      />
      <Dropdown
        value={selectedInstance}
        onChange={(e) => setSelectedInstance(e.value)}
        options={instances}
        filter
        optionLabel="Instance"
        placeholder="Select Instance"
      />
      <Dropdown
        value={selectedCommand}
        onChange={(e) => setSelectedCommand(e.value)}
        options={commands}
        filter
        optionLabel="Command"
        placeholder="Select Command"
      />
      </div>
    </div>
  );
}

export default CommandSelect;
