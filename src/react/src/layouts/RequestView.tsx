import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { BreadCrumb } from "primereact/breadcrumb";
import { MenuItem } from "primereact/menuitem";
import { Message } from "primereact/message";
import { Skeleton } from "primereact/skeleton";
import { SplitButton } from "primereact/splitbutton";
import { Stepper } from "primereact/stepper";
import { StepperPanel } from "primereact/stepperpanel";
import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";

import CommandForm from "../components/CommandForm";
import RequestOutput from "../components/RequestOutput";
import RequestTreeChart from "../components/RequestTreeChart";
import { Request, System } from "../models/brewtils-types";
import {
  CancelRequest,
  DeleteRequest,
  GetRequest,
} from "../services/request_service";
import { GetSystemList } from "../services/system_service";

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
  const fileUrl = `/api/v1/requests/output/${request.id}`;
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

function RequestOptions(request: Request) {
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
            window.open("/requests", "_self");
          })
          .catch((error) => {
            console.error("Error deleting request:", error);
          });
      },
    });
  }

  const pourAgain = (request: Request) => {
    window.open("/recreate/" + request.id, "_self");
  };

  return (
    <div className="card flex justify-content-end">
      <SplitButton
        label="Pour Again"
        icon={<FontAwesomeIcon icon="plus" />}
        model={items}
        className="p-button-secondary"
        onClick={() => pourAgain(request)}
        severity="success"
      />
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

function RequestView({ listeners }: { listeners: Record<string, any> }) {
  const { requestId } = useParams<{ requestId: string }>();
  const [request, setRequest] = useState<Request | null>(null);
  const [system, setSystem] = useState<System | null>(null);
  const [command, setCommand] = useState<any>(null);
  const [rootRequest, setRootRequest] = useState<Request | null>(null);
  const [showCommandForm, setShowCommandForm] = useState(false);

  const rootRequestId = useRef<string | null>(null);

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
    } else {
      if (
        request.status &&
        ["CANCELED", "SUCCESS", "ERROR", "INVALID"].includes(request.status)
      ) {
        setActiveIndex(1);

        if (requestId in listeners) {
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
          {...{ rootRequest: rootRequest, currentRequestId: requestId }}
        />
      )}

      {request && (
        <Stepper
          ref={stepperRef}
          activeStep={activeIndex}
          style={{ flexBasis: "50rem" }}
        >
          <StepperPanel header="Request Parameters">
            <RequestOptions {...request} />
            {!showCommandForm && <Skeleton width="100%" height="10rem" />}
            {showCommandForm && command && (
              <CommandForm
                {...{
                  command: command,
                  request: request,
                  setRequest: setRequest,
                }}
              />
            )}
            {showCommandForm && !command && <UnformattedInput {...request} />}
          </StepperPanel>
          <StepperPanel header="Request Output">
            {request && <RequestOptions {...request} />}
            {request && <RequestOutput {...request} />}
          </StepperPanel>
        </Stepper>
      )}
    </div>
  );
}

export default RequestView;
