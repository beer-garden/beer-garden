import { useState, useRef, useEffect } from "react";
import { Button } from "primereact/button";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Card } from "primereact/card";
import CommandForm from "../../components/CommandForm";
import { Request, System, Command } from "../../models/brewtils-types";
import { GetSystemList } from "../../services/system_service";
import { Toast } from "primereact/toast";
import RequestOutput from "../RequestOutput";
import { GetRequest, DeleteRequest } from "../../services/request_service";
import { DataTable } from "primereact/datatable";
import { Column } from "primereact/column";
import { Badge } from "primereact/badge";
import { Stepper } from "primereact/stepper";
import { StepperPanel } from "primereact/stepperpanel";
import { Message } from "primereact/message";

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
  listeners,
}: {
  values: any;
  updateValues: (values: any) => void;
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

  const optionsTemplate = (request: Request) => {
    return (
      <div>
        <Button
          rounded
          raised
          link
          onClick={() => window.open("/request/" + request.id, "_self")}
        >
          <FontAwesomeIcon icon="arrow-up-right-from-square" />
        </Button>
        <Button
          rounded
          raised
          link
          onClick={() => {
            DeleteRequest(request).then(() => {
              // getCurrentRequests();
            });
          }}
        >
          <FontAwesomeIcon icon="xmark" />
        </Button>
      </div>
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
  useEffect(() => {
    requestId.current = values.requestId ? values.requestId : null;
    if (!request && requestId.current) {
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
            <Column header="Options" body={optionsTemplate}></Column>
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

          <Button
            label="Open Request"
            severity="success"
            icon="pi pi-arrow-right"
            iconPos="right"
            onClick={(e) => {}}
          />
        </div>
      )}
    </Card>
  );
}

export default RequestViewCard;
