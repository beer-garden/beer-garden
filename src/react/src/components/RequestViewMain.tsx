import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { Message } from "primereact/message";
import { Skeleton } from "primereact/skeleton";
import { TabPanel, TabView } from "primereact/tabview";
import { Tag } from "primereact/tag";
import { useEffect, useRef, useState } from "react";

import CommandForm from "../components/CommandForm";
import RequestOptions from "../components/RequestOptions";
import RequestOutput from "../components/RequestOutput";
import { Request, System } from "../models/brewtils-types";
import { Config, RequestCommand, RequestItem } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import { GetRequestProjections } from "../services/request_service";
import { GetSystemList } from "../services/system_service";
import { GetSeverity } from "../services/util_service";

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
  setRequest: (request: Request | undefined) => void;
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
  const showSnackbar = useSnackbar();

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
            showSnackbar({
              severity: "error",
              summary: "Error",
              detail: `Error fetching request projections: ${error}`,
              life: 3000,
            });
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
            showSnackbar({
              severity: "error",
              summary: "Error",
              detail: `Error fetching system list: ${error}`,
              life: 3000,
            });
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

  const statusTemplate = (request: Request) => {
    return (
      <Tag
        value={request?.status}
        severity={GetSeverity(request?.status)}
        id={`request_view_status_${request?.id}`}
        className="ml-2"
      />
    );
  };

  const formatDate = (value: string) => {
    const date = new Date(value);
    return date.toLocaleDateString() + " " + date.toLocaleTimeString();
  };

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
      <div className="flex mb-2">
        <div className="flex-1">
          {isCard === false && (
            <div className="flex">
              <div className="flex flex-1">
                <h1>Request View: {request.id}</h1>
              </div>
              <div className="flex-2 mt-4">
                {request && (
                  <>
                    <RequestOptions
                      request={request}
                      setRequest={setRequest}
                      config={config}
                      addRequestItem={addRequestItem}
                      requestProjections={requestProjections}
                      requestProjectionSelected={requestProjectionSelected}
                      setRequestProjectionSelected={
                        setRequestProjectionSelected
                      }
                      requestProjectionSelectedRef={
                        requestProjectionSelectedRef
                      }
                      isCard={isCard}
                      openRequest={openRequest}
                      closeRequest={closeRequest}
                    />
                  </>
                )}
              </div>
            </div>
          )}

          <DataTable value={[request]} size="small">
            {isCard === true && (
              <Column
                header="Command"
                body={(rowData) =>
                  rowData.command_display_name ?? rowData.command
                }
              ></Column>
            )}
            <Column field="namespace" header="Namespace"></Column>
            <Column field="system" header="System"></Column>
            <Column field="system_version" header="Version"></Column>
            <Column field="instance_name" header="Instance"></Column>
            <Column header="Status" body={statusTemplate}></Column>
            {isCard === false && (
              <Column
                header="Created"
                body={(rowData) => formatDate(rowData.created_at)}
              ></Column>
            )}
            {isCard === false && (
              <Column
                header="Status Updated"
                body={(rowData) => formatDate(rowData.status_updated_at)}
              ></Column>
            )}
            {isCard === false && (
              <Column
                header="Last Updated"
                body={(rowData) => formatDate(rowData.updated_at)}
              ></Column>
            )}
            {request?.comment && (
              <Column field="comment" header="Comment"></Column>
            )}
            {isCard === true && (
              <Column
                header="Action"
                body={() => {
                  return (
                    <RequestOptions
                      request={request}
                      setRequest={setRequest}
                      config={config}
                      addRequestItem={addRequestItem}
                      requestProjections={requestProjections}
                      requestProjectionSelected={requestProjectionSelected}
                      setRequestProjectionSelected={
                        setRequestProjectionSelected
                      }
                      requestProjectionSelectedRef={
                        requestProjectionSelectedRef
                      }
                      isCard={isCard}
                      openRequest={openRequest}
                      closeRequest={closeRequest}
                    />
                  );
                }}
              ></Column>
            )}
          </DataTable>
        </div>
      </div>

      {request && (
        <div>
          <div className="flex">
            <div className="flex-1">
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
                  <>
                    {!showCommandForm && (
                      <Skeleton width="100%" height="10rem" />
                    )}
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
                    {showCommandForm && !command && (
                      <UnformattedInput {...request} />
                    )}
                  </>
                </TabPanel>
                <TabPanel
                  header="Request Output"
                  pt={{ headerAction: { tabIndex: 0 } }}
                >
                  <RequestOutput request={request} />
                </TabPanel>
              </TabView>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default RequestViewMain;
