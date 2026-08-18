import { DialogActions, DialogContent, Grid } from "@mui/material";
import Box from "@mui/material/Box";
import Container from "@mui/material/Container";
import Skeleton from "@mui/material/Skeleton";
import Switch from "@mui/material/Switch";
import Typography from "@mui/material/Typography";
import { useEffect, useState } from "react";

import { Job, Request } from "../models/brewtils-types";
import { Config, RequestCommand, RequestItem } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import { CreateJob, GetJob, UpdateJob } from "../services/job_service";
import { GetRequest } from "../services/request_service";
import { PostRequest } from "../services/request_service";
import { GetBaseURL } from "../services/util_service";
import { FAIcon } from "../services/util_service";
import AccessButton from "./AccessButton";
import CodeExample from "./CodeExample";
import CommandCreate from "./CommandCreate";
import SchedulerForm from "./SchedulerForm";

function RequestCreateCard({
  requestItem,
  updateRequestItem,
  config,
}: {
  requestItem: RequestItem;
  updateRequestItem: (item: RequestItem) => void;
  config: Config;
}) {
  const showSnackbar = useSnackbar();
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

  const [toggleScheduleJob, setToggleScheduleJob] = useState(
    requestItem?.showSchedule ||
      (requestItem?.jobId !== undefined && requestItem?.jobId !== null),
  );
  const updateToggleScheduleJob = (showSchedule: boolean) => {
    setToggleScheduleJob(showSchedule);
    setShowScheduleJob(showSchedule);
    setJob(showSchedule ? {} : undefined);
    updateRequestItem({
      ...requestItem,
      showSchedule: showSchedule,
      job: showSchedule ? {} : undefined,
    });
  };

  const [visibleCodeExample, setVisibleCodeExample] = useState<boolean>(false);
  const [resetForm, setResetForm] = useState<boolean>(false);
  const [isFormValid, setIsFormValid] = useState<boolean>(false);
  const [isJobValid, setIsJobValid] = useState<boolean>(false);

  const [showCreateRequest, setShowCreateRequest] = useState<boolean>(
    (requestItem?.requestId === undefined || requestItem?.requestId === null) &&
      (requestItem?.jobId === undefined || requestItem?.jobId === null),
  );

  const [showScheduleJob, setShowScheduleJob] = useState<boolean>(false);

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
          showSnackbar({
            severity: "error",
            summary: "Error",
            detail: `Error creating request: ${error}`,
            life: 3000,
          });
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
          showSnackbar({
            severity: "error",
            summary: "Error",
            detail: `Error creating request: ${error}`,
            life: 3000,
          });
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
          showSnackbar({
            severity: "error",
            summary: "Error",
            detail: `Error creating job: ${error}`,
            life: 3000,
          });
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
          showSnackbar({
            severity: "error",
            summary: "Error",
            detail: `Error updating job: ${error}`,
            life: 3000,
          });
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
            command_type: responseRequest.command_type,
            comment: responseRequest.comment,
          });
          updateRequestCommand({
            namespace: responseRequest?.namespace ?? undefined,
            systemName: responseRequest?.system ?? undefined,
            version: responseRequest?.system_version ?? undefined,
            instance: responseRequest?.instance_name ?? undefined,
            command: responseRequest?.command ?? undefined,
          });
          setShowCreateRequest(true);
          setShowScheduleJob(true);
        })
        .catch((error) => {
          console.error("Error fetching request:", error);
          showSnackbar({
            severity: "error",
            summary: "Error",
            detail: `Error fetching request: ${error}`,
            life: 3000,
          });
        });
    } else if (
      requestItem?.jobId !== null &&
      requestItem?.jobId !== undefined &&
      requestItem?.job === undefined
    ) {
      GetJob(requestItem.jobId, {})
        .then((responseJob) => {
          updateJobValue(responseJob);
          setRequest({
            ...request,
            namespace: responseJob?.request_template?.namespace,
            system: responseJob?.request_template?.system,
            system_version: responseJob?.request_template?.system_version,
            instance_name: responseJob?.request_template?.instance_name,
            command: responseJob?.request_template?.command,
            parameters: responseJob?.request_template?.parameters,
            command_type: responseJob?.request_template?.command_type,
            comment: responseJob?.request_template?.comment,
          });
          updateRequestValue({
            namespace: responseJob?.request_template?.namespace,
            system: responseJob?.request_template?.system,
            system_version: responseJob?.request_template?.system_version,
            instance_name: responseJob?.request_template?.instance_name,
            command: responseJob?.request_template?.command,
            parameters: responseJob?.request_template?.parameters,
            command_type: responseJob?.request_template?.command_type,
            comment: responseJob?.request_template?.comment,
          });
          updateRequestCommand({
            namespace: responseJob?.request_template?.namespace ?? undefined,
            systemName: responseJob?.request_template?.system ?? undefined,
            version: responseJob?.request_template?.system_version ?? undefined,
            instance: responseJob?.request_template?.instance_name ?? undefined,
            command: responseJob?.request_template?.command ?? undefined,
          });
          setShowCreateRequest(true);
          setShowScheduleJob(true);
        })
        .catch((error) => {
          console.error("Error fetching job:", error);
          showSnackbar({
            severity: "error",
            summary: "Error",
            detail: `Error fetching job: ${error}`,
            life: 3000,
          });
        });
    } else {
      setShowCreateRequest(true);
      setShowScheduleJob(true);
    }
  }, []);

  const permissions = {
    config: config,
    hasNamespace: requestItem.requestCommandInput?.namespace,
    hasSystemName: requestItem.requestCommandInput?.systemName,
    hasSystemVersion: requestItem.requestCommandInput?.version,
    hasInstanceName: requestItem.requestCommandInput?.instance,
    hasCommandName: requestItem.requestCommandInput?.command,
  };

  return (
    <>
      <DialogContent dividers>
        <Container key={requestItem.itemId}>
          <Box
            sx={{
              display: "flex",
            }}
          >
            <Typography sx={{ ml: 4, mr: 2, alignSelf: "center" }}>
              Scheduled
            </Typography>
            <Switch
              checked={toggleScheduleJob}
              onChange={(e) => updateToggleScheduleJob(e.target.checked)}
              sx={{ alignSelf: "center" }}
              slotProps={{
                input: { "aria-label": "Toggle for creating Scheduled Job" },
              }}
            />
          </Box>

          <Box sx={{ pt: 4, width: "100%" }}>
            {toggleScheduleJob && showScheduleJob && (
              <SchedulerForm
                scheduledJob={job}
                setScheduledJob={updateJobValue}
                setIsJobValid={setIsJobValid}
              />
            )}
            {toggleScheduleJob && !showScheduleJob && (
              <Skeleton width="100%" height="150px"></Skeleton>
            )}
            {showCreateRequest && (
              <CommandCreate
                request={request}
                setRequest={updateRequestValue}
                requestCommand={requestCommand}
                setRequestCommand={updateRequestCommand}
                resetForm={resetForm}
                setResetForm={setResetForm}
                setIsFormValid={setIsFormValid}
                config={config}
              />
            )}
            {!showCreateRequest && (
              <Skeleton width="100%" height="150px"></Skeleton>
            )}
          </Box>
        </Container>
      </DialogContent>
      <DialogActions sx={{ m: 2 }}>
        <Box>
          <Grid container>
            <Grid size="grow">
              <AccessButton
                label="Reset Form"
                color="warning"
                onClick={() => setResetForm(true)}
                sx={{ mr: 2 }}
              >
                <Typography variant="button" sx={{ display: "block" }}>
                  Reset Form
                </Typography>
                <FAIcon icon="refresh" sx={{ ml: 2 }} />
              </AccessButton>

              <CodeExample
                visibleCodeExample={visibleCodeExample}
                setVisibleCodeExample={setVisibleCodeExample}
                request={request}
              />
              <AccessButton
                label="Code Examples"
                color="info"
                onClick={() => setVisibleCodeExample(true)}
                sx={{ mr: 2 }}
              >
                <Typography variant="button" sx={{ display: "block" }}>
                  Code Examples
                </Typography>
                <FAIcon icon="code" sx={{ ml: 2 }} />
              </AccessButton>
            </Grid>

            <Grid>
              {showCreateRequest && !showScheduleJob && (
                <AccessButton
                  label="Submit"
                  disabled={!isFormValid}
                  onMouseDown={(event: any) => {
                    if (event.type === "mousedown" && event.button === 1) {
                      submitRequestAndOpen();
                    }
                  }}
                  onClick={submitRequest}
                  {...permissions}
                  permission="OPERATOR"
                >
                  <Typography variant="button" sx={{ display: "block" }}>
                    Submit
                  </Typography>
                  <FAIcon icon="arrow-right-to-bracket" sx={{ ml: 2 }} />
                </AccessButton>
              )}
              {showCreateRequest && showScheduleJob && !requestItem?.jobId && (
                <AccessButton
                  label="Submit Job"
                  color="success"
                  disabled={!(isJobValid && isFormValid)}
                  onClick={submitJob}
                  {...permissions}
                  permission="OPERATOR"
                >
                  <Typography variant="button" sx={{ display: "block" }}>
                    Submit Job
                  </Typography>
                  <FAIcon icon="arrow-right-to-bracket" sx={{ ml: 2 }} />
                </AccessButton>
              )}
              {showCreateRequest && showScheduleJob && requestItem?.jobId && (
                <AccessButton
                  label="Update Job"
                  color="success"
                  disabled={!(isJobValid && isFormValid)}
                  onClick={updateJob}
                  {...permissions}
                  permission="OPERATOR"
                >
                  <Typography variant="button" sx={{ display: "block" }}>
                    Update Job
                  </Typography>
                  <FAIcon icon="arrow-right-to-bracket" sx={{ ml: 2 }} />
                </AccessButton>
              )}
            </Grid>
          </Grid>
        </Box>
      </DialogActions>
    </>
  );
}

export default RequestCreateCard;
