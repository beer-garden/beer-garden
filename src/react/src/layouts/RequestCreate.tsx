import React, { useState, useRef, useEffect } from "react";
import { Stepper } from "primereact/stepper";
import { StepperPanel } from "primereact/stepperpanel";
import { Button } from "primereact/button";
import { Dropdown } from "primereact/dropdown";
import { Request, System, Command, Instance } from "../models/brewtils-types";
import { GetSystemList } from "../services/system_service";
import CommandSelect from "../components/CommandSelect";
import { GetRequest } from "../services/request_service";
import CommandForm from "../components/CommandForm";
import { ConfirmDialog, confirmDialog } from "primereact/confirmdialog";
import { PostRequest } from "../services/request_service";
import { useParams } from "react-router-dom";
import { Skeleton } from "primereact/skeleton";

interface RequestCommand {
  namespace: string | null;
  systemName: string | null;
  version: string | null;
  instance: string | null;
  command: string | null;
}

function RequestCreate() {
  const { requestId } = useParams<{ requestId: string }>();
  const { jobId } = useParams<{ jobId: string }>();

  const stepperRef = useRef<null | any>(null);

  const scheduleHeader = "Schedule";
  const selectCommandHeader = "Select Command";
  const createRequestHeader = "Create Request";

  // Input Request
  const [request, setRequest] = useState<Request | null>(null);

  // System Panel
  const [requestCommand, setRequestCommand] = useState<RequestCommand | null>({
    namespace: null,
    systemName: null,
    version: null,
    instance: null,
    command: null,
  });

  const [systems, setSystems] = useState<Array<System>>([]);

  // Command Panel
  const [showCommand, setShowCommand] = useState<boolean>(false);
  const [command, setCommand] = useState<Command | null>(null);

  function findCommand() {
    if (systems) {
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

  const resetRequest = () => {
    setRequest({
      namespace: requestCommand?.namespace || undefined,
      system: requestCommand?.systemName || undefined,
      system_version: requestCommand?.version || undefined,
      instance_name: requestCommand?.instance || undefined,
      command: requestCommand?.command || undefined,
    });
    setShowCommand(true);
  };

  const migrateRequest = () => {
    let updatedRequest: Request = {
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
  };

  const nextStep = (nextStep: string) => {
    stepperRef.current?.nextCallback();
  };

  const prevStep = (prevStep: string) => {
    stepperRef.current?.prevCallback();
  };

  const submitRequest = () => {
    if (request) {
      PostRequest(request).then((response_request) => {
        window.open("/request/" + response_request.id, "_self");
      });
    }
  };

  const indexCheck = (index: any) => {
    console.log(index);
    if (index === 2) {
      findCommand();
      if (
        request !== null &&
        (request.namespace !== requestCommand?.namespace ||
          request.system !== requestCommand?.systemName ||
          request.system_version !== requestCommand?.version ||
          request.instance_name !== requestCommand?.instance ||
          request.command !== requestCommand?.command)
      ) {
        // Current Request doesn't match the targeted Command, need to migrate

        setShowCommand(false);
        confirmDialog({
          message:
            "Target Command changed, do you want to migrate matching input parameters?",
          header: "Command change",
          icon: "pi pi-exclamation-triangle",
          defaultFocus: "accept",
          accept: migrateRequest,
          reject: resetRequest,
        });
      } else {
        setShowCommand(true);
      }
    }
  };

  useEffect(() => {
    if (requestId !== null && requestId !== undefined) {
      GetRequest(requestId, {}).then((responseRequest) => {
        setRequest({
          namespace: responseRequest.namespace,
          system: responseRequest.system,
          system_version: responseRequest.system_version,
          instance_name: responseRequest.instance_name,
          command: responseRequest.command,
          parameters: responseRequest.parameters,
        });
        setRequestCommand({
          namespace: responseRequest?.namespace ?? null,
          systemName: responseRequest?.system ?? null,
          version: responseRequest?.system_version ?? null,
          instance: responseRequest?.instance_name ?? null,
          command: responseRequest?.command ?? null,
        });
      });
    }
    GetSystemList()
      .then((data) => {
        setSystems(data);
      })
      .catch((error) => {
        console.error("Error fetching system list:", error);
      });
  }, []);

  return (
    <div className="card flex justify-content-center">
      <ConfirmDialog />
      <Stepper
        ref={stepperRef}
        onChangeStep={(e) => indexCheck(e.index)}
        style={{ flexBasis: "50rem" }}
      >
        <StepperPanel header={scheduleHeader}>
          <div className="flex flex-column h-12rem">
            <div className="border-2 border-dashed surface-border border-round surface-ground flex-auto flex justify-content-center align-items-center font-medium">
              Content I
            </div>
          </div>
          <div className="flex pt-4 justify-content-end">
            <Button
              label="Next"
              icon="pi pi-arrow-right"
              iconPos="right"
              onClick={() => nextStep(selectCommandHeader)}
            />
          </div>
        </StepperPanel>
        <StepperPanel header={selectCommandHeader}>
          <div className="flex flex-column h-12rem">
            <CommandSelect
              systems={systems}
              requestCommand={requestCommand}
              setRequestCommand={setRequestCommand}
            />
          </div>

          <div className="flex pt-4 justify-content-between">
            <Button
              label="Back"
              severity="secondary"
              icon="pi pi-arrow-left"
              onClick={() => prevStep(scheduleHeader)}
            />
            <Button
              label="Next"
              icon="pi pi-arrow-right"
              iconPos="right"
              onClick={() => nextStep(createRequestHeader)}
            />
          </div>
        </StepperPanel>
        <StepperPanel header={createRequestHeader}>
          <div className="flex flex-column h-12rem">
            <div className="border-2 border-dashed surface-border border-round surface-ground flex-auto flex justify-content-center align-items-center font-medium">
              {showCommand && (
                <CommandForm
                  command={command}
                  disabled={false}
                  request={request}
                />
              )}
              {!showCommand && (
                <Skeleton width="100%" height="150px"></Skeleton>
              )}
            </div>
          </div>

          <div className="flex pt-4 justify-content-between">
            <Button
              label="Back"
              severity="secondary"
              icon="pi pi-arrow-left"
              onClick={() => prevStep(selectCommandHeader)}
            />
            <Button
              label="Submit"
              severity="success"
              icon="pi pi-arrow-right"
              iconPos="right"
              onClick={submitRequest}
            />
          </div>
        </StepperPanel>
      </Stepper>
    </div>
  );
}

export default RequestCreate;
