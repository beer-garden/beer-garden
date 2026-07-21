import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Grid } from "@mui/material";
import Dialog from "@mui/material/Dialog";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import { PrimeReactProvider } from "primereact/api";
import { ConfirmDialog } from "primereact/confirmdialog";
import { Skeleton } from "primereact/skeleton";
import { useCallback, useEffect, useRef, useState } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { ACTIONS, type EventData, Joyride, STATUS } from "react-joyride";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { v4 as uuidv4 } from "uuid";

import AccessButton from "./components/AccessButton";
import ErrorPage from "./components/ErrorPage";
import HasAccess from "./components/HasAccess";
import NavigationMenu from "./components/Navigation";
import RequestItemCard from "./components/RequestItemCard";
import AboutIndex from "./layouts/AboutIndex";
import GardenDashboard from "./layouts/Dashboard";
import JobIndex from "./layouts/JobIndex";
import RequestIndex from "./layouts/RequestIndex";
import RequestView from "./layouts/RequestView";
import RoleIndex from "./layouts/RoleIndex";
import Swagger from "./layouts/Swagger";
import TopicIndex from "./layouts/TopicIndex";
import UserIndex from "./layouts/UserIndex";
import Workspace from "./layouts/Workspace";
import { Garden, Instance, System } from "./models/brewtils-types";
import { Config, Listener, RequestItem, TourStepProps } from "./models/models";
import { AutoCompletePT } from "./passthrough/AutoCompletePT";
import { ButtonPT } from "./passthrough/ButtonPT";
import { CalendarPT } from "./passthrough/CalendarPT";
import { CheckboxPT } from "./passthrough/CheckboxPT";
import { DataTablePT } from "./passthrough/DataTablePT";
import { DialogPT } from "./passthrough/DialogPT";
import { DropdownPT } from "./passthrough/DropdownPT";
import { FileUploadPT } from "./passthrough/FileUploadPT";
import { InputNumberPT } from "./passthrough/InputNumberPT";
import { InputTextareaPT } from "./passthrough/InputTextareaPT";
import { InputTextPT } from "./passthrough/InputTextPT";
import { MessagesPT } from "./passthrough/MessagesPT";
import { MultiSelectPT } from "./passthrough/MultiSelectPT";
import { PanelPT } from "./passthrough/PanelPT";
import { SplitButtonPT } from "./passthrough/SplitButtonPT";
import { TriStateCheckboxPT } from "./passthrough/TriStateCheckboxPT";
import { ColorModeProvider } from "./providers/ColorModeProvider";
import { SnackbarProvider } from "./providers/SnackbarProvider";
import { GetConfig } from "./services/config_service";
import { GetRootGarden } from "./services/garden_service";
import { preemptiveRefresh } from "./services/token_service";
import { GetToken } from "./services/token_service";
import { ConvertToTourStepProps } from "./services/tour_service";
import { ChangePowerUser, ChangeTheme } from "./services/util_service";

function App() {
  const socketRef = useRef(null as null | any);
  const listeners = useRef<Record<string, Listener>>({});
  const [config, setConfig] = useState<Config | undefined>(undefined);

  const [reloadUI, setReloadUI] = useState(0);
  const [requestItem, setRequestItem] = useState<RequestItem | undefined>(
    undefined,
  );

  const [fullScreenDialog, setFullScreenDialog] = useState(false);

  const addRequestItem = (itemParams?: Partial<RequestItem>) => {
    const newItem: RequestItem = {
      itemId: uuidv4(),
      type: "REQUEST",
      ...itemParams,
    };
    setRequestItem(newItem);
  };

  const tourStepsRef = useRef<Array<TourStepProps>>([]);

  const [runTour, setRunTour] = useState(false);
  const runTourRef = useRef(runTour);
  const toggleRunTour = () => {
    runTourRef.current = !runTourRef.current;
    setRunTour(runTourRef.current);
  };
  const rootGardenRef = useRef<Garden | undefined>(undefined);
  const [gardenState, setGardenState] = useState<number>(0);

  const updateRootGarden = (garden?: Garden) => {
    if (garden) {
      const removeSystems = (garden: Garden) => {
        if (garden.children) {
          garden.children = garden.children.map((child: Garden) => {
            return removeSystems(child);
          });
        }
        const updated = { ...garden };
        delete updated.systems;
        return updated;
      };
      rootGardenRef.current = removeSystems(garden);
      sessionStorage.setItem(
        "rootGarden",
        JSON.stringify(rootGardenRef.current),
      );
    } else {
      rootGardenRef.current = undefined;
      sessionStorage.removeItem("rootGarden");
    }
    setGardenState((prev) => prev + 1);
  };

  const systemsRef = useRef<System[] | undefined>(undefined);

  const [systemState, setSystemState] = useState<number>(0);

  const updateSystems = (systems?: System[]) => {
    if (systems) {
      systemsRef.current = systems;
      sessionStorage.setItem("systems", JSON.stringify(systemsRef.current));
    } else {
      systemsRef.current = undefined;
      sessionStorage.removeItem("systems");
    }
    setSystemState((prev) => prev + 1);
  };

  const runReloadUI = () => {
    sessionStorage.clear();
    localStorage.removeItem("requestItems");
    setReloadUI(reloadUI + 1);
  };

  const primeValue = {
    hideOverlaysOnDocumentScrolling: true,
    pt: {
      autocomplete: AutoCompletePT,
      button: ButtonPT,
      calendar: CalendarPT,
      checkbox: CheckboxPT,
      datatable: DataTablePT,
      dialog: DialogPT,
      dropdown: DropdownPT,
      fileUpload: FileUploadPT,
      inputNumber: InputNumberPT,
      inputText: InputTextPT,
      inputTextarea: InputTextareaPT,
      messages: MessagesPT,
      multiselect: MultiSelectPT,
      panel: PanelPT,
      splitButton: SplitButtonPT,
      triStateCheckbox: TriStateCheckboxPT,
    },
  };

  const loadRootGarden = (config: Config) => {
    GetRootGarden(config)
      .then((garden) => {
        const extractSystems = (garden: Garden): System[] => {
          let systems: System[] = [];
          if (garden.systems) {
            garden.systems.forEach((system: System) => {
              system.garden_name = garden.name;
              systems.push(system);
            });
          }
          if (garden.children) {
            for (const subGarden of garden.children) {
              systems = systems.concat(extractSystems(subGarden));
            }
          }
          return systems;
        };

        updateSystems(extractSystems(garden));
        updateRootGarden(garden);
      })
      .catch((error) => {
        console.log("Unable to retrieve root garden", error);
        updateSystems();
        updateRootGarden();
      });
  };

  useEffect(() => {
    // might take a second to load in all of the data, so pushed it off to to allow for the page to load
    ChangeTheme();
    ChangePowerUser();
    updateRootGarden(
      sessionStorage.getItem("rootGarden")
        ? JSON.parse(sessionStorage.getItem("rootGarden") || "")
        : undefined,
    );

    updateSystems(
      sessionStorage.getItem("systems")
        ? JSON.parse(sessionStorage.getItem("systems") || "")
        : undefined,
    );

    GetConfig()
      .then((config) => {
        setConfig(config);

        if (config?.auth_enabled === true) {
          preemptiveRefresh();
        }
        loadRootGarden(config);
      })
      .catch((error) => {
        console.log("Unable to retrieve configuration", error);
      });

    const interval = setInterval(preemptiveRefresh, 30000);

    // Cleanup function to clear the interval when the component unmounts
    return () => clearInterval(interval);
  }, []);

  const MonitorGardenSystemEvents = useCallback(
    (message: any) => {
      if (message.name === "GARDEN_REMOVED") {
        const removeGarden = (
          gardenId: string,
          compareGarden: Garden,
        ): Garden | undefined => {
          if (gardenId === compareGarden.id) {
            return undefined;
          } else {
            compareGarden.children = compareGarden.children
              .map((child: Garden) => removeGarden(gardenId, child))
              .filter(
                (child: Garden | undefined) => child !== undefined,
              ) as Array<Garden>;
          }
          return compareGarden;
        };

        if (!rootGardenRef.current) {
          return;
        }

        updateRootGarden(
          removeGarden(message.payload.id, rootGardenRef.current),
        );
        if (
          systemsRef.current?.some(
            (system: System) => system.garden_name === message.payload.name,
          )
        ) {
          updateSystems(
            systemsRef.current?.filter(
              (system: System) => system.garden_name !== message.payload.name,
            ),
          );
        }
      } else if (
        ["GARDEN_CONFIGURED", "GARDEN_UPDATED", "GARDEN_CREATED"].includes(
          message.name,
        )
      ) {
        const upsertGarden = (
          updatedGarden: Garden,
          compareGarden: Garden,
        ): Garden => {
          if (updatedGarden.id === compareGarden.id) {
            compareGarden = {
              ...compareGarden,
              receiving_connections: updatedGarden.receiving_connections,
              publishing_connections: updatedGarden.publishing_connections,
              metadata: updatedGarden.metadata,
            };
          } else {
            compareGarden.children = compareGarden.children.map(
              (child: Garden) => upsertGarden(updatedGarden, child),
            );
            // New one hop Garden
            if (
              !updatedGarden.has_parent &&
              updatedGarden.connection_type === "Remote" &&
              compareGarden.connection_type === "LOCAL"
            ) {
              if (
                !compareGarden.children.some(
                  (child: Garden) => child.id === updatedGarden.id,
                )
              ) {
                compareGarden.children.push(updatedGarden);
              }
            }
          }
          return compareGarden;
        };

        const upsertSystems = (
          updatedGarden: Garden,
          systems: System[] | undefined,
        ): System[] | undefined => {
          if (systems === undefined) {
            return updatedGarden.systems;
          }

          if (updatedGarden.systems) {
            systems = systems
              .filter(
                (system: System) => system.garden_name !== updatedGarden.name,
              )
              .concat(
                updatedGarden.systems.map((system: System) => {
                  system.garden_name = updatedGarden.name;
                  return system;
                }),
              );
          }
          return systems;
        };
        if (message.payload.systems) {
          updateSystems(upsertSystems(message.payload, systemsRef.current));
        }
        updateRootGarden(
          upsertGarden(message.payload, rootGardenRef.current as Garden),
        );
      } else if (message.name === "SYSTEM_REMOVED") {
        updateSystems(
          systemsRef.current?.filter(
            (system: System) => system.id !== message.payload.id,
          ),
        );
      } else if (message.name === "SYSTEM_UPDATED") {
        updateSystems(
          systemsRef.current?.map((system: System) => {
            if (system.id === message.payload.id) {
              return {
                ...system,
                ...message.payload,
              };
            }
            return system;
          }),
        );
      } else if (message.name === "SYSTEM_CREATED") {
        const newSystems = { ...message.payload };
        if (!newSystems.garden_name) {
          newSystems.garden_name = message.payload.namespace;
        }
        if (!newSystems.garden_name) {
          newSystems.garden_name = message.garden;
        }

        updateSystems(
          systemsRef.current
            ?.filter((system: System) => system.id !== message.payload.id)
            .concat(newSystems),
        );
      } else if (
        [
          "INSTANCE_STARTED",
          "INSTANCE_STOPPED",
          "INSTANCE_UPDATED",
          "INSTANCE_INITIALIZED",
        ].includes(message.name)
      ) {
        const updateInstance = (
          updatedInstance: Instance,
          checkSystems: System[] | undefined,
        ): [System[] | undefined, boolean] => {
          if (!checkSystems) {
            return [undefined, false];
          }

          if (
            checkSystems.some((system: System) =>
              system.instances?.some(
                (instance: Instance) => instance.id === updatedInstance.id,
              ),
            )
          ) {
            checkSystems = checkSystems.map((system: System) => {
              if (
                system.instances &&
                system.instances.some(
                  (instance: Instance) => instance.id === updatedInstance.id,
                )
              ) {
                system.instances = system.instances.map(
                  (instance: Instance) => {
                    if (instance.id === updatedInstance.id) {
                      return {
                        ...instance,
                        ...{
                          status: updatedInstance.status,
                          metadata: updatedInstance.metadata,
                        },
                      };
                    }
                    return instance;
                  },
                );
              }
              return system;
            });

            return [checkSystems, true];
          }

          return [checkSystems, false];
        };

        const [updatedSystems, updated] = updateInstance(
          message.payload,
          systemsRef.current,
        );
        if (updated) {
          updateSystems(updatedSystems);
        }
      }
    },
    [rootGardenRef, systemsRef],
  );

  useEffect(() => {
    if (config && config.auth_enabled === true) {
      if (
        (systemsRef.current !== undefined ||
          rootGardenRef.current !== undefined) &&
        GetToken() === null
      ) {
        updateSystems();
        updateRootGarden();
      } else if (
        (systemsRef.current === undefined ||
          rootGardenRef.current === undefined) &&
        GetToken() !== null
      ) {
        loadRootGarden(config);
      }
    }
  }, [reloadUI]);

  useEffect(() => {
    // Create WebSocket connection when component mounts
    socketRef.current = new WebSocket("/api/v1/socket/events/");
    const handleMessage = (event: any) => {
      // Update React state with new message

      if (event.data) {
        const eventData = JSON.parse(event.data);
        if (eventData?.name === "AUTHORIZATION_REQUIRED") {
          socketRef.current.send(
            JSON.stringify({ name: "UPDATE_TOKEN", payload: GetToken() }),
          );
        } else {
          for (const [key, listener] of Object.entries(listeners.current)) {
            if (key && listener && listener.listener) {
              listener.listener(eventData);
              console.debug(
                "Message from server for listener",
                key,
                event.data,
              );
            }
          }
        }
      }
    };
    // Add event listeners to the socket instance
    socketRef.current.addEventListener("message", handleMessage);
    listeners.current.root_app = {
      listener: MonitorGardenSystemEvents,
    } as Listener;

    // Cleanup function to run when the component unmounts or dependencies change
    return () => {
      socketRef.current.close();
    };
  }, []);

  const baseURL =
    import.meta.env.VITE_BASE_URL === "/"
      ? undefined
      : import.meta.env.VITE_BASE_URL || undefined;

  const handleJoyrideEvent = (data: EventData) => {
    const { action, status } = data;

    if (action === ACTIONS.CLOSE) {
      runTourRef.current = false;
      setRunTour(false);
    } else if (
      ([STATUS.FINISHED, STATUS.SKIPPED] as string[]).includes(status)
    ) {
      runTourRef.current = false;
      setRunTour(false);
    }
  };

  function ErrorFallback({ error }: { error: unknown }) {
    let errorMsg = "";
    if (error instanceof Error) {
      errorMsg = error.toString();
    }
    return <ErrorPage errorMsg={errorMsg} />;
  }

  return (
    <PrimeReactProvider value={primeValue}>
      <ColorModeProvider>
        <SnackbarProvider>
          {config && Object.keys(config).length === 0 && (
            <div>
              <Skeleton height="5rem" className="mb-2" />
              <Skeleton height="40rem" />
            </div>
          )}
          {config && Object.keys(config).length > 0 && (
            <div className="flex" key={reloadUI}>
              <div className="flex-grow-1">
                <BrowserRouter basename={baseURL}>
                  {runTour && (
                    <Joyride
                      onEvent={handleJoyrideEvent}
                      continuous
                      run={true}
                      steps={ConvertToTourStepProps(tourStepsRef.current)}
                    />
                  )}
                  <div role="navigation">
                    <NavigationMenu
                      listeners={listeners.current}
                      config={config}
                      runReloadUI={runReloadUI}
                      addRequestItem={addRequestItem}
                      toggleRunTour={toggleRunTour}
                      tourStepsRef={tourStepsRef}
                    />
                  </div>
                  <ConfirmDialog />
                  {requestItem && (
                    <Dialog
                      open={requestItem !== undefined}
                      fullScreen={fullScreenDialog}
                      maxWidth="xl"
                      onClose={() => {
                        setRequestItem(undefined);
                        setFullScreenDialog(false);
                      }}
                    >
                      <DialogTitle
                        sx={{ m: 0, p: 2 }}
                        id="customized-dialog-title"
                      >
                        <Grid container>
                          <Grid size="grow">
                            {requestItem.type === "REQUEST" && "Create Request"}
                            {requestItem.type === "VIEW_REQUEST" &&
                              `View Request: ${requestItem?.requestId}`}
                            {requestItem.type === "VIEW_JOB" &&
                              `View Scheduled Job: ${requestItem?.jobId}`}
                            {requestItem.type === "VIEW_TOPIC" &&
                              `View Topic: ${requestItem?.topic?.name}`}
                          </Grid>
                          <Grid>
                            {fullScreenDialog === false && (
                              <AccessButton
                                sx={{ mr: 2 }}
                                onClick={() => setFullScreenDialog(true)}
                              >
                                <FontAwesomeIcon icon="maximize" />
                              </AccessButton>
                            )}
                            {fullScreenDialog === true && (
                              <AccessButton
                                sx={{ mr: 2 }}
                                onClick={() => setFullScreenDialog(false)}
                              >
                                <FontAwesomeIcon icon="minimize" />
                              </AccessButton>
                            )}
                            <AccessButton
                              sx={{ mr: 2 }}
                              onClick={() => {
                                setRequestItem(undefined);
                                setFullScreenDialog(false);
                              }}
                            >
                              <FontAwesomeIcon icon="xmark" />
                            </AccessButton>
                          </Grid>
                        </Grid>
                      </DialogTitle>

                      <DialogContent dividers>
                        <RequestItemCard
                          removeItem={() => {
                            setRequestItem(undefined);
                          }}
                          updateRequestItem={addRequestItem}
                          requestItem={requestItem}
                          listeners={listeners}
                          config={config}
                          isDialog={true}
                        />
                      </DialogContent>
                    </Dialog>
                  )}
                  <div
                    className="flex-grow-1"
                    role="main"
                    id="main-content"
                    tabIndex={-1}
                  >
                    <HasAccess
                      config={config}
                      permission="READ_ONLY"
                      renderAuthFailed={
                        <ErrorPage
                          errorCode={401}
                          errorMsg="Insufficient access or not logged in. Please contact Garden Administrator."
                        />
                      }
                    >
                      <ErrorBoundary FallbackComponent={ErrorFallback}>
                        <Routes>
                          <Route
                            path="/dashboard"
                            element={
                              <GardenDashboard
                                tourStepsRef={tourStepsRef}
                                gardenRef={rootGardenRef}
                                systemsRef={systemsRef}
                                gardenState={gardenState}
                                systemState={systemState}
                                addRequestItem={addRequestItem}
                                config={config}
                                listeners={listeners.current}
                              />
                            }
                          />
                          <Route
                            path="/request/:requestId"
                            element={
                              <RequestView
                                listeners={listeners.current}
                                config={config}
                                addRequestItem={addRequestItem}
                              />
                            }
                          />
                          <Route
                            path="/requests"
                            element={
                              <RequestIndex
                                listeners={listeners.current}
                                tourStepsRef={tourStepsRef}
                                addRequestItem={addRequestItem}
                              />
                            }
                          />
                          <Route
                            path="/create/:defaultType/:paramNamespace?/:paramSystem?/:paramVersion?/:paramInstance?/:paramCommand?"
                            element={
                              <Workspace
                                listeners={listeners.current}
                                display={false}
                                tourStepsRef={tourStepsRef}
                                config={config}
                              />
                            }
                          />
                          <Route
                            path="/recreate/:requestId"
                            element={
                              <Workspace
                                listeners={listeners.current}
                                display={false}
                                tourStepsRef={tourStepsRef}
                                config={config}
                              />
                            }
                          />
                          <Route
                            path="/workspace"
                            element={
                              <Workspace
                                listeners={listeners.current}
                                tourStepsRef={tourStepsRef}
                                config={config}
                              />
                            }
                          />
                          <Route
                            path="/workspace/request/:requestId"
                            element={
                              <Workspace
                                listeners={listeners.current}
                                display={true}
                                tourStepsRef={tourStepsRef}
                                config={config}
                              />
                            }
                          />
                          <Route
                            path="/workspace/job/:jobId"
                            element={
                              <Workspace
                                listeners={listeners.current}
                                display={true}
                                tourStepsRef={tourStepsRef}
                                config={config}
                              />
                            }
                          />
                          <Route
                            path="/jobs"
                            element={
                              <JobIndex
                                listeners={listeners.current}
                                tourStepsRef={tourStepsRef}
                                addRequestItem={addRequestItem}
                                config={config}
                              />
                            }
                          />
                          <Route
                            path="/job/:jobId"
                            element={
                              <Workspace
                                listeners={listeners.current}
                                display={false}
                                tourStepsRef={tourStepsRef}
                                config={config}
                              />
                            }
                          />
                          <Route
                            path="/about"
                            element={<AboutIndex config={config} />}
                          />
                          <Route
                            path="/roles"
                            element={
                              <HasAccess
                                config={config}
                                permission="GARDEN_ADMIN"
                                isGlobal={true}
                                renderAuthFailed={
                                  <ErrorPage
                                    errorCode={401}
                                    errorMsg="Insufficient Access for Roles Management. Please contact Garden Administrator"
                                  />
                                }
                              >
                                <RoleIndex
                                  config={config}
                                  tourStepsRef={tourStepsRef}
                                />
                              </HasAccess>
                            }
                          />
                          <Route
                            path="/topics"
                            element={
                              <TopicIndex
                                config={config}
                                listeners={listeners}
                                addRequestItem={addRequestItem}
                              />
                            }
                          />
                          <Route
                            path="/users"
                            element={
                              <UserIndex
                                config={config}
                                tourStepsRef={tourStepsRef}
                              />
                            }
                          />
                          <Route path="/swagger" element={<Swagger />} />
                          <Route
                            path="/"
                            element={
                              <GardenDashboard
                                tourStepsRef={tourStepsRef}
                                gardenRef={rootGardenRef}
                                systemsRef={systemsRef}
                                gardenState={gardenState}
                                systemState={systemState}
                                addRequestItem={addRequestItem}
                                config={config}
                                listeners={listeners.current}
                              />
                            }
                          />
                          <Route
                            path="*"
                            element={<ErrorPage errorCode={404} />}
                          />
                        </Routes>
                      </ErrorBoundary>
                    </HasAccess>
                  </div>
                </BrowserRouter>
              </div>
            </div>
          )}
        </SnackbarProvider>
      </ColorModeProvider>
    </PrimeReactProvider>
  );
}

export default App;
