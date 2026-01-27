import { useState, useEffect } from "react";
import { Dropdown } from "primereact/dropdown";
import { System, Command, Instance } from "../models/brewtils-types";

interface RequestCommand {
  namespace: string | null;
  systemName: string | null;
  version: string | null;
  instance: string | null;
  command: string | null;
}

interface CreateRequestProps {
  systems: Array<System> | null;
  request: Request | null;
}

interface CommandSelectProps {
  systems: Array<System> | null;
  requestCommand: RequestCommand | null;
  setRequestCommand: (request: RequestCommand) => void;
  setValidCommand: (valid: boolean) => void;
}

function CommandSelect({
  systems,
  requestCommand,
  setRequestCommand,
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
    setRequestCommand({
      namespace: selectedNamespace,
      systemName: selectedSystemName,
      version: selectedVersion,
      instance: selectedInstance,
      command: selectedCommand,
    });
  }, [
    selectedNamespace,
    selectedSystemName,
    selectedVersion,
    selectedInstance,
    selectedCommand,
  ]);

  useEffect(() => {
    if (
      !requestCommand?.command ||
      !commands ||
      commands.length === 0 ||
      !commands.includes(requestCommand.command)
    ) {
      setValidCommand(false);
      return;
    }
    if (
      !requestCommand?.instance ||
      !instances ||
      instances.length === 0 ||
      !instances.includes(requestCommand.instance)
    ) {
      setValidCommand(false);
      return;
    }
    if (
      !requestCommand?.version ||
      !versions ||
      versions.length === 0 ||
      !versions.includes(requestCommand.version)
    ) {
      setValidCommand(false);
      return;
    }
    if (
      !requestCommand?.systemName ||
      !systemNames ||
      systemNames.length === 0 ||
      !systemNames.includes(requestCommand.systemName)
    ) {
      setValidCommand(false);
      return;
    }
    if (
      !requestCommand?.namespace ||
      !namespaces ||
      namespaces.length === 0 ||
      !namespaces.includes(requestCommand.namespace)
    ) {
      setValidCommand(false);
      return;
    }

    setValidCommand(true);
  }, [requestCommand, commands, instances, versions, systemNames, namespaces]);

  useEffect(() => {
    let namespaceList: Array<string> = [];
    let systemNameList: Array<string> = [];
    let systemVersionList: Array<string> = [];
    let instanceList: Array<string> = [];
    let commandList: Array<string> = [];

    if (systems) {
      systems.forEach((system: System) => {
        if (!namespaceList.includes(system.namespace as string)) {
          namespaceList.push(system.namespace as string);
        }

        if (requestCommand) {
          if (
            requestCommand.namespace !== null &&
            system.name !== null &&
            system.namespace === requestCommand.namespace
          ) {
            if (!systemNameList.includes(system.name as string)) {
              systemNameList.push(system.name as string);
            }
            if (
              requestCommand.systemName !== null &&
              system.version !== null &&
              system.name === requestCommand.systemName
            ) {
              if (!systemVersionList.includes(system.version as string)) {
                systemVersionList.push(system.version as string);
              }

              if (
                requestCommand.version !== null &&
                system.version === requestCommand.version
              ) {
                if (system.instances) {
                  system.instances.forEach((instance: Instance) => {
                    if (
                      instance.name &&
                      !instanceList.includes(instance.name as string)
                    ) {
                      instanceList.push(instance.name as string);
                    }
                  });
                }
                if (system.commands) {
                  system.commands.forEach((command: Command) => {
                    if (
                      command.name &&
                      !commandList.includes(command.name as string)
                    ) {
                      commandList.push(command.name as string);
                    }
                  });
                }
              }
            }
          }
        }
      });
    }

    setNamespaces(namespaceList);
    setSystemNames(systemNameList);
    setVersions(systemVersionList);
    setInstances(instanceList);
    setCommands(commandList);

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
      systemVersionList.length === 1 &&
      selectedVersion !== systemVersionList[0]
    ) {
      setSelectedVersion(systemVersionList[0]);
    } else if (
      systemVersionList.length > 0 &&
      selectedVersion !== null &&
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
  }, [systems, requestCommand]);

  return (
    <div className="border-2 border-dashed surface-border border-round surface-ground flex-auto flex justify-content-center align-items-center font-medium">
      <Dropdown
        value={selectedNamespace}
        onChange={(e) => setSelectedNamespace(e.value)}
        options={namespaces}
        optionLabel="Namespace"
        placeholder="Select Namespace"
      />
      <Dropdown
        value={selectedSystemName}
        onChange={(e) => setSelectedSystemName(e.value)}
        options={systemNames}
        optionLabel="System"
        placeholder="Select System"
      />
      <Dropdown
        value={selectedVersion}
        onChange={(e) => setSelectedVersion(e.value)}
        options={versions}
        optionLabel="Version"
        placeholder="Select Version"
      />
      <Dropdown
        value={selectedInstance}
        onChange={(e) => setSelectedInstance(e.value)}
        options={instances}
        optionLabel="Instance"
        placeholder="Select Instance"
      />
      <Dropdown
        value={selectedCommand}
        onChange={(e) => setSelectedCommand(e.value)}
        options={commands}
        optionLabel="Command"
        placeholder="Select Command"
      />
    </div>
  );
}

export default CommandSelect;
