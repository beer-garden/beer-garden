import { Button } from "primereact/button";
import { Skeleton } from "primereact/skeleton";
import { Stepper } from "primereact/stepper";
import { StepperPanel } from "primereact/stepperpanel";
import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import CommandCreate from "../components/CommandCreate";
import HasAccess from "../components/HasAccess";
import SchedulerForm from "../components/SchedulerForm";
import { Job, Request } from "../models/brewtils-types";
import { Config, RequestCommand } from "../models/models";
import { CreateJob, GetJob, UpdateJob } from "../services/job_service";
import { GetRequest } from "../services/request_service";
import { PostRequest } from "../services/request_service";
import { GetBaseURL } from "../services/util_service";

function RequestCreate({ config }: { config: Config }) {
  const { requestId } = useParams<{ requestId: string }>();
  const { jobId } = useParams<{ jobId: string }>();
  const { defaultType } = useParams<{ defaultType: string }>();
  const { paramNamespace } = useParams<{ paramNamespace: string }>();
  const { paramSystem } = useParams<{ paramSystem: string }>();
  const { paramVersion } = useParams<{ paramVersion: string }>();
  const { paramInstance } = useParams<{ paramInstance: string }>();
  const { paramCommand } = useParams<{ paramCommand: string }>();
  const stepperRef = useRef<null | any>(null);
  const navigate = useNavigate();

  const scheduleHeader = "Schedule";
  const createRequestHeader = "Create Request";

  const defaultStepperStep = jobId || defaultType === "job" ? 0 : 1;

  // Input Request
  const [request, setRequest] = useState<Request | undefined>(undefined);

  // Job Panel
  const [job, setJob] = useState<Job | null>(null);
  const runOptions = ["Run Now", "Schedule Job"];
  const [runState, setRunState] = useState(
    jobId || defaultType === "job" ? runOptions[1] : runOptions[0],
  );

  // Create Request Panel
  const [requestCommand, setRequestCommand] = useState<RequestCommand>({
    namespace: paramNamespace ?? undefined,
    systemName: paramSystem ?? undefined,
    version: paramVersion ?? undefined,
    instance: paramInstance ?? undefined,
    command: paramCommand ?? undefined,
  });

  const [showCreateRequest, setShowCreateRequest] = useState<boolean>(
    (requestId === undefined || requestId === null) &&
      (jobId === undefined || jobId === null),
  );

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
          void navigate(`${GetBaseURL()}/request/${response_request.id}`);
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
          void navigate(`${GetBaseURL()}/jobs/`);
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
          void navigate(`${GetBaseURL()}/jobs/`);
        })
        .catch((error) => {
          console.error("Error updating job:", error);
        });
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
            namespace: responseRequest?.namespace,
            systemName: responseRequest?.system,
            version: responseRequest?.system_version,
            instance: responseRequest?.instance_name,
            command: responseRequest?.command,
          });
          setShowCreateRequest(true);
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
          setShowCreateRequest(true);
        })
        .catch((error) => {
          console.error("Error fetching job:", error);
        });
    }
  }, [jobId, requestId]);

  return (
    <div className="card flex justify-content-center">
      <Stepper
        ref={stepperRef}
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
        <StepperPanel header={createRequestHeader}>
          <div className="flex pt-4 justify-content-between">
            <Button
              label="Back"
              severity="secondary"
              icon="pi pi-arrow-left"
              onClick={() => prevStep()}
            />

            {runState === runOptions[0] && (
              <div>
                <HasAccess
                  config={config}
                  permission="OPERATOR"
                  hasNamespace={requestCommand.namespace}
                  hasSystemName={requestCommand.systemName}
                  hasInstanceName={requestCommand.instance}
                  hasSystemVersion={requestCommand.version}
                  hasCommandName={requestCommand.command}
                >
                  <Button
                    label="Submit"
                    icon="pi pi-arrow-right"
                    onClick={() => {
                      submitRequest();
                    }}
                  />
                </HasAccess>
              </div>
            )}
            {runState === runOptions[1] && !jobId && (
              <HasAccess
                config={config}
                permission="OPERATOR"
                hasNamespace={requestCommand.namespace}
                hasSystemName={requestCommand.systemName}
                hasInstanceName={requestCommand.instance}
                hasSystemVersion={requestCommand.version}
                hasCommandName={requestCommand.command}
              >
                <Button
                  label="Submit Job"
                  severity="success"
                  icon="pi pi-arrow-right"
                  iconPos="right"
                  onClick={submitJob}
                />
              </HasAccess>
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
            {showCreateRequest && (
              <CommandCreate
                request={request}
                setRequest={setRequest}
                requestCommand={requestCommand}
                setRequestCommand={setRequestCommand}
              />
            )}
            {!showCreateRequest && (
              <Skeleton width="100%" height="150px"></Skeleton>
            )}
          </div>
        </StepperPanel>
      </Stepper>
    </div>
  );
}

export default RequestCreate;
