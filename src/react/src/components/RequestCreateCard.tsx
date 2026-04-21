import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "primereact/button";
import { Card } from "primereact/card";
import { InputSwitch } from "primereact/inputswitch";
import { Skeleton } from "primereact/skeleton";
import { useEffect, useState } from "react";

import HasAccess from "../components/HasAccess";
import { Job, Request } from "../models/brewtils-types";
import { Config, RequestCommand, RequestItem } from "../models/models";
import { CreateJob, GetJob, UpdateJob } from "../services/job_service";
import { GetRequest } from "../services/request_service";
import { PostRequest } from "../services/request_service";
import { GetBaseURL } from "../services/util_service";
import CodeExample from "./CodeExample";
import CommandCreate from "./CommandCreate";
import SchedulerForm from "./SchedulerForm";

function RequestCreateCard({
  requestItem,
  updateRequestItem,
  removeItem,
  config,
}: {
  requestItem: RequestItem;
  updateRequestItem: (item: RequestItem) => void;
  removeItem: (id: string) => void;
  config: Config;
}) {
  // Input Request
  const [request, setRequest] = useState<Request | undefined>(
    requestItem?.request ?? undefined,
  );
  const updateRequestValue = (requestValue: Request | undefined) => {
    setRequest(requestValue);
    updateRequestItem({
      ...requestItem,
      request: requestValue,
    });
  };

  // Job Panel
  const [job, setJob] = useState<Job | undefined>(
    requestItem?.job ?? undefined,
  );

  const updateJobValue = (jobValue: Job | undefined) => {
    setJob(jobValue);
    updateRequestItem({
      ...requestItem,
      job: jobValue,
    });
  };

  // Create Request Panel
  const [requestCommand, setRequestCommand] = useState<RequestCommand>(
    requestItem?.requestCommandInput ?? {
      namespace: undefined,
      systemName: undefined,
      version: undefined,
      instance: undefined,
      command: undefined,
    },
  );
  const updateRequestCommand = (requestCommand: RequestCommand) => {
    setRequestCommand(requestCommand);
    updateRequestItem({
      ...requestItem,
      requestCommandInput: requestCommand,
    });
  };

  const [showScheduleJob, setShowScheduleJob] = useState(
    requestItem?.showSchedule ||
      (requestItem?.jobId !== undefined && requestItem?.jobId !== null),
  );
  const updateShowScheduleJob = (showSchedule: boolean) => {
    setShowScheduleJob(showSchedule);

    updateRequestItem({
      ...requestItem,
      showSchedule: showSchedule,
    });
  };

  const [visibleCodeExample, setVisibleCodeExample] = useState<boolean>(false);
  const [resetForm, setResetForm] = useState<boolean>(false);

  const [showCreateRequest, setShowCreateRequest] = useState<boolean>(
    (requestItem?.requestId === undefined || requestItem?.requestId === null) &&
      (requestItem?.jobId === undefined || requestItem?.jobId === null),
  );

  const submitRequest = () => {
    if (request) {
      PostRequest(request)
        .then((response_request) => {
          updateRequestItem({
            ...requestItem,
            ...{
              request: response_request,
              requestId: response_request.id,
              type: "VIEW_REQUEST",
            },
          });
        })
        .catch((error) => {
          console.error("Error creating request:", error);
        });
    }
  };

  const submitRequestAndOpen = () => {
    if (request) {
      PostRequest(request)
        .then((response_request) => {
          window.open(
            `${GetBaseURL()}/request/${response_request.id}`,
            "_blank",
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
        .then((createdJob) => {
          updateRequestItem({
            ...requestItem,
            ...{
              job: createdJob,
              jobId: createdJob.id,
              type: "VIEW_JOB",
            },
          });
        })
        .catch((error) => {
          console.error("Error creating job:", error);
        });
    }
  };

  const updateJob = () => {
    if (job && request) {
      UpdateJob({ ...job, ...{ request_template: request } })
        .then((updatedJob) => {
          updateRequestItem({
            ...requestItem,
            ...{
              job: updatedJob,
              jobId: updatedJob.id,
              type: "VIEW_JOB",
            },
          });
        })
        .catch((error) => {
          console.error("Error updating job:", error);
        });
    }
  };

  useEffect(() => {
    if (
      requestItem?.requestId !== null &&
      requestItem?.requestId !== undefined &&
      requestItem?.request === undefined
    ) {
      GetRequest(requestItem.requestId, {})
        .then((responseRequest) => {
          updateRequestValue({
            namespace: responseRequest.namespace,
            system: responseRequest.system,
            system_version: responseRequest.system_version,
            instance_name: responseRequest.instance_name,
            command: responseRequest.command,
            parameters: responseRequest.parameters,
          });
          updateRequestCommand({
            namespace: responseRequest?.namespace ?? undefined,
            systemName: responseRequest?.system ?? undefined,
            version: responseRequest?.system_version ?? undefined,
            instance: responseRequest?.instance_name ?? undefined,
            command: responseRequest?.command ?? undefined,
          });
          setShowCreateRequest(true);
        })
        .catch((error) => {
          console.error("Error fetching request:", error);
        });
    } else if (
      requestItem?.jobId !== null &&
      requestItem?.jobId !== undefined &&
      requestItem?.job === undefined
    ) {
      GetJob(requestItem.jobId, {})
        .then((responseJob) => {
          updateJobValue(responseJob);
          updateRequestCommand({
            namespace: responseJob?.request_template?.namespace ?? undefined,
            systemName: responseJob?.request_template?.system ?? undefined,
            version: responseJob?.request_template?.system_version ?? undefined,
            instance: responseJob?.request_template?.instance_name ?? undefined,
            command: responseJob?.request_template?.command ?? undefined,
          });
          setShowCreateRequest(true);
        })
        .catch((error) => {
          console.error("Error fetching job:", error);
        });
    } else {
      setShowCreateRequest(true);
    }
  }, []);

  return (
    <Card
      className="justify-content-center"
      header={
        <div className="flex">
          <Button
            onClick={() => {
              removeItem(requestItem.itemId);
            }}
            tooltip={`Close Request Creation for ${request?.command_display_name ?? request?.command ?? "Unknown Request"}`}
          >
            <FontAwesomeIcon icon="xmark" />
          </Button>
          <div className="ml-4 mr-2 align-self-center">Scheduled</div>
          <InputSwitch
            checked={showScheduleJob}
            onChange={(e) => updateShowScheduleJob(e.value)}
            className="align-self-center"
          />
        </div>
      }
      key={requestItem.itemId}
      footer={
        <div className="flex">
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
              hasGardenName={request?.target_garden}
              hasNamespace={request?.namespace}
              hasSystemName={request?.system}
              hasInstanceName={request?.instance_name}
              hasSystemVersion={request?.system_version}
              hasCommandName={request?.command}
            >
              {showCreateRequest && !showScheduleJob && (
                <Button
                  label="Submit"
                  icon="pi pi-arrow-right"
                  onMouseDown={(event) => {
                    if (event.button === 1) {
                      // Middle mouse button click
                      submitRequestAndOpen();
                    } else {
                      submitRequest();
                    }
                  }}
                />
              )}
              {showCreateRequest && showScheduleJob && !requestItem?.jobId && (
                <Button
                  label="Submit Job"
                  severity="success"
                  icon="pi pi-arrow-right"
                  iconPos="right"
                  onClick={submitJob}
                />
              )}
              {showCreateRequest && showScheduleJob && requestItem?.jobId && (
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
      }
    >
      <div>
        <div className="flex pt-4 justify-content-between">
          <div className="flex-column" style={{ width: "100%" }}>
            {showScheduleJob && (
              <SchedulerForm
                scheduledJob={job}
                setScheduledJob={updateJobValue}
              />
            )}
            {showCreateRequest && (
              <CommandCreate
                request={request}
                setRequest={updateRequestValue}
                requestCommand={requestCommand}
                setRequestCommand={updateRequestCommand}
                resetForm={resetForm}
                setResetForm={setResetForm}
              />
            )}
            {!showCreateRequest && (
              <Skeleton width="100%" height="150px"></Skeleton>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}

export default RequestCreateCard;
