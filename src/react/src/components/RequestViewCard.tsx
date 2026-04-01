import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Badge } from "primereact/badge";
import { Button } from "primereact/button";
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

import CommandForm from "../components/CommandForm";
import { Command, Request, System } from "../models/brewtils-types";
import { RequestItem } from "../models/models";
import { GetRequest, PostRequest } from "../services/request_service";
import { GetSystemList } from "../services/system_service";
import { GetBaseURL } from "../services/util_service";
import RequestOutput from "./RequestOutput";

function UnformattedInput(request: Request) {
  return (
    <div>
      <Message severity="warn" text="Unable to find source System/Command" />
      <pre>{JSON.stringify(request.parameters, null, 2)}</pre>
    </div>
  );
}

function RequestViewCard({
  requestItem,
  updateRequestItem,
  removeItem,
  addItem,
  listeners,
}: {
  requestItem: RequestItem;
  updateRequestItem: (item: RequestItem) => void;
  removeItem: (id: string) => void;
  addItem: (itemParams?: Partial<RequestItem>) => void;
  listeners: Record<string, any>;
}) {
  const requestId = useRef<string | null | undefined>(
    requestItem?.requestId ?? null,
  );
  const [request, setRequest] = useState<Request | null>(
    requestItem?.request ?? null,
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

  const submitRequest = (openRequest: boolean) => {
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
            window.open(
              `${GetBaseURL()}/request/${response_request.id}`,
              "_self",
            );
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

  useEffect(() => {
    const MonitorRequestId = (message: any) => {
      if (message.payload_type === "Request") {
        if (
          requestId.current &&
          message.payload.id &&
          message.payload.id === requestId.current
        ) {
          setRequest(message.payload as Request);
          updateRequestItem({
            ...requestItem,
            ...{ request: message.payload as Request },
          });
        }
      }
    };

    if (!requestId.current) {
      requestId.current = requestItem?.requestId ?? null;

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
          updateRequestItem({
            ...requestItem,
            ...{ request: data },
          });

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
  }, [request, system, command, listeners]);

  const stepperRef = useRef(null);
  const [activeIndex] = useState(1);

  return (
    <Card
      title={CardTitle()}
      className="mr-2 mb-2 mt-2"
      style={{ minWidth: "49%" }}
      header={
        <Button
          onClick={() => {
            removeItem(requestItem.itemId);
          }}
        >
          <FontAwesomeIcon icon="minus" />
        </Button>
      }
    >
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
                    resetForm: false,
                    setResetForm: () => {},
                  }}
                />
              )}
              {showCommandForm && !command && <UnformattedInput {...request} />}
            </StepperPanel>

            <StepperPanel header="Output">
              <RequestOutput {...request} />
            </StepperPanel>
          </Stepper>

          <SplitButton
            label="Open"
            icon="pi pi-plus"
            onClick={() => {
              window.open(`${GetBaseURL()}/request/${request.id}`, "_self");
            }}
            model={[
              {
                label: "Run Again Now",
                // icon: <FontAwesomeIcon icon="arrow-up-right-from-square" />,
                command: () => {
                  submitRequest(false);
                },
              },
              {
                label: "Pour Again",
                // icon: <FontAwesomeIcon icon="arrow-up-from-bracket" />,
                command: () => {
                  addItem({
                    requestId: request.id,
                    type: "REQUEST",
                  } as RequestItem);
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
