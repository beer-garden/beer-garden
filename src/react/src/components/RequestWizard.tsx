import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { BreadCrumb } from "primereact/breadcrumb";
import { Button } from "primereact/button";
import { Card } from "primereact/card";
import { InputSwitch } from "primereact/inputswitch";
import { Stepper } from "primereact/stepper";
import { StepperPanel } from "primereact/stepperpanel";
import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";

import {
  Command,
  Instance,
  Job,
  Request,
  System,
} from "../models/brewtils-types";
import { RequestCommand, RequestItem } from "../models/models";
import { CreateJob, GetJob, UpdateJob } from "../services/job_service";
import { GetRequest } from "../services/request_service";
import { PostRequest } from "../services/request_service";
import { GetSystemList } from "../services/system_service";
import { GetBaseURL } from "../services/util_service";
import CodeExample from "./CodeExample";
import CommandForm from "./CommandForm";
import CommandList from "./CommandList";
import SchedulerForm from "./SchedulerForm";
import SystemList from "./SystemList";

function RequestWizard({
  requestItem,
  updateRequestItem,
  removeItem,
}: {
  requestItem: RequestItem;
  updateRequestItem: (item: RequestItem) => void;
  removeItem: (id: string) => void;
}) {
  const stepperRef = useRef<Stepper>(null);
  const [activeIndex, setActiveIndex] = useState(0);

  const [selectedSystem, setSelectedSystem] = useState<System | undefined>(
    undefined,
  );
  const [selectedInstance, setSelectedInstance] = useState<
    Record<string, any> | undefined
  >(undefined);
  const [selectedCommand, setSelectedCommand] = useState<Command | undefined>(
    null,
  );
  const [instances, setInstances] = useState<Array<Instance>>();
  const instanceList: Array<any> = [];
  const [resetForm, setResetForm] = useState<boolean>(false);
  const [visibleCodeExample, setVisibleCodeExample] = useState<boolean>(false);
  const { paramNamespace } = useParams<{ paramNamespace: string }>();
  const { paramSystem } = useParams<{ paramSystem: string }>();
  const { paramVersion } = useParams<{ paramVersion: string }>();
  const { paramInstance } = useParams<{ paramInstance: string }>();
  const { paramCommand } = useParams<{ paramCommand: string }>();
  const [requestCommand, setRequestCommand] = useState<RequestCommand>({
    namespace: paramNamespace ?? undefined,
    systemName: paramSystem ?? undefined,
    version: paramVersion ?? undefined,
    instance: paramInstance ?? undefined,
    command: paramCommand ?? undefined,
  });

  const [showCreateRequest, setShowCreateRequest] = useState<boolean>(
    (requestItem?.requestId === undefined || requestItem?.requestId === null) &&
      (requestItem?.jobId === undefined || requestItem?.jobId === null),
  );

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

  // Create Request Panel
  const updateRequestCommand = (requestCommand: RequestCommand) => {
    setRequestCommand(requestCommand);
    updateRequestItem({
      ...requestItem,
      requestCommandInput: requestCommand,
    });
  };

  useEffect(() => {
    if (selectedSystem) {
      setRequest((prevReq) => ({
        ...prevReq,
        namespace: selectedSystem?.namespace,
        system: selectedSystem?.name,
        system_version: selectedSystem?.version,
      }));
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
      setRequest((prevReq) => ({
        ...prevReq,
        instance_name: selectedInstance?.name,
      }));
    }
  }, [selectedInstance, setSelectedInstance]);

  useEffect(() => {
    if (selectedCommand) {
      setRequest((prevReq) => ({
        ...prevReq,
        command: selectedCommand?.name,
      }));
    }
  }, [selectedCommand]);

  useEffect(() => {
    if (
      requestItem?.requestId !== null &&
      requestItem?.requestId !== undefined &&
      requestItem?.request === undefined
    ) {
      GetRequest(requestItem.requestId, {})
        .then((responseRequest) => {
          GetSystemList()
            .then((responseSystems) => {
              const chosenSystem = responseSystems.find(
                (s) =>
                  s.namespace == responseRequest.namespace &&
                  s.name == responseRequest.system &&
                  s.version == responseRequest.system_version,
              );
              setSelectedSystem(chosenSystem);
              setSelectedInstance(
                chosenSystem?.instances?.find(
                  (i) => i.name == responseRequest.instance_name,
                ),
              );
              setSelectedCommand(
                chosenSystem?.commands?.find(
                  (c) =>
                    c.name == responseRequest.command &&
                    c.display_name == responseRequest.command_display_name,
                ),
              );
            })
            .catch((error) => {
              console.error("Error fetching systems:", error);
            });
          setRequest((prevReq) => ({
            ...prevReq,
            namespace: responseRequest.namespace,
            system: responseRequest.system,
            system_version: responseRequest.system_version,
            instance_name: responseRequest.instance_name,
            command_display_name: responseRequest.command_display_name,
            parameters: responseRequest.parameters,
          }));
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
          setActiveIndex(2);
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
          GetSystemList()
            .then((responseSystems) => {
              const chosenSystem = responseSystems.find(
                (s) =>
                  s.namespace == responseJob.request_template.namespace &&
                  s.name == responseJob.request_template.system &&
                  s.version == responseJob.request_template.system_version,
              );
              setSelectedSystem(chosenSystem);
              setSelectedInstance(
                chosenSystem?.instances?.find(
                  (i) => i.name == responseJob.request_template.instance_name,
                ),
              );
              setSelectedCommand(
                chosenSystem?.commands?.find(
                  (c) =>
                    c.name == responseJob.request_template.command &&
                    c.display_name ==
                      responseJob.request_template.command_display_name,
                ),
              );
            })
            .catch((error) => {
              console.error("Error fetching systems:", error);
            });
          updateJobValue(responseJob);
          updateRequestCommand({
            namespace: responseJob?.request_template?.namespace ?? undefined,
            systemName: responseJob?.request_template?.system ?? undefined,
            version: responseJob?.request_template?.system_version ?? undefined,
            instance: responseJob?.request_template?.instance_name ?? undefined,
            command: responseJob?.request_template?.command ?? undefined,
          });
          setShowCreateRequest(true);
          setActiveIndex(2);
        })
        .catch((error) => {
          console.error("Error fetching job:", error);
        });
    } else if (requestItem?.job !== undefined) {
      const job = requestItem.job;
      GetSystemList()
        .then((responseSystems) => {
          const chosenSystem = responseSystems.find(
            (s) =>
              s.namespace == job.request_template.namespace &&
              s.name == job.request_template.system &&
              s.version == job.request_template.system_version,
          );
          setSelectedSystem(chosenSystem);
          setSelectedInstance(
            chosenSystem?.instances?.find(
              (i) => i.name == job.request_template.instance_name,
            ),
          );
          setSelectedCommand(
            chosenSystem?.commands?.find(
              (c) =>
                c.name == job.request_template.command &&
                c.display_name == job.request_template.command_display_name,
            ),
          );
        })
        .catch((error) => {
          console.error("Error fetching systems:", error);
        });
      updateJobValue(job);
      updateRequestCommand({
        namespace: job.request_template?.namespace ?? undefined,
        systemName: job.request_template?.system ?? undefined,
        version: job.request_template?.system_version ?? undefined,
        instance: job.request_template?.instance_name ?? undefined,
        command: job.request_template?.command ?? undefined,
      });
      setShowCreateRequest(true);
      setActiveIndex(2);
    } else {
      setShowCreateRequest(true);
      setActiveIndex(0);
    }
  }, []);

  const systemListButtonClick = (system: System) => {
    setSelectedSystem(system);
    stepperRef.current?.nextCallback();
  };

  const commandListButtonClick = (command: Command) => {
    setSelectedCommand(command);
    stepperRef.current?.nextCallback();
  };

  const iconItemTemplate = (item: any, options: any) => {
    if (item.icon) {
      return (
        <span className={options.className}>
          <FontAwesomeIcon icon={item.icon} />
        </span>
      );
    }
    return <span className={options.className}>{item.label}</span>;
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
        </div>
      }
      key={requestItem.itemId}
    >
      <Stepper
        ref={stepperRef}
        activeStep={activeIndex}
        style={{ flexBasis: "50rem" }}
        linear
      >
        <StepperPanel header="Pick System">
          <SystemList systemListButtonClick={systemListButtonClick} />
        </StepperPanel>
        <StepperPanel header="Pick Command">
          <BreadCrumb model={breadcrumbs} className="mb-2" />
          <CommandList
            selectedSystem={selectedSystem}
            commandListButtonClick={commandListButtonClick}
            instances={instances?.map((instance) => ({
              name: instance.name,
              label: instance.name,
            }))}
            selectedInstance={selectedInstance}
            setSelectedInstance={setSelectedInstance}
          />
          <div className="flex pt-4 justify-content-between">
            <Button
              label="Back"
              severity="secondary"
              onClick={() => {
                setSelectedInstance(undefined);
                stepperRef.current?.prevCallback();
              }}
            />
          </div>
        </StepperPanel>
        <StepperPanel header="Form">
          <BreadCrumb model={commandBreadcrumbs} className="mb-2" />
          <div className="flex ml-4">
            <span className="mr-2 align-self-center">Scheduled</span>
            <InputSwitch
              checked={showScheduleJob}
              onChange={(e) => updateShowScheduleJob(e.value)}
            />
          </div>
          {showScheduleJob && (
            <SchedulerForm
              scheduledJob={job}
              setScheduledJob={updateJobValue}
            />
          )}
          <CommandForm
            command={selectedCommand}
            disabled={false}
            request={request}
            setRequest={setRequest}
            requestCommand={requestCommand}
            setRequestCommand={setRequestCommand}
            resetForm={resetForm}
            setResetForm={setResetForm}
          />
          <div className="flex pt-4 justify-content-between">
            <Button
              label="Back"
              severity="secondary"
              onClick={() => {
                if (request?.parameters) {
                  const newRequest = { ...request };
                  delete newRequest.parameters;
                  setRequest(newRequest);
                }
                stepperRef.current?.prevCallback();
              }}
            />
            <Button
              label="Reset Form"
              severity="warning"
              onClick={() => setResetForm(true)}
              className="ml-2"
            />
            <div>
              <CodeExample
                visibleCodeExample={visibleCodeExample}
                setVisibleCodeExample={setVisibleCodeExample}
                request={request}
              />
              <Button
                label="Code Examples"
                severity="info"
                onClick={() => setVisibleCodeExample(true)}
                className="mr-2"
              />
            </div>
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
          </div>
        </StepperPanel>
      </Stepper>
    </Card>
  );
}

export default RequestWizard;
