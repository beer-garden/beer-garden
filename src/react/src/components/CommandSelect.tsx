import { useState, useRef, useEffect } from "react";
import { Dropdown } from "primereact/dropdown";
import { System, Command, Instance } from "../models/brewtils-types";
import { GetSystemList } from "../services/system_service";

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

  useEffect(() => {
    if (systems && namespaces.length == 0) {
      let namespaceList: Array<string> = [];

      systems.forEach((system: System) => {
        if (!namespaceList.includes(system.namespace as string)) {
          namespaceList.push(system.namespace as string);
        }
      });
      setNamespaces(namespaceList);
    }
  }, [systems]);

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

    let updatedRequest = {
      namespace: requestCommand?.namespace ?? null,
      systemName: requestCommand?.systemName ?? null,
      version: requestCommand?.version ?? null,
      instance: requestCommand?.instance ?? null,
      command: requestCommand?.command ?? null,
    };

    let pushUpdate = false;

    if (
      namespaceList.length === 1 &&
      updatedRequest.namespace !== namespaceList[0]
    ) {
      pushUpdate = true;
      updatedRequest.namespace = namespaceList[0];
    } else if (
      namespaceList.length > 0 &&
      updatedRequest.namespace !== null &&
      !namespaceList.includes(updatedRequest.namespace)
    ) {
      pushUpdate = true;
      updatedRequest.namespace = null;
    }

    if (
      systemNameList.length === 1 &&
      updatedRequest.systemName !== systemNameList[0]
    ) {
      pushUpdate = true;
      updatedRequest.systemName = systemNameList[0];
    } else if (
      systemNameList.length > 0 &&
      updatedRequest.systemName !== null &&
      !systemNameList.includes(updatedRequest.systemName)
    ) {
      pushUpdate = true;
      updatedRequest.systemName = null;
    }

    if (
      systemVersionList.length === 1 &&
      updatedRequest.version !== systemVersionList[0]
    ) {
      pushUpdate = true;
      updatedRequest.version = systemVersionList[0];
    } else if (
      systemVersionList.length > 0 &&
      updatedRequest.version !== null &&
      !systemVersionList.includes(updatedRequest.version)
    ) {
      pushUpdate = true;
      updatedRequest.version = null;
    }

    if (
      instanceList.length === 1 &&
      updatedRequest.instance !== instanceList[0]
    ) {
      pushUpdate = true;
      updatedRequest.instance = instanceList[0];
    } else if (
      instanceList.length > 0 &&
      updatedRequest.instance !== null &&
      !instanceList.includes(updatedRequest.instance)
    ) {
      pushUpdate = true;
      updatedRequest.instance = null;
    }

    if (commandList.length === 1 && updatedRequest.command !== commandList[0]) {
      pushUpdate = true;
      updatedRequest.command = commandList[0];
    } else if (
      commandList.length > 0 &&
      updatedRequest.command !== null &&
      !commandList.includes(updatedRequest.command)
    ) {
      pushUpdate = true;
      updatedRequest.command = null;
    }

    if (pushUpdate) {
      setRequestCommand(updatedRequest);
    }
  }, [requestCommand]);

  return (
    <div className="border-2 border-dashed surface-border border-round surface-ground flex-auto flex justify-content-center align-items-center font-medium">
      <Dropdown
        value={requestCommand?.namespace}
        onChange={(e) => {
          setRequestCommand({
            namespace: e.value as string,
            systemName: requestCommand?.systemName ?? null,
            version: requestCommand?.version ?? null,
            instance: requestCommand?.instance ?? null,
            command: requestCommand?.command ?? null,
          });
        }}
        options={namespaces}
        optionLabel="Namespace"
        placeholder="Select Namespace"
      />
      <Dropdown
        value={requestCommand?.systemName}
        onChange={(e) => {
          setRequestCommand({
            namespace: requestCommand?.namespace ?? null,
            systemName: e.value as string,
            version: requestCommand?.version ?? null,
            instance: requestCommand?.instance ?? null,
            command: requestCommand?.command ?? null,
          });
        }}
        options={systemNames}
        optionLabel="System"
        placeholder="Select System"
      />
      <Dropdown
        value={requestCommand?.version}
        onChange={(e) => {
          setRequestCommand({
            namespace: requestCommand?.namespace ?? null,
            systemName: requestCommand?.systemName ?? null,
            version: e.value as string,
            instance: requestCommand?.instance ?? null,
            command: requestCommand?.command ?? null,
          });
        }}
        options={versions}
        optionLabel="Version"
        placeholder="Select Version"
      />
      <Dropdown
        value={requestCommand?.instance}
        onChange={(e) => {
          setRequestCommand({
            namespace: requestCommand?.namespace ?? null,
            systemName: requestCommand?.systemName ?? null,
            version: requestCommand?.version ?? null,
            instance: e.value as string,
            command: requestCommand?.command ?? null,
          });
        }}
        options={instances}
        optionLabel="Instance"
        placeholder="Select Instance"
      />
      <Dropdown
        value={requestCommand?.command}
        onChange={(e) => {
          setRequestCommand({
            namespace: requestCommand?.namespace ?? null,
            systemName: requestCommand?.systemName ?? null,
            version: requestCommand?.version ?? null,
            instance: requestCommand?.instance ?? null,
            command: e.value as string,
          });
        }}
        options={commands}
        optionLabel="Command"
        placeholder="Select Command"
      />
    </div>
  );
}

export default CommandSelect;
