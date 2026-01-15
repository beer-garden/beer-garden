import { Request, System } from "../models/brewtils-types";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { BreadCrumb } from "primereact/breadcrumb";
import RequestTreeChart from "../components/RequestTreeChart";
import { Steps } from "primereact/steps";
import { Toast } from "primereact/toast";
import { useState, useRef, use, useEffect } from "react";
import { MenuItem } from "primereact/menuitem";
import { Button } from "primereact/button";
import { Menubar } from "primereact/menubar";
import CommandForm from "../components/CommandForm";
import RequestOutput from "../components/RequestOutput";
import { Splitter, SplitterPanel } from "primereact/splitter";
import { Stepper } from "primereact/stepper";
import { StepperPanel } from "primereact/stepperpanel";
import { Message } from "primereact/message";
import { SplitButton } from "primereact/splitbutton";
import { useParams } from "react-router-dom";

import { GetRequest, DeleteRequest } from "../services/request_service";
import { GetSystemList } from "../services/system_service";

function UnformattedInput(request: Request) {
  return (
    <div>
      <Message severity="warn" text="Unable to find source System/Command" />
      <pre>{JSON.stringify(request.parameters, null, 2)}</pre>
    </div>
  );
}

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
        //
      },
    });
  } else {
    items.push({
      label: "Download Output",
      icon: <FontAwesomeIcon icon="download" />,
      command: () => {
        //
      },
    });
    items.push({
      label: "Delete Request",
      icon: <FontAwesomeIcon icon="xmark" />,
      command: () => {
        DeleteRequest(request).then(() => {
          window.open("/requests", "_self");
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

function RequestView() {
  const { requestId } = useParams<{ requestId: string }>();
  const [request, setRequest] = useState<Request | null>(null);
  const [system, setSystem] = useState<System | null>(null);
  const [command, setCommand] = useState<any>(null);
  const [rootRequest, setRootRequest] = useState<Request | null>(null);

  function loadRootRequest(check_request: Request) {
    if (
      check_request.has_parent === true &&
      check_request.parent &&
      check_request.parent.id
    ) {
      GetRequest(check_request.parent.id, {}).then((root_request) => {
        loadRootRequest(root_request);
      });
    } else {
      setRootRequest(check_request);
    }
  }

  useEffect(() => {
    if (!request) {
      GetRequest(requestId, {})
        .then((data: Request) => {
          setRequest(data);
        })
        .catch((error) => {
          console.error("Error fetching request:", error);
        });
    }
  }, []);

  useEffect(() => {
    if (request) {
      if (
        request.status &&
        ["CANCELED", "SUCCESS", "ERROR", "INVALID"].includes(request.status)
      ) {
        setActiveIndex(1);
      }

      loadRootRequest(request);

      const systems = GetSystemList({
        name: request.system,
        version: request.system_version,
        namespace: request.namespace,
        garden_name: request.target_garden,
      })
        .then((data) => {
          if (data.length > 0) {
            setSystem(data[0]);
          }
        })
        .catch((error) => {
          console.error("Error fetching system list:", error);
        });
    }
  }, [request]);

  useEffect(() => {
    if (system && system.commands && request) {
      const commandData = system.commands.find(
        (cmd) => cmd.name === request.command,
      );
      setCommand(commandData);
    }
  }, [system]);

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
            {command && (
              <CommandForm
                {...{
                  command: command,
                  request: request,
                  setRequest: setRequest,
                }}
              />
            )}
            {!command && <UnformattedInput {...request} />}
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
