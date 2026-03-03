import { Badge } from "primereact/badge";
import { Card } from "primereact/card";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { Message } from "primereact/message";
import { Skeleton } from "primereact/skeleton";
import { SplitButton } from "primereact/splitbutton";
import { Stepper } from "primereact/stepper";
import { StepperPanel } from "primereact/stepperpanel";
import { Toast } from "primereact/toast";
import { useEffect, useRef, useState } from "react";

import CommandForm from "../../components/CommandForm";
import { Command, Request, System } from "../../models/brewtils-types";
import { ScratchPadValue } from "../../models/models";
import { GetRequest, PostRequest } from "../../services/request_service";
import { PushToScratchPad } from "../../services/scratchpad_service";
import { GetSystemList } from "../../services/system_service";
import RequestOutput from "../RequestOutput";

function UnformattedInput(request: Request) {
  return (
    <div>
      <Message severity="warn" text="Unable to find source System/Command" />
      <pre>{JSON.stringify(request.parameters, null, 2)}</pre>
    </div>
  );
}

function RequestViewCard({
  padItem,
  updatePadItem,
  reloadScratchPad,
  listeners,
}: {
  padItem: ScratchPadValue;
  updatePadItem: (padItem: ScratchPadValue) => void;
  reloadScratchPad: () => void;
  listeners: Record<string, any>;
}) {
  const requestId = useRef<string | null | undefined>(null);
  const [request, setRequest] = useState<Request | null>(
    padItem?.values?.request ? padItem.values.request : null,
  );
  const [system, setSystem] = useState<System | null>(null);

  const toast = useRef(null as null | any);

  const [command, setCommand] = useState<Command | any>(null);

  const [showCommandForm, setShowCommandForm] = useState(false);

  const SeverityCheck = (status?: string) => {
    if (!status) {
      return "danger";
    }
    if (["CREATED"].includes(status)) {
      return "info";
    }
    if (["IN_PROGRESS"].includes(status)) {
      return "warning";
    }
    if (["SUCCESS"].includes(status)) {
      return "success";
    }
    return "danger";
  };

  const statusTemplate = (request: Request) => {
    return (
      <Badge value={request.status} severity={SeverityCheck(request?.status)} />
    );
  };

  const CardTitle = () => {
    let title = "Request View";
    if (request?.namespace && request?.system && request?.instance_name) {
      title =
        request.namespace +
        " / " +
        request.system +
        " / " +
        request.instance_name;
    }
    if (request?.command_display_name) {
      title += " / " + request.command_display_name;
    } else if (request?.command) {
      title += " / " + request.command;
    }
    return title;
  };

  const submitRequest = (openRequest: boolean, addToScratchPad?: boolean) => {
    if (request) {
      PostRequest({
        namespace: request?.namespace || undefined,
        system: request?.system || undefined,
        system_version: request?.system_version || undefined,
        instance_name: request?.instance_name || undefined,
        command: request?.command || undefined,
        parameters: request?.parameters || {},
      } as Request)
        .then((response_request: any) => {
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

  const cloneAndPushToScratchPad = () => {
    if (request) {
      PushToScratchPad("REQUEST", {
        requestCommand: {
          namespace: request.namespace ?? null,
          systemName: request.system ?? null,
          version: request.system_version ?? null,
          instance: request.instance_name ?? null,
          command: request.command ?? null,
        },
        request: {
          namespace: request.namespace,
          system: request.system,
          system_version: request.system_version,
          instance_name: request.instance_name,
          command: request.command,
          parameters: request.parameters,
        },
      });
      reloadScratchPad();
    }
  };

  useEffect(() => {
    const updateScratchPadValues = () => {
      updatePadItem({
        ...padItem,
        values: {
          ...padItem.values,
          request: request,
          requestId: requestId.current,
        },
      });
    };

    const MonitorRequestId = (message: any) => {
      if (message.payload_type === "Request") {
        if (
          requestId.current &&
          message.payload.id &&
          message.payload.id === requestId.current
        ) {
          setRequest(message.payload as Request);
          updateScratchPadValues();
        }
      }
    };

    if (!requestId.current) {
      requestId.current = padItem?.values?.requestId
        ? padItem.values.requestId
        : null;

      if (
        request &&
        request.status &&
        ["CREATED", "IN_PROGRESS"].includes(request.status)
      ) {
        // First load, force a refresh of data to ensure latest is rendered in case the completed
        // event has already been received before the listener was registered
        setRequest(null);
      }
    }

    if (!request && requestId.current) {
      GetRequest(requestId.current, {})
        .then((data: Request) => {
          setRequest(data);
          updateScratchPadValues();

          if (
            requestId.current &&
            !(requestId.current in listeners) &&
            data.status &&
            ["CREATED", "IN_PROGRESS"].includes(data.status)
          ) {
            listeners[requestId.current] = {
              listener: MonitorRequestId,
            };
          }
        })
        .catch((error) => {
          console.error("Error fetching request:", error);
        });
    }

    if (
      request &&
      requestId.current &&
      !(requestId.current in listeners) &&
      request?.status &&
      ["CREATED", "IN_PROGRESS"].includes(request.status)
    ) {
      listeners[requestId.current] = {
        listener: MonitorRequestId,
      };
    }

    if (
      requestId.current &&
      requestId.current in listeners &&
      request?.status &&
      !["CREATED", "IN_PROGRESS"].includes(request.status)
    ) {
      delete listeners[requestId.current];
    }

    if (request && !system) {
      GetSystemList({
        name: request.system,
        version: request.system_version,
        namespace: request.namespace,
        garden_name: request.target_garden,
      })
        .then((data) => {
          if (data.length > 0) {
            setSystem(data[0]);
          } else {
            setShowCommandForm(true);
          }
        })
        .catch((error) => {
          console.error("Error fetching system list:", error);
          setShowCommandForm(true);
        });
    }

    if (system && !command) {
      if (system && system.commands && request) {
        const commandData = system.commands.find(
          (cmd) => cmd.name === request.command,
        );
        setCommand(commandData);
        setShowCommandForm(true);
      }
    }

    return () => {
      if (requestId.current) {
        delete listeners[requestId.current];
      }
    };
  }, [request, system, command, listeners, padItem, updatePadItem]);

  const stepperRef = useRef(null);
  const [activeIndex] = useState(1);

  return (
    <Card title={CardTitle()}>
      <Toast ref={toast} />
      {request && (
        <div>
          <DataTable value={[request]}>
            <Column field="command" header="Command"></Column>
            <Column header="Status" body={statusTemplate}></Column>
          </DataTable>
          <Stepper
            ref={stepperRef}
            activeStep={activeIndex}
            style={{ flexBasis: "50rem" }}
          >
            <StepperPanel header="Parameters">
              {!showCommandForm && <Skeleton width="100%" height="10rem" />}
              {showCommandForm && command && (
                <CommandForm
                  {...{
                    command: command,
                    request: request,
                    setRequest: setRequest,
                  }}
                />
              )}
              {showCommandForm && !command && <UnformattedInput {...request} />}
            </StepperPanel>
            <StepperPanel header="Hide" />
            <StepperPanel header="Output">
              <RequestOutput {...request} />
            </StepperPanel>
          </Stepper>

          <SplitButton
            label="Open"
            icon="pi pi-plus"
            onClick={() => {
              window.open("/request/" + request.id, "_self");
            }}
            model={[
              {
                label: "Run Again",
                // icon: <FontAwesomeIcon icon="arrow-up-right-from-square" />,
                command: () => {
                  submitRequest(false);
                },
              },
              {
                label: "Run Again and Add to Scratch Pad",
                // icon: <FontAwesomeIcon icon="arrow-up-from-bracket" />,
                command: () => {
                  submitRequest(true, true);
                },
              },
              {
                label: "Clone Request and Open",
                // icon: <FontAwesomeIcon icon="arrow-up-from-bracket" />,
                command: () => {
                  window.open("/recreate/" + request.id, "_self");
                },
              },
              {
                label: "Clone Request and Add to Scratch Pad",
                // icon: <FontAwesomeIcon icon="arrow-up-from-bracket" />,
                command: () => {
                  cloneAndPushToScratchPad();
                },
              },
            ]}
          />
        </div>
      )}
    </Card>
  );
}

export default RequestViewCard;
