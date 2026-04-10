import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { BreadCrumb } from "primereact/breadcrumb";
import { Button } from "primereact/button";
import { Card } from "primereact/card";
import { Stepper } from "primereact/stepper";
import { StepperPanel } from "primereact/stepperpanel";
import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";

import { Command, Instance, Request, System } from "../models/brewtils-types";
import { RequestCommand, RequestItem } from "../models/models";
import { PostRequest } from "../services/request_service";
import CodeExample from "./CodeExample";
import CommandForm from "./CommandForm";
import CommandList from "./CommandList";
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
  const [activeIndex] = useState(0);
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
  const [request, setRequest] = useState<Request | null | undefined>(undefined);
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
          <SystemList
            stepperRef={stepperRef}
            setSelectedSystem={setSelectedSystem}
          />
        </StepperPanel>
        <StepperPanel header="Pick Command">
          <BreadCrumb model={breadcrumbs} className="mb-2" />
          <CommandList
            stepperRef={stepperRef}
            selectedSystem={selectedSystem}
            setSelectedCommand={setSelectedCommand}
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
            <Button
              label="Submit"
              onClick={() => {
                submitRequest();
              }}
            />
          </div>
        </StepperPanel>
      </Stepper>
    </Card>
  );
}

export default RequestWizard;
