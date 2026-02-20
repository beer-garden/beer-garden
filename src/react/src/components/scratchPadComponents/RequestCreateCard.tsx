import { Card } from "primereact/card";
import { SplitButton } from "primereact/splitbutton";
import { Toast } from "primereact/toast";
import { useEffect, useRef, useState } from "react";

import CommandForm from "../../components/CommandForm";
import CommandSelect from "../../components/CommandSelect";
import { Command, Request, System } from "../../models/brewtils-types";
import { ScratchPadValue } from "../../models/models";
import { PostRequest } from "../../services/request_service";
import { PushToScratchPad } from "../../services/scratchpad_service";
import { GetSystemList } from "../../services/system_service";

interface RequestCommand {
  namespace: string | null;
  systemName: string | null;
  version: string | null;
  instance: string | null;
  command: string | null;
}

function RequestCreateCard({
  padItem,
  updatePadItem,
  reloadScratchPad,
}: {
  padItem: ScratchPadValue;
  updatePadItem: (padItem: ScratchPadValue) => void;
  reloadScratchPad: () => void;
}) {
  const [request, setRequest] = useState<Request | null>(
    padItem?.values?.request ? padItem.values.request : null,
  );

  const toast = useRef(null as null | any);

  // System Panel
  const [requestCommand, setRequestCommand] = useState<RequestCommand | null>(
    padItem?.values?.requestCommand
      ? padItem.values.requestCommand
      : {
          namespace: null,
          systemName: null,
          version: null,
          instance: null,
          command: null,
        },
  );

  const [systems, setSystems] = useState<Array<System>>([]);

  // Command Panel
  const [showCommand, setShowCommand] = useState<boolean>(false);
  const [command, setCommand] = useState<Command | null>(null);
  // const [validCommand, setValidCommand] = useState(false);

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
    const updateScratchPadValues = () => {
      updatePadItem({
        ...padItem,
        values: {
          ...padItem.values,
          requestCommand: requestCommand,
          request: request,
        },
      });
    };

    function findCommand() {
      setShowCommand(false);
      if (systems && systems.length > 0) {
        systems.forEach((system) => {
          if (
            system.namespace === requestCommand?.namespace &&
            system.name === requestCommand?.systemName &&
            system.version === requestCommand?.version
          ) {
            if (system.instances) {
              system.instances.forEach((instance) => {
                if (instance.name === requestCommand?.instance) {
                  if (system.commands) {
                    system.commands.forEach((command) => {
                      if (command.name === requestCommand?.command) {
                        setCommand(command);
                        setShowCommand(true);
                        return;
                      }
                    });
                  }
                }
              });
            }
          }
        });
      }
    }

    // Target Command Changed, need to update
    if (
      requestCommand?.namespace &&
      requestCommand.namespace !== request?.namespace &&
      requestCommand?.systemName &&
      requestCommand.systemName !== request?.system &&
      requestCommand?.version &&
      requestCommand.version !== request?.system_version &&
      requestCommand?.instance &&
      requestCommand.instance !== request?.instance_name &&
      requestCommand?.command &&
      requestCommand.command !== request?.command
    ) {
      setRequest({
        namespace: requestCommand?.namespace || undefined,
        system: requestCommand?.systemName || undefined,
        system_version: requestCommand?.version || undefined,
        instance_name: requestCommand?.instance || undefined,
        command: requestCommand?.command || undefined,
      });
      findCommand();
      updateScratchPadValues();
    }

    // Command is null, have all values to populate it
    else if (
      systems &&
      systems.length > 0 &&
      !command &&
      requestCommand?.namespace &&
      requestCommand?.systemName &&
      requestCommand?.version &&
      requestCommand?.instance &&
      requestCommand?.command
    ) {
      findCommand();
    } else {
      // Event from Request or Command
      updateScratchPadValues();
    }
  }, [systems, requestCommand, request, command, padItem, updatePadItem]);

  const submitRequest = (openRequest: boolean, addToScratchPad?: boolean) => {
    if (request) {
      PostRequest(request)
        .then((response_request) => {
          if (openRequest) {
            if (addToScratchPad) {
              PushToScratchPad("REQUEST_VIEW", {
                requestId: response_request.id,
                request: response_request,
              });
              reloadScratchPad();
            } else {
              window.open("/request/" + response_request.id, "_self");
            }
          } else {
            toast?.current?.show({
              severity: "info",
              summary: "Info",
              detail: "Request Created: " + response_request.id,
            });
          }
        })
        .catch((error) => {
          console.error("Error creating request:", error);
        });
    }
  };

  return (
    <Card title="Create Request">
      <Toast ref={toast} />
      <CommandSelect
        systems={systems}
        requestCommand={requestCommand}
        setRequestCommand={setRequestCommand}
        validCommand={true}
        setValidCommand={() => {}}
      />
      {showCommand && (
        <div>
          <CommandForm
            command={command}
            disabled={false}
            request={request}
            setRequest={setRequest}
          />
          <SplitButton
            label="Run"
            icon="pi pi-plus"
            onClick={() => {
              submitRequest(false);
            }}
            model={[
              {
                label: " Run and Open",
                // icon: <FontAwesomeIcon icon="arrow-up-right-from-square" />,
                command: () => {
                  submitRequest(true);
                },
              },
              {
                label: " Run and Add to Scratch Pad",
                // icon: <FontAwesomeIcon icon="arrow-up-from-bracket" />,
                command: () => {
                  submitRequest(true, true);
                },
              },
            ]}
          />
        </div>
      )}
    </Card>
  );
}

export default RequestCreateCard;
