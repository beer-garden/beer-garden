import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "primereact/button";
import { Dialog } from "primereact/dialog";
import { Skeleton } from "primereact/skeleton";
import { SplitButton } from "primereact/splitbutton";
import { Stepper } from "primereact/stepper";
import { StepperPanel } from "primereact/stepperpanel";
import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";

import CommandCreate from "../components/CommandCreate";
import SchedulerForm from "../components/SchedulerForm";
import { Job, Request } from "../models/brewtils-types";
import { RequestCommand } from "../models/models";
import { CreateJob, GetJob, UpdateJob } from "../services/job_service";
import { GetRequest } from "../services/request_service";
import { PostRequest } from "../services/request_service";

function RequestCreate() {
  const { requestId } = useParams<{ requestId: string }>();
  const { jobId } = useParams<{ jobId: string }>();
  const { defaultType } = useParams<{ defaultType: string }>();
  const { paramNamespace } = useParams<{ paramNamespace: string }>();
  const { paramSystem } = useParams<{ paramSystem: string }>();
  const { paramVersion } = useParams<{ paramVersion: string }>();
  const { paramInstance } = useParams<{ paramInstance: string }>();
  const { paramCommand } = useParams<{ paramCommand: string }>();
  const stepperRef = useRef<null | any>(null);

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
    namespace: paramNamespace ?? null,
    systemName: paramSystem ?? null,
    version: paramVersion ?? null,
    instance: paramInstance ?? null,
    command: paramCommand ?? null,
  });

  const [showCreateRequest, setShowCreateRequest] = useState<boolean>(
    (requestId === undefined || requestId === null) &&
      (jobId === undefined || jobId === null),
  );

  const [visibleCodeExample, setVisibleCodeExample] = useState<boolean>(false);

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

  const CodeBlock = (codeType: string) => {
    const getHostName = () => {
      return window.location.hostname;
    };

    const getPort = () => {
      return window.location.port;
    };

    const getPrefix = () => {
      const path = window.location.pathname;

      for (const knownPaths of ["/create", "/recreate"]) {
        const index = path.indexOf(knownPaths);
        if (index > 0) {
          return path.slice(1, index) + "/";
        }
      }

      return "";
    };

    const getSslEnabled = () => {
      return window.location.protocol === "https:" ? "True" : "False";
    };

    const wgetCode = () => {
      return `
wget --method=POST -O- \\
  --body-data='${JSON.stringify(request)}' \\
  --header=Content-Type:application/json \\
  ${getHostName()}:${getPort()}${getPrefix()}/api/v1/requests?blocking=true
`;
    };

    const curlCode = () => {
      return `
curl -X POST ${getHostName()}:${getPort()}${getPrefix()}/api/v1/requests?blocking=true \\
  -H "Content-Type: application/json" \\
  -d '${JSON.stringify(request)}'
`;
    };

    const pythonCode = () => {
      const generateParams = () => {
        if (request?.parameters) {
          const printParams = [] as Array<string>;

          for (const [key, value] of Object.entries(
            request?.parameters || {},
          )) {
            if (value && value !== undefined && value !== null) {
              if (typeof value === "string") {
                printParams.push(key + '="' + value + '"');
              } else if (typeof value === "boolean") {
                printParams.push(key + "=" + (value ? "True" : "False"));
              } else {
                printParams.push(key + "=" + value);
              }
            }
          }

          return printParams.join(", ");
        }
        return "";
      };

      return `
from brewtils import SystemClient

request = SystemClient(
  system_name = '${request?.system}',
	system_namespace = '${request?.namespace}',
	version_constraint = '${request?.system_version}',
	default_instance = '${request?.instance_name}',
	bg_host = '${getHostName()}',
	bg_url_prefix = '${getPrefix()}',
	bg_port = ${getPort()},
	blocking = True,
	ssl_enabled = ${getSslEnabled()},
	ca_cert = None,
	ca_verify = None,
	client_cert = None).${request?.command ? request?.command : "command"}(${generateParams()})

print(request)
`;
    };

    const code = () => {
      if (codeType === "Python") {
        return pythonCode();
      }
      if (codeType === "cURL") {
        return curlCode();
      }
      if (codeType === "Wget") {
        return wgetCode();
      }

      if (codeType === "JSON") {
        return JSON.stringify(request, null, 2);
      }

      return "";
    };
    const copyToClipboard = () => {
      navigator.clipboard.writeText(code()).catch((error) => {
        console.error("Error copying to clipboard:", error);
      });
    };

    return (
      <div style={{ position: "relative" }}>
        <h3>{codeType}</h3>
        <Button
          className="p-button-rounded p-button-text"
          onClick={copyToClipboard}
          style={{ position: "absolute", top: "0.5rem", right: "0.5rem" }}
        >
          <FontAwesomeIcon icon="copy" />
        </Button>
        <pre>
          <code>{code()}</code>
        </pre>
      </div>
    );
  };

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
                <Dialog
                  header={"Code Examples"}
                  visible={visibleCodeExample}
                  onHide={() => {
                    if (!visibleCodeExample) return;
                    setVisibleCodeExample(false);
                  }}
                  style={{ width: "50vw" }}
                >
                  <div>
                    Bytes and Base64 parameters are not supported in code
                    examples.
                  </div>
                  {CodeBlock("Python")}

                  {CodeBlock("cURL")}

                  {CodeBlock("Wget")}

                  {CodeBlock("JSON")}
                </Dialog>
                <SplitButton
                  label="Submit"
                  icon="pi pi-arrow-right"
                  onClick={() => {
                    submitRequest();
                  }}
                  model={[
                    {
                      label: "Code Examples",
                      // icon: <FontAwesomeIcon icon="arrow-up-right-from-square" />,
                      command: () => {
                        setVisibleCodeExample(true);
                      },
                    },
                  ]}
                />
              </div>
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
