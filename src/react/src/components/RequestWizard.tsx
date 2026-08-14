import {
  Box,
  Breadcrumbs,
  Card,
  CardContent,
  Skeleton,
  Step,
  StepButton,
  Stepper,
  Switch,
  Typography,
} from "@mui/material";
import { grey } from "@mui/material/colors";
import { useEffect, useState } from "react";

import {
  Command,
  Instance,
  Job,
  Request,
  System,
} from "../models/brewtils-types";
import { Config, RequestCommand, RequestItem } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import { CreateJob, GetJob, UpdateJob } from "../services/job_service";
import { GetRequest } from "../services/request_service";
import { PostRequest } from "../services/request_service";
import { GetSystemList } from "../services/system_service";
import { FAIcon, GetBaseURL } from "../services/util_service";
import AccessButton from "./AccessButton";
import CodeExample from "./CodeExample";
import CommandForm from "./CommandForm";
import CommandList from "./CommandList";
import SchedulerForm from "./SchedulerForm";
import SystemList from "./SystemList";

function RequestWizard({
  requestItem,
  updateRequestItem,
  config,
}: {
  requestItem: RequestItem;
  updateRequestItem: (item: RequestItem) => void;
  config: Config;
}) {
  const showSnackbar = useSnackbar();
  const [activeIndex, setActiveIndex] = useState(0);

  const [selectedSystem, setSelectedSystem] = useState<System | undefined>(
    undefined,
  );
  const [selectedInstance, setSelectedInstance] = useState<
    Record<string, any> | undefined
  >(undefined);
  const [selectedCommand, setSelectedCommand] = useState<Command | undefined>(
    undefined,
  );
  const [instances, setInstances] = useState<Array<Instance>>();
  const instanceList: Array<any> = [];
  const [resetForm, setResetForm] = useState<boolean>(false);
  const [isFormValid, setIsFormValid] = useState<boolean>(false);
  const [isJobValid, setIsJobValid] = useState<boolean>(false);
  const [visibleCodeExample, setVisibleCodeExample] = useState<boolean>(false);

  const [showCreateRequest, setShowCreateRequest] = useState<boolean>(
    (requestItem?.requestId === undefined || requestItem?.requestId === null) &&
      (requestItem?.jobId === undefined || requestItem?.jobId === null),
  );

  const [showScheduleJob, setShowScheduleJob] = useState<boolean>(
    (requestItem?.jobId === undefined || requestItem?.jobId === null) &&
      requestItem?.job === undefined,
  );

  const [showStepper, setShowStepper] = useState<boolean>(false);

  // Input Request
  const [request, setRequest] = useState<Request | undefined>(
    requestItem?.request ??
      (requestItem.requestCommandInput
        ? {
            system: requestItem.requestCommandInput?.systemName,
            system_version: requestItem.requestCommandInput?.version,
            namespace: requestItem.requestCommandInput?.namespace,
            instance_name: requestItem.requestCommandInput?.instance,
            command: requestItem.requestCommandInput?.command,
          }
        : undefined),
  );

  const updateRequestValue = (requestValue: Request | undefined) => {
    setRequest(requestValue);
    updateRequestItem({
      ...requestItem,
      request: requestValue,
      requestCommandInput: {
        namespace: requestValue?.namespace,
        systemName: requestValue?.system,
        version: requestValue?.system_version,
        instance: requestValue?.instance_name,
        command: requestValue?.command,
      },
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
            detail: `Error creating request: ${error}`,
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

  // Create Request Panel
  const updateRequestCommand = (requestCommand: RequestCommand) => {
    updateRequestItem({
      ...requestItem,
      requestCommandInput: requestCommand,
    });
  };

  const findSelectedSystem = (
    namespace?: string,
    system?: string,
    system_version?: string,
    instance_name?: string,
    command?: string,
    command_display_name?: string,
  ) => {
    GetSystemList()
      .then((responseSystems) => {
        const chosenSystem = responseSystems.find(
          (s) =>
            s.namespace == namespace &&
            s.name == system &&
            s.version == system_version,
        );
        setSelectedSystem(chosenSystem);
        updateRequestValue({
          ...request,
          namespace: namespace,
          system: system,
          system_version: system_version,
          instance_name: instance_name,
          command: command,
          target_garden: chosenSystem?.garden_name,
          source_garden: config.garden_name,
        });
        if (instance_name) {
          if (chosenSystem?.instances?.find((i) => i.name == instance_name)) {
            setSelectedInstance({
              name: instance_name,
              label: instance_name,
            });
          }

          if (command || command_display_name) {
            setSelectedCommand(
              chosenSystem?.commands?.find(
                (c) =>
                  (command && c.name == command) ||
                  (command_display_name &&
                    c.display_name == command_display_name),
              ),
            );
            setActiveIndex(2);
            setShowCreateRequest(true);
          } else {
            setActiveIndex(1);
          }
        } else {
          setActiveIndex(0);
        }
        setShowStepper(true);
      })
      .catch((error) => {
        console.error("Error fetching systems:", error);
        showSnackbar({
          severity: "error",
          summary: "Error",
          detail: `Error fetching systems: ${error}`,
          life: 3000,
        });
      });
  };

  const updateSelectedInstance = (instance: Record<string, any>) => {
    setSelectedInstance(instance);
    updateRequestValue({
      ...request,
      instance_name: instance?.name,
    });
  };

  useEffect(() => {
    if (selectedSystem) {
      updateRequestValue({
        ...request,
        namespace: selectedSystem?.namespace,
        system: selectedSystem?.name,
        system_version: selectedSystem?.version,
      });
      if (selectedSystem.instances) {
        selectedSystem.instances.forEach((instance: Instance) => {
          if (instance.name && !instanceList.includes(instance)) {
            instanceList.push(instance);
          }
        });
        setInstances(instanceList);
      }
      if (selectedSystem?.instances?.length == 1) {
        setSelectedInstance({
          name: selectedSystem?.instances[0].name,
          label: selectedSystem?.instances[0].name,
        });
      }
    }
  }, [selectedSystem]);

  useEffect(() => {
    if (selectedInstance) {
      updateRequestValue({
        ...request,
        instance_name: selectedInstance?.name,
      });
    }
  }, [selectedInstance, setSelectedInstance]);

  useEffect(() => {
    if (
      requestItem?.requestId !== null &&
      requestItem?.requestId !== undefined &&
      requestItem?.request === undefined
    ) {
      GetRequest(requestItem.requestId, {})
        .then((responseRequest) => {
          findSelectedSystem(
            responseRequest.namespace,
            responseRequest.system,
            responseRequest.system_version,
            responseRequest.instance_name,
            responseRequest.command,
            responseRequest.command_display_name,
          );

          updateRequestValue({
            ...request,
            namespace: responseRequest.namespace,
            system: responseRequest.system,
            system_version: responseRequest.system_version,
            instance_name: responseRequest.instance_name,
            command_display_name: responseRequest.command_display_name,
            command: responseRequest.command,
            parameters: responseRequest.parameters,
            command_type: responseRequest.command_type,
            comment:
              responseRequest.comment !== null
                ? responseRequest.comment
                : undefined,
          });
          updateRequestCommand({
            namespace: responseRequest?.namespace ?? undefined,
            systemName: responseRequest?.system ?? undefined,
            version: responseRequest?.system_version ?? undefined,
            instance: responseRequest?.instance_name ?? undefined,
            command: responseRequest?.command ?? undefined,
          });
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
          findSelectedSystem(
            responseJob.request_template?.namespace,
            responseJob.request_template?.system,
            responseJob.request_template?.system_version,
            responseJob.request_template?.instance_name,
            responseJob.request_template?.command,
            responseJob.request_template?.command_display_name,
          );

          updateJobValue(responseJob);
          updateRequestValue({
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
          updateRequestCommand({
            namespace: responseJob?.request_template?.namespace ?? undefined,
            systemName: responseJob?.request_template?.system ?? undefined,
            version: responseJob?.request_template?.system_version ?? undefined,
            instance: responseJob?.request_template?.instance_name ?? undefined,
            command: responseJob?.request_template?.command ?? undefined,
          });
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
    } else if (
      requestItem?.job !== undefined &&
      requestItem.job?.request_template !== undefined
    ) {
      const job = requestItem.job;
      findSelectedSystem(
        job.request_template?.namespace,
        job.request_template?.system,
        job.request_template?.system_version,
        job.request_template?.instance_name,
        job.request_template?.command,
        job.request_template?.command_display_name,
      );
      updateJobValue(job);
      updateRequestValue({
        ...request,
        namespace: job.request_template?.namespace,
        system: job.request_template?.system,
        system_version: job.request_template?.system_version,
        instance_name: job.request_template?.instance_name,
        command: job.request_template?.command,
        parameters: job.request_template?.parameters,
        command_type: job.request_template?.command_type,
        comment: job.request_template?.comment,
      });
      updateRequestCommand({
        namespace: job.request_template?.namespace ?? undefined,
        systemName: job.request_template?.system ?? undefined,
        version: job.request_template?.system_version ?? undefined,
        instance: job.request_template?.instance_name ?? undefined,
        command: job.request_template?.command ?? undefined,
      });
    } else if (requestItem?.requestCommandInput !== undefined) {
      findSelectedSystem(
        requestItem.requestCommandInput.namespace,
        requestItem.requestCommandInput.systemName,
        requestItem.requestCommandInput.version,
        requestItem.requestCommandInput.instance,
        requestItem.requestCommandInput.command,
      );
    } else if (requestItem?.request !== undefined) {
      findSelectedSystem(
        requestItem.request.namespace,
        requestItem.request.system,
        requestItem.request.system_version,
        requestItem.request.instance_name,
        requestItem.request.command,
      );
      updateRequestCommand({
        namespace: requestItem.request?.namespace ?? undefined,
        systemName: requestItem.request?.system ?? undefined,
        version: requestItem.request?.system_version ?? undefined,
        instance: requestItem.request?.instance_name ?? undefined,
        command: requestItem.request?.command ?? undefined,
      });
    } else {
      setActiveIndex(0);
      setShowStepper(true);
    }
  }, []);

  const breadcrumbStyles = {
    p: 2,
    border: "1px solid",
    borderColor: grey[300],
    borderRadius: 2,
    mb: 2,
  };

  const steps = ["Pick System", "Pick command", "Form"];

  const handleStep = (step: number) => () => {
    setActiveIndex(step);
  };

  const systemListButtonClick = (system: System) => {
    setSelectedSystem(system);
    updateRequestValue({
      ...request,
      target_garden: selectedSystem?.garden_name,
      source_garden: config.garden_name,
    });
    setActiveIndex((index) => index + 1);
  };

  const commandListButtonClick = (command: Command) => {
    setSelectedCommand(command);
    updateRequestValue({
      ...request,
      command: command?.name,
    });
    setActiveIndex((index) => index + 1);
  };

  const iconItemTemplate = (item: any) => {
    if (item.icon) {
      return (
        <span>
          <FAIcon icon={item.icon} />
        </span>
      );
    }
    return <span>{item.label}</span>;
  };

  const breadcrumbs = [
    {
      icon: "file-lines",
      template: iconItemTemplate,
    },
    {
      label: selectedSystem?.namespace,
      template: iconItemTemplate,
    },
    {
      label: selectedSystem?.name,
      template: iconItemTemplate,
    },
    {
      label: selectedSystem?.version,
      template: iconItemTemplate,
    },
  ];

  const commandBreadcrumbs = [
    {
      icon: "file-lines",
      template: iconItemTemplate,
    },
    {
      label: selectedSystem?.namespace,
      template: iconItemTemplate,
    },
    {
      label: selectedSystem?.name,
      template: iconItemTemplate,
    },
    {
      label: selectedSystem?.version,
      template: iconItemTemplate,
    },
    {
      label: selectedInstance?.name,
      template: iconItemTemplate,
    },
    {
      label: selectedCommand?.name,
      template: iconItemTemplate,
    },
  ];

  const cleanForm = () => {
    const newRequest = { ...request, command_type: "" };
    delete newRequest.parameters;
    delete newRequest.comment;
    updateRequestValue(newRequest);
  };

  const getStepperPanel = () => {
    if (activeIndex == 0) {
      return <SystemList systemListButtonClick={systemListButtonClick} />;
    }
    if (activeIndex == 1) {
      return (
        <>
          <Box sx={breadcrumbStyles}>
            <Breadcrumbs
              separator={<FAIcon icon="angle-right" />}
              aria-label="breadcrumb"
              aria-description="Breadcrumb navigation for system and instance selection steps of request creation."
            >
              {breadcrumbs.map((item) => (
                <span>{item.template(item)}</span>
              ))}
            </Breadcrumbs>
          </Box>
          <CommandList
            selectedSystem={selectedSystem}
            commandListButtonClick={commandListButtonClick}
            instances={
              instances
                ? instances.map((instance) => ({
                    name: instance.name,
                    label: instance.name,
                  }))
                : []
            }
            selectedInstance={selectedInstance}
            setSelectedInstance={updateSelectedInstance}
          />
          <Box sx={{ display: "flex", pt: 4, justifyContent: "space-between" }}>
            <AccessButton
              label="Back"
              color="secondary"
              onClick={() => {
                setSelectedInstance(undefined);
                setActiveIndex((index) => index - 1);
              }}
            >
              Back
            </AccessButton>
          </Box>
        </>
      );
    }
    if (activeIndex == 2) {
      return (
        <>
          <Box sx={breadcrumbStyles}>
            <Breadcrumbs
              separator={<FAIcon icon="angle-right" />}
              aria-label="breadcrumb"
              aria-description="Breadcrumb navigation for command selection step of request creation."
            >
              {commandBreadcrumbs.map((item) => (
                <span>{item.template(item)}</span>
              ))}
            </Breadcrumbs>
          </Box>
          <Box sx={{ display: "flex", ml: 4 }}>
            <Typography sx={{ mr: 2, alignSelf: "center" }}>
              Scheduled
            </Typography>
            <Switch
              aria-label="Toggle for creating Scheduled Job"
              checked={toggleScheduleJob}
              onChange={(e) => updateToggleScheduleJob(e.target.checked)}
            />
          </Box>
          {showScheduleJob && (
            <SchedulerForm
              scheduledJob={job}
              setScheduledJob={updateJobValue}
              setIsJobValid={setIsJobValid}
            />
          )}
          <CommandForm
            command={selectedCommand}
            disabled={false}
            request={request}
            setRequest={updateRequestValue}
            resetForm={resetForm}
            setResetForm={setResetForm}
            setIsFormValid={setIsFormValid}
          />
          <Box sx={{ display: "flex", pt: 4, justifyContent: "space-between" }}>
            <AccessButton
              label="Back"
              color="secondary"
              onClick={() => {
                cleanForm();
                setActiveIndex((index) => index - 1);
              }}
            >
              Back
            </AccessButton>
            <AccessButton
              label="Reset Form"
              color="warning"
              onClick={() => setResetForm(true)}
              sx={{ ml: 2 }}
            >
              Reset Form
            </AccessButton>
            <Box>
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
                Code Examples
              </AccessButton>
            </Box>
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
                config={config}
                permission="OPERATOR"
                hasNamespace={requestItem.requestCommandInput?.namespace}
                hasSystemName={requestItem.requestCommandInput?.systemName}
                hasSystemVersion={requestItem.requestCommandInput?.version}
                hasInstanceName={requestItem.requestCommandInput?.instance}
                hasCommandName={requestItem.requestCommandInput?.command}
              >
                Submit
                <FAIcon icon="arrow-right" sx={{ ml: 2 }} />
              </AccessButton>
            )}
            {showCreateRequest && showScheduleJob && !requestItem?.jobId && (
              <AccessButton
                label="Submit Job"
                color="success"
                disabled={!(isJobValid && isFormValid)}
                onClick={submitJob}
                config={config}
                permission="OPERATOR"
                hasNamespace={requestItem.requestCommandInput?.namespace}
                hasSystemName={requestItem.requestCommandInput?.systemName}
                hasSystemVersion={requestItem.requestCommandInput?.version}
                hasInstanceName={requestItem.requestCommandInput?.instance}
                hasCommandName={requestItem.requestCommandInput?.command}
              >
                Submit Job
                <FAIcon icon="arrow-right" sx={{ ml: 2 }} />
              </AccessButton>
            )}
            {showCreateRequest && showScheduleJob && requestItem?.jobId && (
              <AccessButton
                label="Update Job"
                color="success"
                disabled={!(isJobValid && isFormValid)}
                onClick={updateJob}
                config={config}
                permission="OPERATOR"
                hasNamespace={requestItem.requestCommandInput?.namespace}
                hasSystemName={requestItem.requestCommandInput?.systemName}
                hasSystemVersion={requestItem.requestCommandInput?.version}
                hasInstanceName={requestItem.requestCommandInput?.instance}
                hasCommandName={requestItem.requestCommandInput?.command}
              >
                Update Job
                <FAIcon icon="arrow-right" sx={{ ml: 2 }} />
              </AccessButton>
            )}
          </Box>
        </>
      );
    }
  };

  return (
    <Card sx={{ overflow: "scroll" }} key={requestItem.itemId}>
      <CardContent>
        {!showStepper && <Skeleton width="100%" height="150px"></Skeleton>}
        {showStepper && (
          <>
            <Stepper nonLinear activeStep={activeIndex} sx={{ mb: 2 }}>
              {steps.map((label, index) => (
                <Step key={label} disabled={activeIndex < index}>
                  <StepButton color="inherit" onClick={handleStep(index)}>
                    {label}
                  </StepButton>
                </Step>
              ))}
            </Stepper>
            <Box>{getStepperPanel()}</Box>
          </>
        )}
      </CardContent>
    </Card>
  );
}

export default RequestWizard;
