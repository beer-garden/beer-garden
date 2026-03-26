import { Button } from "primereact/button";
import { InputSwitch } from "primereact/inputswitch";
import { Skeleton } from "primereact/skeleton";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import CodeExample from "../components/CodeExample";
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

  const { paramNamespace } = useParams<{ paramNamespace: string }>();
  const { paramSystem } = useParams<{ paramSystem: string }>();
  const { paramVersion } = useParams<{ paramVersion: string }>();
  const { paramInstance } = useParams<{ paramInstance: string }>();
  const { paramCommand } = useParams<{ paramCommand: string }>();

  // Input Request
  const [request, setRequest] = useState<Request | undefined>(undefined);

  // Job Panel
  const [job, setJob] = useState<Job | undefined>(undefined);
  const [showScheduleJob, setShowScheduleJob] = useState(
    jobId !== undefined && jobId !== null,
  );

  // Create Request Panel
  const [requestCommand, setRequestCommand] = useState<RequestCommand>({
    namespace: paramNamespace ?? undefined,
    systemName: paramSystem ?? undefined,
    version: paramVersion ?? undefined,
    instance: paramInstance ?? undefined,
    command: paramCommand ?? undefined,
  });
  const [visibleCodeExample, setVisibleCodeExample] = useState<boolean>(false);
  const [resetForm, setResetForm] = useState<boolean>(false);

  const [showCreateRequest, setShowCreateRequest] = useState<boolean>(
    (requestId === undefined || requestId === null) &&
      (jobId === undefined || jobId === null),
  );

  const submitRequest = () => {
    if (request) {
      PostRequest(request)
        .then((response_request) => {
          window.open(
            `${GetBaseURL()}/request/${response_request.id}`,
            "_self",
          );
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
          window.open(`${GetBaseURL()}/jobs/`, "_self");
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
          window.open(`${GetBaseURL()}/jobs/`, "_self");
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
    <div className="card justify-content-center">
      <div>
        <div className="flex pt-4 justify-content-between">
          <div className="flex">
            <div className=" flex mr-2">
              <div className="mr-2">Scheduled:</div>
              <InputSwitch
                checked={showScheduleJob}
                onChange={(e) => setShowScheduleJob(e.value)}
              ></InputSwitch>
            </div>
          </div>
        </div>
      </div>
      <div className="flex flex-column h-12rem">
        {showScheduleJob && (
          <SchedulerForm scheduledJob={job} setScheduledJob={setJob} />
        )}
        {showCreateRequest && (
          <CommandCreate
            request={request}
            setRequest={setRequest}
            requestCommand={requestCommand}
            setRequestCommand={setRequestCommand}
            resetForm={resetForm}
            setResetForm={setResetForm}
          />
        )}
        {showCreateRequest && (
          <div className="flex pt-4 ">
            <div>
              <Button
                label="Reset Form"
                severity="warning"
                icon="pi pi-arrow-right"
                onClick={() => setResetForm(true)}
                className="mr-2"
              />
            </div>
            <div>
              <CodeExample
                visibleCodeExample={visibleCodeExample}
                setVisibleCodeExample={setVisibleCodeExample}
                request={request}
              />
              <Button
                label="Code Examples"
                severity="info"
                icon="pi pi-arrow-right"
                onClick={() => setVisibleCodeExample(true)}
                className="mr-2"
              />
            </div>
            <div style={{ marginLeft: "auto" }}>
              <HasAccess
                config={config}
                permission="OPERATOR"
                hasNamespace={requestCommand.namespace}
                hasSystemName={requestCommand.systemName}
                hasInstanceName={requestCommand.instance}
                hasSystemVersion={requestCommand.version}
                hasCommandName={requestCommand.command}
              >
                {!showScheduleJob && (
                  <Button
                    label="Submit"
                    icon="pi pi-arrow-right"
                    onClick={() => {
                      submitRequest();
                    }}
                  />
                )}
                {showScheduleJob && !jobId && (
                  <Button
                    label="Submit Job"
                    severity="success"
                    icon="pi pi-arrow-right"
                    iconPos="right"
                    onClick={submitJob}
                  />
                )}
                {showScheduleJob && jobId && (
                  <Button
                    label="Update Job"
                    severity="success"
                    icon="pi pi-arrow-right"
                    iconPos="right"
                    onClick={updateJob}
                  />
                )}
              </HasAccess>
            </div>
          </div>
        )}
        {!showCreateRequest && (
          <Skeleton width="100%" height="150px"></Skeleton>
        )}
      </div>
    </div>
  );
}

export default RequestCreate;
