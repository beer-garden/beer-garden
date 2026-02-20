import { Button } from "primereact/button";
import { ConfirmDialog, confirmDialog } from "primereact/confirmdialog";
import { Skeleton } from "primereact/skeleton";
import { Stepper } from "primereact/stepper";
import { StepperPanel } from "primereact/stepperpanel";
import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";

import CommandForm from "../components/CommandForm";
import CommandSelect from "../components/CommandSelect";
import SchedulerForm from "../components/SchedulerForm";
import { Command, Job, Request, System } from "../models/brewtils-types";
import { CreateJob, GetJob, UpdateJob } from "../services/job_service";
import { GetRequest } from "../services/request_service";
import { PostRequest } from "../services/request_service";
import { GetSystemList } from "../services/system_service";

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
  const { defaultType } = useParams<{ defaultType: string }>();

  const stepperRef = useRef<null | any>(null);

  const scheduleHeader = "Schedule";
  const selectCommandHeader = "Select Command";
  const createRequestHeader = "Create Request";

  const defaultStepperStep = requestId
    ? 2
    : jobId || defaultType === "job"
      ? 0
      : 1;

  // Input Request
  const [request, setRequest] = useState<Request | null>(null);

  // Job Panel
  const [job, setJob] = useState<Job | null>(null);
  const runOptions = ["Run Now", "Schedule Job"];
  const [runState, setRunState] = useState(
    jobId || defaultType === "job" ? runOptions[1] : runOptions[0],
  );

  // System Panel
  const [requestCommand, setRequestCommand] = useState<RequestCommand | null>({
    namespace: null,
    systemName: null,
    version: null,
    instance: null,
    command: null,
  });

  const [systems, setSystems] = useState<Array<System> | null>(null);

  // Command Panel
  const [showCommand, setShowCommand] = useState<boolean>(false);
  const [command, setCommand] = useState<Command | null>(null);
  const [validCommand, setValidCommand] = useState(false);

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
  };

  const nextStep = () => {
    stepperRef.current?.nextCallback();
  };

  const prevStep = () => {
    stepperRef.current?.prevCallback();
  };

  const submitRequest = () => {
    if (request) {
      PostRequest(request)
        .then((response_request) => {
          window.open("/request/" + response_request.id, "_self");
        })
        .catch((error) => {
          console.error("Error creating request:", error);
        });
    }
  };

  const submitJob = () => {
    if (job && request) {
      CreateJob({ ...job, ...{ request_template: request } })
        .then(() => {
          window.open("/jobs/", "_self");
        })
        .catch((error) => {
          console.error("Error creating job:", error);
        });
    }
  };

  const updateJob = () => {
    if (job && request) {
      UpdateJob({ ...job, ...{ request_template: request } })
        .then(() => {
          window.open("/jobs/", "_self");
        })
        .catch((error) => {
          console.error("Error updating job:", error);
        });
    }
  };

  const indexCheck = (index: any) => {
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
        if (request === null) {
          resetRequest();
        } else {
          setShowCommand(true);
        }
      }
    }
  };

  useEffect(() => {
    if (requestId !== null && requestId !== undefined) {
      GetRequest(requestId, {})
        .then((responseRequest) => {
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
        })
        .catch((error) => {
          console.error("Error fetching request:", error);
        });
    } else if (jobId !== null && jobId !== undefined) {
      GetJob(jobId, {})
        .then((responseJob) => {
          setJob(responseJob);
          setRequestCommand({
            namespace: responseJob?.request_template?.namespace ?? null,
            systemName: responseJob?.request_template?.system ?? null,
            version: responseJob?.request_template?.system_version ?? null,
            instance: responseJob?.request_template?.instance_name ?? null,
            command: responseJob?.request_template?.command ?? null,
          });
        })
        .catch((error) => {
          console.error("Error fetching job:", error);
        });
    }

    if (!systems) {
      GetSystemList()
        .then((data) => {
          setSystems(data);
        })
        .catch((error) => {
          console.error("Error fetching system list:", error);
        });
    }
  }, [jobId, requestId, systems]);

  return (
    <div className="card flex justify-content-center">
      <ConfirmDialog />
      <Stepper
        ref={stepperRef}
        onChangeStep={(e) => indexCheck(e.index)}
        style={{ flexBasis: "50rem" }}
        linear={true}
        activeStep={defaultStepperStep}
      >
        <StepperPanel header={scheduleHeader}>
          <div className="flex pt-4 justify-content-end">
            <Button
              label="Next"
              icon="pi pi-arrow-right"
              iconPos="right"
              onClick={() => nextStep()}
            />
          </div>
          <div className="flex flex-column h-12rem">
            {(!jobId || job) && (
              <SchedulerForm
                scheduledJob={job}
                setScheduledJob={setJob}
                runOptions={runOptions}
                runState={runState}
                setRunState={setRunState}
              />
            )}
            {jobId && !job && <Skeleton width="100%" height="150px"></Skeleton>}
          </div>
        </StepperPanel>
        <StepperPanel header={selectCommandHeader}>
          <div className="flex pt-4 justify-content-between">
            <Button
              label="Back"
              severity="secondary"
              icon="pi pi-arrow-left"
              onClick={() => prevStep()}
            />
            <Button
              label="Next"
              icon="pi pi-arrow-right"
              iconPos="right"
              onClick={() => nextStep()}
              disabled={!validCommand}
            />
          </div>
          <div className="flex flex-column h-12rem">
            {systems && systems.length > 0 && (
              <CommandSelect
                systems={systems}
                requestCommand={requestCommand}
                setRequestCommand={setRequestCommand}
                validCommand={validCommand}
                setValidCommand={setValidCommand}
              />
            )}
            {(!systems || systems.length === 0) && (
              <Skeleton width="100%" height="150px"></Skeleton>
            )}
          </div>
        </StepperPanel>
        <StepperPanel header={createRequestHeader}>
          <div className="flex pt-4 justify-content-between">
            <Button
              label="Back"
              severity="secondary"
              icon="pi pi-arrow-left"
              onClick={() => prevStep()}
            />
            {runState === runOptions[0] && (
              <Button
                label="Submit"
                severity="success"
                icon="pi pi-arrow-right"
                iconPos="right"
                onClick={submitRequest}
              />
            )}
            {runState === runOptions[1] && !jobId && (
              <Button
                label="Submit Job"
                severity="success"
                icon="pi pi-arrow-right"
                iconPos="right"
                onClick={submitJob}
              />
            )}
            {runState === runOptions[1] && jobId && (
              <Button
                label="Update Job"
                severity="success"
                icon="pi pi-arrow-right"
                iconPos="right"
                onClick={updateJob}
              />
            )}
          </div>
          <div className="flex flex-column h-12rem">
            <div className="border-2 border-dashed surface-border border-round surface-ground flex-auto flex justify-content-center align-items-center font-medium">
              {showCommand && (
                <CommandForm
                  command={command}
                  disabled={false}
                  request={request}
                  setRequest={setRequest}
                />
              )}
              {!showCommand && (
                <Skeleton width="100%" height="150px"></Skeleton>
              )}
            </div>
          </div>
        </StepperPanel>
      </Stepper>
    </div>
  );
}

export default RequestCreate;
