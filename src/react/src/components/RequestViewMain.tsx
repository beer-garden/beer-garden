import { Message } from "primereact/message";
import { Skeleton } from "primereact/skeleton";
import { Stepper } from "primereact/stepper";
import { StepperPanel } from "primereact/stepperpanel";
import { useEffect, useRef, useState } from "react";

import CommandForm from "../components/CommandForm";
import RequestOptions from "../components/RequestOptions";
import RequestOutput from "../components/RequestOutput";
import { Request, System } from "../models/brewtils-types";
import { Config, RequestCommand, RequestItem } from "../models/models";
import { GetRequestProjections } from "../services/request_service";
import { GetSystemList } from "../services/system_service";

function UnformattedInput(request: Request) {
  return (
    <div>
      <Message severity="warn" text="Unable to find source System/Command" />
      <pre>{JSON.stringify(request.parameters, null, 2)}</pre>
    </div>
  );
}

function RequestViewMain({
  request,
  setRequest,
  config,
  addRequestItem,
  showProjections,
  isCard,
  openRequest,
}: {
  request: Request;
  setRequest: (request: Request | null) => void;
  config: Config;
  showProjections: boolean;
  addRequestItem: (itemParams?: Partial<RequestItem>) => void;
  isCard: boolean;
  openRequest?: () => void;
}) {
  const stepperRef = useRef(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [showCommandForm, setShowCommandForm] = useState(false);
  const [command, setCommand] = useState<any>(null);
  const [system, setSystem] = useState<System | null>(null);

  const [requestProjections, setRequestProjections] = useState<
    RequestCommand[] | undefined
  >(undefined);
  const [requestProjectionSelected, setRequestProjectionSelected] = useState<
    RequestCommand | undefined
  >(undefined);
  const requestProjectionSelectedRef = useRef<RequestCommand | undefined>(
    undefined,
  );

  useEffect(() => {
    if (request) {
      if (showProjections && request) {
        GetRequestProjections(request)
          .then((projections) => {
            setRequestProjections(projections);
            setRequestProjectionSelected(projections[0]);
            requestProjectionSelectedRef.current = projections[0];
          })
          .catch((error) => {
            console.error("Error fetching request projections:", error);
          });
      }

      if (
        request &&
        request.status &&
        ["CANCELED", "SUCCESS", "ERROR", "INVALID"].includes(request.status)
      ) {
        setActiveIndex(1);
      }
      if (!system && !showCommandForm) {
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
      } else if (!showCommandForm && system && system.commands) {
        const commandData = system.commands.find(
          (cmd) => cmd.name === request.command,
        );
        setCommand(commandData);
        setShowCommandForm(true);
      }
    }
  }, [request, showProjections, system]);

  // ARC Toolkit Errors:
  //     1) The tab role is missing the {{requiredContextRole}} required context role
  //     2) The list element is not expected inside the tablist role
  //     3) A relationship attribute (such as <label for="...">, or an ARIA attribute such as aria-controls="...") is pointing to a non-existent id.
  // Stepper Panel Content is not loaded into DOM until loaded causing checks to fail

  // ARC Toolkit Errors:
  //     1) Found an <ol> ordered list or <ul> unordered list that contains no list items.
  // PrimeReact CSS styling is `list-style-type:none` that hides it from check in DOM
  return (
    <div>
      {request && (
        <Stepper
          ref={stepperRef}
          activeStep={activeIndex}
          style={{ flexBasis: "50rem" }}
        >
          <StepperPanel
            header="Request Parameters"
            pt={{
              action: {
                id: `${request.id}_tab_1`,
                "aria-controls": `${request.id}_stepper_1`,
              },
              content: {
                id: `${request.id}_stepper_1`,
                role: "tabpanel",
                "aria-labelledby": `${request.id}_tab_1`,
              },
              number: {
                style: {
                  color: "var(--info-color)",
                  backgroundColor: "var(--info-background-color)",
                },
              },
              separator: {
                "aria-hidden": undefined,
                tabIndex: -1,
                style: {
                  color: "var(--info-background-color)",
                },
              },
            }}
          >
            {/* Need to determine if Read Only can still download values */}
            <div className="flex">
              {!showCommandForm && <Skeleton width="100%" height="10rem" />}
              {showCommandForm && command && (
                <CommandForm
                  {...{
                    command: command,
                    request: request,
                    setRequest: () => {},
                    resetForm: false,
                    setResetForm: () => {},
                    setIsFormValid: () => {},
                  }}
                />
              )}
              {showCommandForm && !command && <UnformattedInput {...request} />}

              {request && (
                <div style={{ marginLeft: "auto" }}>
                  <RequestOptions
                    request={request}
                    setRequest={setRequest}
                    config={config}
                    addRequestItem={addRequestItem}
                    requestProjections={requestProjections}
                    requestProjectionSelected={requestProjectionSelected}
                    setRequestProjectionSelected={setRequestProjectionSelected}
                    requestProjectionSelectedRef={requestProjectionSelectedRef}
                    isCard={isCard}
                    openRequest={openRequest}
                  />
                </div>
              )}
            </div>
          </StepperPanel>
          <StepperPanel
            header="Request Output"
            pt={{
              action: {
                id: `${request.id}_tab_2`,
                "aria-controls": `${request.id}_stepper_2`,
              },
              content: {
                id: `${request.id}_stepper_2`,
                role: "tabpanel",
                "aria-labelledby": `${request.id}_tab_2`,
              },
              number: {
                style: {
                  color: "var(--info-color)",
                  backgroundColor: "var(--info-background-color)",
                },
              },
              separator: {
                "aria-hidden": undefined,
                tabIndex: -1,
                style: {
                  color: "var(--info-background-color)",
                },
              },
            }}
          >
            <div className="flex">
              {request && <RequestOutput request={request} />}
              {request && (
                <div style={{ marginLeft: "auto" }}>
                  <RequestOptions
                    request={request}
                    setRequest={setRequest}
                    config={config}
                    addRequestItem={addRequestItem}
                    requestProjections={requestProjections}
                    requestProjectionSelected={requestProjectionSelected}
                    setRequestProjectionSelected={setRequestProjectionSelected}
                    requestProjectionSelectedRef={requestProjectionSelectedRef}
                    isCard={isCard}
                    openRequest={openRequest}
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

export default RequestViewMain;
