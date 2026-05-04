import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { BreadCrumb } from "primereact/breadcrumb";
import { Button } from "primereact/button";
import { Dropdown } from "primereact/dropdown";
import { MenuItem } from "primereact/menuitem";
import { Message } from "primereact/message";
import { Skeleton } from "primereact/skeleton";
import { SplitButton } from "primereact/splitbutton";
import { Stepper } from "primereact/stepper";
import { StepperPanel } from "primereact/stepperpanel";
import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import CommandForm from "../components/CommandForm";
import HasAccess from "../components/HasAccess";
import RequestOutput from "../components/RequestOutput";
import RequestTreeChart from "../components/RequestTreeChart";
import { Request, System } from "../models/brewtils-types";
import { Config, RequestCommand, RequestItem } from "../models/models";
import {
  CancelRequest,
  DeleteRequest,
  GetRequest,
  GetRequestProjections,
} from "../services/request_service";
import { GetSystemList } from "../services/system_service";
import { GetBaseURL } from "../services/util_service";

function UnformattedInput(request: Request) {
  return (
    <div>
      <Message severity="warn" text="Unable to find source System/Command" />
      <pre>{JSON.stringify(request.parameters, null, 2)}</pre>
    </div>
  );
}

const handleDownload = (request: Request) => {
  // Example: fetch a file from a URL
  const fileUrl = `${GetBaseURL()}/api/v1/requests/output/${request.id}`;
  let filename = `${request.id}.txt`;
  if (request.output_type == "HTML") {
    filename = `${request.id}.html`;
  } else if (request.output_type == "JSON") {
    filename = `${request.id}.json`;
  }

  fetch(fileUrl)
    .then((response) => response.blob())
    .then((blob) => {
      // Create blob link to download
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", filename); // Set the custom download name
      document.body.appendChild(link);
      link.click(); // Trigger the download
      link?.parentNode?.removeChild(link); // Clean up the link
      window.URL.revokeObjectURL(url); // Free up the memory
    })
    .catch((error) => {
      console.error("Error fetching the file:", error);
    });
};

function RequestOptions({
  request,
  requestProjections,
  requestProjectionSelected,
  setRequestProjectionSelected,
  requestProjectionSelectedRef,
  addRequestItem,
}: {
  request: Request;
  requestProjections?: RequestCommand[];
  requestProjectionSelected?: RequestCommand;
  setRequestProjectionSelected: (value: RequestCommand | undefined) => void;
  requestProjectionSelectedRef: React.RefObject<RequestCommand | undefined>;
  addRequestItem: (itemParams?: Partial<RequestItem>) => void;
}) {
  const navigate = useNavigate();
  const items: MenuItem[] = [];

  if (
    request.status &&
    ["CREATED", "RECEIVED", "IN_PROGRESS"].includes(request.status)
  ) {
    items.push({
      label: "Cancel Request",
      icon: <FontAwesomeIcon icon="xmark" />,
      command: () => {
        CancelRequest(request).catch((error) => {
          console.error("Error canceling request:", error);
        });
      },
    });
  } else {
    items.push({
      label: "Download Output",
      icon: <FontAwesomeIcon icon="download" />,
      command: () => {
        handleDownload(request);
      },
    });

    items.push({
      label: "Delete Request",
      icon: <FontAwesomeIcon icon="xmark" />,
      command: () => {
        DeleteRequest(request)
          .then(() => {
            void navigate(`${GetBaseURL()}/requests`);
          })
          .catch((error) => {
            console.error("Error deleting request:", error);
          });
      },
    });
  }

  const pourAgain = (request: Request) => {
    addRequestItem({ requestId: request.id, type: "REQUEST" });
  };

  const commandTemplate = (requestCommand: RequestCommand) => {
    return (
      <span>
        {requestCommand?.namespace === request.namespace
          ? null
          : `${requestCommand?.namespace} / `}{" "}
        {requestCommand?.systemName} / {requestCommand?.version} /{" "}
        {requestCommand?.instance} / {requestCommand?.command}
      </span>
    );
  };

  return (
    <div className="card justify-content-end">
      <div className="flex flex-end">
        <SplitButton
          label="Pour Again"
          icon={<FontAwesomeIcon icon="plus" />}
          model={items}
          className="p-button-secondary"
          onClick={() => pourAgain(request)}
          severity="success"
          style={{ marginLeft: "auto" }}
        />
      </div>
      {requestProjections && requestProjections.length > 0 && (
        <div className="card">
          <h5>Run Next</h5>
          <Dropdown
            value={requestProjectionSelected}
            options={requestProjections}
            valueTemplate={commandTemplate}
            itemTemplate={commandTemplate}
            onChange={(e) => {
              requestProjectionSelectedRef.current = e.value;
              setRequestProjectionSelected(e.value);
            }}
            placeholder="Select a command to run next"
          />
          <Button
            label="Run"
            onClick={() => {
              if (requestProjectionSelectedRef.current) {
                addRequestItem({
                  type: "REQUEST",
                  requestCommandInput: requestProjectionSelectedRef.current,
                });
              }
            }}
          />
        </div>
      )}
    </div>
  );
}

function RequestHeader(request: Request) {
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

  const items = [
    {
      icon: "file-lines",
      template: iconItemTemplate,
    },
    {
      label: request.namespace,
      template: iconItemTemplate,
    },
    {
      label: request.system,
      template: iconItemTemplate,
    },
    {
      label: request.system_version,
      template: iconItemTemplate,
    },
    {
      label: request.instance_name,
      template: iconItemTemplate,
    },
    {
      label: request.command,
      template: iconItemTemplate,
    },
    {
      label: request.id,
      template: iconItemTemplate,
    },
  ];

  return <BreadCrumb model={items} />;
}

function RequestView({
  listeners,
  config,
  addRequestItem,
}: {
  listeners: Record<string, any>;
  config: Config;
  addRequestItem: (itemParams?: Partial<RequestItem>) => void;
}) {
  const { requestId } = useParams<{ requestId: string }>();
  const [request, setRequest] = useState<Request | null>(null);
  const [system, setSystem] = useState<System | null>(null);
  const [command, setCommand] = useState<any>(null);
  const [rootRequest, setRootRequest] = useState<Request | null>(null);
  const [showCommandForm, setShowCommandForm] = useState(false);

  const rootRequestId = useRef<string | null>(null);
  const [requestProjections, setRequestProjections] = useState<
    RequestCommand[] | undefined
  >(undefined);
  const [requestProjectionSelected, setRequestProjectionSelected] = useState<
    RequestCommand | undefined
  >(undefined);
  const requestProjectionSelectedRef = useRef<RequestCommand | undefined>(
    undefined,
  );

  const MonitorRequestId = useCallback(
    (message: any) => {
      if (message.payload_type === "Request") {
        if (
          requestId &&
          message.payload.id &&
          message.payload.id === requestId
        ) {
          setRequest(message.payload as Request);
        }
        if (
          rootRequestId.current &&
          message.payload.id &&
          message.payload.id === rootRequestId.current
        ) {
          setRootRequest(message.payload as Request);
        }
      }
    },
    [requestId],
  );

  useEffect(() => {
    if (!request) {
      if (requestId !== undefined) {
        GetRequest(requestId, {})
          .then((data: Request) => {
            setRequest(data);

            if (
              !(requestId in listeners) &&
              data.status &&
              ["CREATED", "IN_PROGRESS"].includes(data.status)
            ) {
              listeners[requestId] = {
                listener: MonitorRequestId,
              };
            }
          })
          .catch((error) => {
            console.error("Error fetching request:", error);
          });
      }
    } else {
      GetRequestProjections(request)
        .then((projections) => {
          setRequestProjections(projections);
          setRequestProjectionSelected(projections[0]);
          requestProjectionSelectedRef.current = projections[0];
        })
        .catch((error) => {
          console.error("Error fetching request projections:", error);
        });
      if (
        request.status &&
        ["CANCELED", "SUCCESS", "ERROR", "INVALID"].includes(request.status)
      ) {
        setActiveIndex(1);

        if (requestId && requestId in listeners) {
          delete listeners[requestId];
        }
      }

      const loadRootRequest = (check_request: Request) => {
        if (
          check_request.has_parent === true &&
          check_request.parent &&
          check_request.parent.id
        ) {
          GetRequest(check_request.parent.id, {})
            .then((root_request) => {
              loadRootRequest(root_request);
            })
            .catch((error) => {
              console.error("Error fetching parent request:", error);
            });
        } else {
          setRootRequest(check_request);
          if (check_request.id) {
            rootRequestId.current = check_request.id;
            if (!(check_request.id in listeners)) {
              listeners[check_request.id] = { listener: MonitorRequestId };
            }
          }
        }
      };

      loadRootRequest(request);

      if (!system) {
        GetSystemList({
          name: request.system,
          version: request.system_version,
          namespace: request.namespace,
          garden_name: request.target_garden,
        })
          .then((data) => {
            if (data.length > 0) {
              setSystem(data[0]);
            } else {
              setShowCommandForm(true);
            }
          })
          .catch((error) => {
            console.error("Error fetching system list:", error);
            setShowCommandForm(true);
          });
      } else if (system.commands) {
        const commandData = system.commands.find(
          (cmd) => cmd.name === request.command,
        );
        setCommand(commandData);
        setShowCommandForm(true);
      }
    }

    return () => {
      if (requestId) {
        delete listeners[requestId];
      }
      if (rootRequestId.current) {
        delete listeners[rootRequestId.current];
      }
    };
  }, [request, requestId, listeners, MonitorRequestId, system]);

  const stepperRef = useRef(null);
  const [activeIndex, setActiveIndex] = useState(0);

  return (
    <div>
      {request && <RequestHeader {...request} />}

      {rootRequest && (
        <RequestTreeChart
          {...{
            rootRequest: rootRequest,
            currentRequestId: requestId,
            config: config,
          }}
        />
      )}

      {request && (
        <Stepper
          ref={stepperRef}
          activeStep={activeIndex}
          style={{ flexBasis: "50rem" }}
        >
          <StepperPanel header="Request Parameters">
            {/* Need to determine if Read Only can still download values */}
            <div className="flex">
              {!showCommandForm && <Skeleton width="100%" height="10rem" />}
              {showCommandForm && command && (
                <CommandForm
                  {...{
                    command: command,
                    request: request,
                    setRequest: setRequest,
                    resetForm: false,
                    setResetForm: () => {},
                    setIsFormValid: () => {},
                  }}
                />
              )}
              {showCommandForm && !command && <UnformattedInput {...request} />}

              {request && (
                <div style={{ marginLeft: "auto" }}>
                  <HasAccess
                    config={config}
                    permission="OPERATOR"
                    hasNamespace={request.namespace}
                    hasSystemName={request.system}
                    hasInstanceName={request.instance_name}
                    hasSystemVersion={request.system_version}
                    hasCommandName={request.command}
                  >
                    <RequestOptions
                      request={request}
                      addRequestItem={addRequestItem}
                      requestProjections={requestProjections}
                      requestProjectionSelected={requestProjectionSelected}
                      setRequestProjectionSelected={
                        setRequestProjectionSelected
                      }
                      requestProjectionSelectedRef={
                        requestProjectionSelectedRef
                      }
                    />
                  </HasAccess>
                </div>
              )}
            </div>
          </StepperPanel>
          <StepperPanel header="Request Output">
            <div className="flex">
              {request && <RequestOutput {...request} />}
              {request && (
                <div style={{ marginLeft: "auto" }}>
                  <RequestOptions
                    request={request}
                    addRequestItem={addRequestItem}
                    requestProjections={requestProjections}
                    requestProjectionSelected={requestProjectionSelected}
                    setRequestProjectionSelected={setRequestProjectionSelected}
                    requestProjectionSelectedRef={requestProjectionSelectedRef}
                  />
                </div>
              )}
            </div>
          </StepperPanel>
        </Stepper>
      )}
    </div>
  );
}

export default RequestView;
