import { Message } from "primereact/message";
import { Skeleton } from "primereact/skeleton";
import { TabPanel, TabView } from "primereact/tabview";
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
  closeRequest,
}: {
  request: Request;
  setRequest: (request: Request | null) => void;
  config: Config;
  showProjections: boolean;
  addRequestItem: (itemParams?: Partial<RequestItem>) => void;
  isCard: boolean;
  openRequest?: () => void;
  closeRequest?: () => void;
}) {
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
        <div>
          <div className="flex mb-2 gap-2 justify-content-end mt-2">
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
              closeRequest={closeRequest}
            />
          </div>
          <TabView
            style={{ flexBasis: "85%" }}
            className="mt-2"
            activeIndex={activeIndex}
            onTabChange={(e) => setActiveIndex(e.index)}
          >
            <TabPanel
              header="Request Parameters"
              pt={{ headerAction: { tabIndex: 0 } }}
            >
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
            </TabPanel>
            <TabPanel
              header="Request Output"
              pt={{ headerAction: { tabIndex: 0 } }}
            >
              <RequestOutput request={request} />
            </TabPanel>
          </TabView>
        </div>
      )}
    </div>
  );
}

export default RequestViewMain;
