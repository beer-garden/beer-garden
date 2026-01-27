import { useState, useRef, useEffect } from "react";
import { Button } from "primereact/button";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Card } from "primereact/card";
import CommandForm from "../../components/CommandForm";
import { Request, System, Command } from "../../models/brewtils-types";
import { GetSystemList } from "../../services/system_service";
import { Toast } from "primereact/toast";
import RequestOutput from "../RequestOutput";
import {
  GetRequest,
  DeleteRequest,
  PostRequest,
} from "../../services/request_service";
import { DataTable } from "primereact/datatable";
import { Column } from "primereact/column";
import { Badge } from "primereact/badge";
import { Stepper } from "primereact/stepper";
import { StepperPanel } from "primereact/stepperpanel";
import { Message } from "primereact/message";
import { SplitButton } from "primereact/splitbutton";
import { PushToScratchPad } from "../../services/scratchpad_service";

interface RequestCommand {
  namespace: string | null;
  systemName: string | null;
  version: string | null;
  instance: string | null;
  command: string | null;
}
function UnformattedInput(request: Request) {
  return (
    <div>
      <Message severity="warn" text="Unable to find source System/Command" />
      <pre>{JSON.stringify(request.parameters, null, 2)}</pre>
    </div>
  );
}

function RequestViewCard({
  values,
  updateValues,
  reloadScratchPad,
  listeners,
}: {
  values: any;
  updateValues: (values: any) => void;
  reloadScratchPad: () => void;
  listeners: Record<string, any>;
}) {
  const requestId = useRef<string | null | undefined>(null);
  const [request, setRequest] = useState<Request | null>(
    values.request ? values.request : null,
  );
  const [system, setSystem] = useState<System | null>(null);

  const toast = useRef(null as null | any);

  const [command, setCommand] = useState<Command | any>(null);

  const updateScratchPadValues = () => {
    updateValues({
      ...values,
      ...{ request: request, requestId: requestId.current },
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
      }
    }
  };

  const header = (
    <div className="flex flex-wrap align-items-center justify-content-between gap-2">
      <span className="text-xl text-900 font-bold">Current Requests</span>
    </div>
  );
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
      } as Request).then((response_request: any) => {
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
    requestId.current = values.requestId ? values.requestId : null;
    if (
      (!request ||
        (request?.status &&
          ["CREATED", "IN_PROGRESS"].includes(request.status))) &&
      requestId.current
    ) {
      GetRequest(requestId.current, {})
        .then((data: Request) => {
          setRequest(data);

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
    return () => {
      if (requestId.current) {
        delete listeners[requestId.current];
      }
    };
  }, []);

  useEffect(() => {
    if (request) {
      if (
        request.status &&
        ["CANCELED", "SUCCESS", "ERROR", "INVALID"].includes(request.status)
      ) {
        if (requestId.current && requestId.current in listeners) {
          delete listeners[requestId.current];
        }
      }

      const systems = GetSystemList({
        name: request.system,
        version: request.system_version,
        namespace: request.namespace,
        garden_name: request.target_garden,
      })
        .then((data) => {
          if (data.length > 0) {
            setSystem(data[0]);
          }
        })
        .catch((error) => {
          console.error("Error fetching system list:", error);
        });
    }
    updateScratchPadValues();
  }, [request]);

  useEffect(() => {
    if (system && system.commands && request) {
      const commandData = system.commands.find(
        (cmd) => cmd.name === request.command,
      );
      setCommand(commandData);
    }
  }, [system]);

  const stepperRef = useRef(null);
  const [activeIndex, setActiveIndex] = useState(1);

  return (
    <Card title={CardTitle()}>
      <Toast ref={toast} />
      {request && (
        <div>
          <DataTable value={[request]}>
            <Column field="command" header="Command"></Column>
            <Column header="Status" body={statusTemplate}></Column>
            {/* <Column header="Options" body={optionsTemplate}></Column> */}
          </DataTable>
          <Stepper
            ref={stepperRef}
            activeStep={activeIndex}
            style={{ flexBasis: "50rem" }}
          >
            <StepperPanel header="Parameters">
              {command && (
                <CommandForm
                  {...{
                    command: command,
                    request: request,
                    setRequest: setRequest,
                  }}
                />
              )}
              {!command && <UnformattedInput {...request} />}
            </StepperPanel>
            <StepperPanel header="Hide" />
            <StepperPanel header="Output">
              <RequestOutput {...request} />
            </StepperPanel>
          </Stepper>
          {/* <RequestOutput {...request} /> */}

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
