import { useState, useRef, useEffect } from "react";
import { Button } from "primereact/button";
import { Card } from "primereact/card";
import CommandSelect from "../../components/CommandSelect";
import CommandForm from "../../components/CommandForm";
import { Request, System, Command } from "../../models/brewtils-types";
import { GetSystemList } from "../../services/system_service";
import { PostRequest } from "../../services/request_service";
import { Toast } from "primereact/toast";

interface RequestCommand {
  namespace: string | null;
  systemName: string | null;
  version: string | null;
  instance: string | null;
  command: string | null;
}

function RequestCreateCard({
  values,
  updateValues,
}: {
  values: any;
  updateValues: (values: any) => void;
}) {
  const [request, setRequest] = useState<Request | null>(
    values.request ? values.request : null,
  );

  const toast = useRef(null as null | any);

  // System Panel
  const [requestCommand, setRequestCommand] = useState<RequestCommand | null>(
    values.requestCommand
      ? values.requestCommand
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

  function findCommand() {
    let foundCommand = false;
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
                      foundCommand = true;
                      return;
                    }
                  });
                }
              }
            });
          }
        }
      });
    } else {
      console.error("Missing Systems for Commands");
      return;
    }

    if (!foundCommand) {
      console.error("Missing Command");
      // setShowCommand(false);
    }
  }

  const updateScratchPadValues = () => {
    updateValues({
      ...values,
      ...{ requestCommand: requestCommand, request: request },
    });
  };

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
    findCommand();
  }, [systems]);

  useEffect(() => {
    if (
      requestCommand?.namespace &&
      requestCommand?.systemName &&
      requestCommand?.version &&
      requestCommand?.instance &&
      requestCommand?.command
    ) {
      if (
        requestCommand.namespace !== request?.namespace ||
        requestCommand?.systemName !== request?.system ||
        requestCommand?.version !== request?.system_version ||
        requestCommand?.instance !== request?.instance_name ||
        requestCommand?.command !== request?.command
      ) {
        setRequest({
          namespace: requestCommand?.namespace || undefined,
          system: requestCommand?.systemName || undefined,
          system_version: requestCommand?.version || undefined,
          instance_name: requestCommand?.instance || undefined,
          command: requestCommand?.command || undefined,
        });
      }
      findCommand();
    } else {
      updateScratchPadValues();
    }
  }, [requestCommand]);

  useEffect(() => {
    updateScratchPadValues();
  }, [request]);

  const submitRequest = (openRequest: boolean) => {
    if (request) {
      PostRequest(request).then((response_request) => {
        if (openRequest) {
          window.open("/request/" + response_request.id, "_self");
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

  return (
    <Card title="Create Request">
      <Toast ref={toast} />
      <CommandSelect
        systems={systems}
        requestCommand={requestCommand}
        setRequestCommand={setRequestCommand}
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
          <Button
            label="Run Now"
            severity="success"
            icon="pi pi-arrow-right"
            iconPos="right"
            onClick={(e) => submitRequest(true)}
          />
          <Button
            label="Run Background"
            severity="success"
            icon="pi pi-arrow-right"
            iconPos="right"
            onClick={(e) => submitRequest(false)}
          />
          {/* <Button
            label="Run Here"
            severity="success"
            icon="pi pi-arrow-right"
            iconPos="right"
            onClick={(e) => submitRequest(false)}
          /> */}
        </div>
      )}
    </Card>
  );
}

export default RequestCreateCard;
