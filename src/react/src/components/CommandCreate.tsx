import { Skeleton } from "primereact/skeleton";
import { Toast } from "primereact/toast";
import { useEffect, useRef, useState } from "react";

import CommandForm from "../components/CommandForm";
import CommandSelect from "../components/CommandSelect";
import { Command, Request, System } from "../models/brewtils-types";
import { RequestCommand } from "../models/models";
import {
  DetermineLatestSystemVersion,
  GetSystemList,
} from "../services/system_service";

function CommandCreate({
  request,
  setRequest,
  requestCommand,
  setRequestCommand,
  resetForm,
  setResetForm,
  callback,
}: {
  request?: Request;
  setRequest: (request: Request) => void;
  requestCommand: RequestCommand;
  setRequestCommand: (requestCommand: RequestCommand) => void;
  resetForm: boolean;
  setResetForm: (reset: boolean) => void;
  callback?: () => void;
}) {
  const toast = useRef(null as null | any);

  const [systems, setSystems] = useState<Array<System>>([]);

  // Command Panel
  const [showCommand, setShowCommand] = useState<boolean>(false);
  const [command, setCommand] = useState<Command | null>(null);

  // Effect only runs at startup to get systems
  useEffect(() => {
    GetSystemList()
      .then((data) => {
        setSystems(data);
      })
      .catch((error) => {
        console.error("Error fetching system list:", error);
      });
  }, []);

  useEffect(() => {
    const findCommand = () => {
      setShowCommand(false);
      if (systems && systems.length > 0) {
        const latestSystem = DetermineLatestSystemVersion(
          systems,
          requestCommand?.systemName,
          requestCommand?.namespace,
          requestCommand?.version,
        );

        if (latestSystem && latestSystem.instances) {
          latestSystem.instances.forEach((instance) => {
            if (instance.name === requestCommand?.instance) {
              if (latestSystem.commands) {
                latestSystem.commands.forEach((command) => {
                  if (command.name === requestCommand?.command) {
                    setCommand(command);
                    return;
                  }
                });
              }
            }
          });
        }
      }
    };

    const migrateRequest = () => {
      const updatedRequest: Request = {
        namespace: requestCommand?.namespace || undefined,
        system: requestCommand?.systemName || undefined,
        system_version: requestCommand?.version || undefined,
        instance_name: requestCommand?.instance || undefined,
        command: requestCommand?.command || undefined,
        parameters: {},
      };

      for (const [key, value] of Object.entries(request?.parameters || {})) {
        if (command?.parameters && updatedRequest.parameters) {
          command.parameters.forEach((parameter) => {
            if (parameter.key === key) {
              updatedRequest.parameters![key] = value;
            }
          });
        }
      }
      setRequest(updatedRequest);
      setShowCommand(true);
      if (callback) {
        callback();
      }
    };

    // Target Command Changed, need to update
    if (
      command !== null &&
      requestCommand?.namespace &&
      requestCommand?.systemName &&
      requestCommand?.version &&
      requestCommand?.instance &&
      requestCommand?.command &&
      (requestCommand.namespace !== request?.namespace ||
        requestCommand.systemName !== request?.system ||
        requestCommand.version !== request?.system_version ||
        requestCommand.instance !== request?.instance_name ||
        requestCommand.command !== request?.command)
    ) {
      // These all have to be different loops to allow for React to Render changes
      if (showCommand) {
        // Selected Command changed via dropdown and new command needs to be found
        setCommand(null);
        setShowCommand(false);
      } else {
        // New Command found and need to migrate old request to new command
        migrateRequest();
      }

      if (callback) {
        callback();
      }
    }

    // Command is null, have all values to populate it
    else if (
      systems &&
      systems.length > 0 &&
      command === null &&
      requestCommand?.namespace &&
      requestCommand?.systemName &&
      requestCommand?.version &&
      requestCommand?.instance &&
      requestCommand?.command
    ) {
      findCommand();
    } else {
      if (command !== null && !showCommand) {
        setShowCommand(true);
      }
      // Event from Request or Command
      if (callback) {
        callback();
      }
    }
  }, [
    systems,
    requestCommand,
    request,
    command,
    showCommand,
    setRequest,
    setShowCommand,
    setCommand,
    callback,
  ]);

  return (
    <div>
      <Toast ref={toast} />
      {systems && systems.length > 0 && (
        <CommandSelect
          systems={systems}
          requestCommand={requestCommand}
          setRequestCommand={setRequestCommand}
          validCommand={true}
          setValidCommand={() => {}}
        />
      )}
      {showCommand && (
        <div>
          <CommandForm
            command={command}
            disabled={false}
            request={request}
            setRequest={setRequest}
            resetForm={resetForm}
            setResetForm={setResetForm}
          />
        </div>
      )}
      {(!systems || systems.length === 0 || !showCommand) && (
        <Skeleton width="100%" height="150px"></Skeleton>
      )}
    </div>
  );
}

export default CommandCreate;
