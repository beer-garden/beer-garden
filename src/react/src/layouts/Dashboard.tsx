import { IconProp } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Badge } from "primereact/badge";
import { MultiSelect } from "primereact/multiselect";
import { Skeleton } from "primereact/skeleton";
import { Tag } from "primereact/tag";
import { Tooltip } from "primereact/tooltip";
import { Tree } from "primereact/tree";
import { RefObject, useEffect, useRef, useState } from "react";

import GardenSummary from "../components/GardenSummary";
import SystemCard from "../components/SystemCard";
import UnassociatedRunnerCard from "../components/UnassociatedRunnerCard";
import { Garden, Runner, System } from "../models/brewtils-types";
import { Config } from "../models/models";
import { RequestItem, RunnerGroup, TourStepProps } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import { GetRunnerList } from "../services/runner_service";
import {
  AddTourStep,
  ClearTourSteps,
  GenerateTourProps,
} from "../services/tour_service";
import { GenerateStatusCounts, GetSeverity } from "../services/util_service";

function GardenDashboard({
  gardenRef,
  systemsRef,
  gardenState,
  systemState,
  tourStepsRef,
  addRequestItem,
  config,
  listeners,
}: {
  gardenRef: RefObject<Garden | undefined>;
  systemsRef: RefObject<System[] | undefined>;
  gardenState: number;
  systemState: number;
  tourStepsRef: RefObject<Array<TourStepProps>>;
  addRequestItem: (itemParams?: Partial<RequestItem>) => void;
  config: Config;
  listeners: Record<string, any>;
}) {
  const tourUuid = "garden_dashboard_tour";
  const tourPrefix = "garden_dashboard";
  const selectedGardenRef = useRef<Garden | undefined>(undefined);
  const associatedRunnersRef = useRef<Runner[] | undefined>(undefined);
  const [associatedRunners, setAssociatedRunners] = useState<Runner[]>([]);

  const [selectedGarden, setSelectedGarden] = useState<Garden | undefined>();
  const [selectedSystems, setSelectedSystems] = useState<System[]>([]);
  const [filteredSystems, setFilteredSystems] = useState<System[]>([]);
  const [filteredStatuses, setFilteredStatuses] = useState<Array<string>>([]);
  const [unassociatedRunners, setUnassociatedRunners] = useState<RunnerGroup[]>(
    [],
  );

  const [gardenMenu, setGardenMenu] = useState<Array<any>>();

  const [loading, setLoading] = useState<boolean>(true);

  const showSnackbar = useSnackbar();

  const instanceStatuses = [
    "RUNNING",
    "INITIALIZING",
    "STARTING",
    "STOPPING",
    "AWAITING_SYSTEM",
    "PAUSED",
    "STOPPED",
    "UNRESPONSIVE",
    "DEAD",
    "ERROR",
    "UNKNOWN",
  ] as string[];

  const instanceStatusTemplate = (option: string) => {
    const statusSeverity = GetSeverity(option);

    return <Tag value={option} severity={statusSeverity} />;
  };

  const updateFilteredSystems = () => {
    if (selectedGardenRef?.current) {
      const matchedSystems = getSelectedSystems(selectedGardenRef?.current);
      setFilteredSystems(
        matchedSystems.filter(
          (system) =>
            filteredStatuses.length === 0 ||
            !system.instances ||
            system.instances.length === 0 ||
            system.instances.some(
              (instance) =>
                instance.status && filteredStatuses.includes(instance.status),
            ),
        ),
      );
    } else {
      setFilteredSystems([]);
    }
  };

  const updateSelectedGarden = (garden?: Garden) => {
    if (garden) {
      if (garden.name !== selectedGardenRef.current?.name) {
        setFilteredStatuses([]);
        setSelectedGarden({ ...garden });
        selectedGardenRef.current = { ...garden };
      }
      const matchedSystems = getSelectedSystems(garden);
      setSelectedSystems(matchedSystems);
      updateFilteredSystems();
      setUnassociatedRunners(getUnassociatedRunners());
    } else {
      selectedGardenRef.current = undefined;
      setSelectedGarden(undefined);
      setSelectedSystems([]);
      updateFilteredSystems();
    }
  };

  const getUnassociatedRunners = (): RunnerGroup[] => {
    const instanceMissingCheck = (runner: Runner): boolean => {
      if (selectedGardenRef.current && systemsRef.current) {
        for (const system of systemsRef.current) {
          if (
            system?.garden_name === selectedGardenRef.current?.name &&
            system.instances
          ) {
            for (const instance of system.instances) {
              if (instance?.metadata?.runner_id === runner.id) {
                return false;
              }
            }
          }
        }
      }

      return true;
    };

    if (
      selectedGardenRef.current?.name === gardenRef.current?.name &&
      associatedRunnersRef.current
    ) {
      const unassociated = associatedRunnersRef.current.filter((runner) => {
        return (
          runner.instance_id === undefined ||
          runner.instance_id === null ||
          runner.instance_id.length === 0 ||
          instanceMissingCheck(runner)
        );
      });

      const grouped = Object.groupBy(
        unassociated,
        (item) => item.path ?? "unknown",
      );

      return Object.keys(grouped).map(
        (key) => ({ path: key, runners: grouped[key] }) as RunnerGroup,
      );
    }

    return [];
  };

  // Root Level Updates
  useEffect(() => {
    if (gardenRef?.current) {
      setGardenMenu([generateMenu(gardenRef.current, systemsRef.current)]);
    } else {
      setGardenMenu([]);
    }
    setLoading(false);

    if (selectedGardenRef.current?.id && gardenRef?.current) {
      const findSelectedGarden = (
        garden_id: string,
        garden: Garden,
      ): Garden | undefined => {
        if (garden.id === garden_id) {
          return garden;
        }
        if (garden?.children && garden.children.length > 0) {
          for (const child of garden.children) {
            const foundGarden = findSelectedGarden(garden_id, child);
            if (foundGarden) {
              return foundGarden;
            }
          }
        }

        return undefined;
      };
      updateSelectedGarden(
        findSelectedGarden(selectedGardenRef.current.id, gardenRef.current),
      );
    } else if (selectedGardenRef.current === undefined && gardenRef?.current) {
      updateSelectedGarden(gardenRef?.current);
    } else {
      updateSelectedGarden(undefined);
    }

    if (associatedRunnersRef.current) {
      setUnassociatedRunners(getUnassociatedRunners());
    }
    if (selectedSystems) {
      updateFilteredSystems();
    }
  }, [gardenState, systemState, filteredStatuses, selectedGarden]);

  const getSelectedSystems = (garden: Garden): System[] => {
    if (systemsRef.current && systemsRef.current.length > 0) {
      return systemsRef.current
        .filter((sys) => sys.garden_name === garden.name)
        .sort((a: System, b: System) => {
          if (a?.name && b?.name) {
            const nameComparison = a.name.localeCompare(b.name);

            if (nameComparison !== 0) {
              return nameComparison;
            }

            if (a?.version && b?.version) {
              return a.version.localeCompare(b.version);
            }
            if (a?.version) {
              return -1;
            }
            return 1;
          }

          if (a?.name) {
            return -1;
          }
          return 1;
        });
    }
    return [];
  };

  const findSelectedGarden = (garden_id: string, gardens?: Array<Garden>) => {
    if (gardens === undefined || gardens === null) {
      if (gardenRef.current) {
        findSelectedGarden(garden_id, [gardenRef.current]);
      }
    }
    if (gardens !== undefined) {
      for (const garden of gardens) {
        if (garden.id === garden_id) {
          updateSelectedGarden(garden);
          return;
        } else if (garden?.children && garden.children.length > 0) {
          findSelectedGarden(garden_id, garden?.children);
        }
      }
    }
  };

  const generateMenu = (
    garden: Garden,
    systems: System[] | undefined,
    upstreamRouting: boolean = true,
  ) => {
    const receiving = receivingStatus(garden);
    const publishing = publishingStatus(garden);
    return {
      key: garden.id,
      label: garden.name,
      statusCounts: generateStatusCounts(garden, systems),
      gardenIcon: gardenIcon(garden, receiving, publishing, upstreamRouting),
      expanded: true,
      children:
        garden?.children && garden.children.length > 0
          ? garden.children.map((child: Garden) =>
              generateMenu(
                child,
                systems,
                upstreamRouting && receiving && publishing,
              ),
            )
          : [],
    };
  };

  const receivingStatus = (garden: Garden) => {
    if (
      garden.receiving_connections &&
      garden.receiving_connections.length > 0
    ) {
      for (const connection of garden.receiving_connections) {
        if (
          connection.status !== "NOT_CONFIGURED" &&
          !["NOT_CONFIGURED", "PUBLISHING", "RECEIVING"].includes(
            connection.status,
          )
        ) {
          return false;
        }
      }
    }
    return true;
  };

  const publishingStatus = (garden: Garden) => {
    if (
      garden.publishing_connections &&
      garden.publishing_connections.length > 0
    ) {
      for (const connection of garden.publishing_connections) {
        if (
          connection.status !== "NOT_CONFIGURED" &&
          !["NOT_CONFIGURED", "PUBLISHING", "RECEIVING"].includes(
            connection.status,
          )
        ) {
          return false;
        }
      }
    }
    return true;
  };

  const gardenIcon = (
    garden: Garden,
    receiving: boolean,
    publishing: boolean,
    parentRouting: boolean = true,
  ) => {
    if (!parentRouting) {
      return (
        <>
          <Tooltip
            content="Upstream Routing Error"
            target={`#GARDEN_MENU_${garden.id}`}
            position="bottom"
          />
          <span className="fa-layers" id={`GARDEN_MENU_${garden.id}`}>
            <FontAwesomeIcon
              icon="play"
              style={{ color: "var(--warning-color)" }}
              rotation={270}
            />
            <FontAwesomeIcon
              icon="triangle-exclamation"
              style={{ color: "var(--warning-background-color)" }}
            />
          </span>
        </>
      );
    } else if (publishing && receiving) {
      // Ideal scenario is to get this icon from the Garden model, but we
      // don't currently have access to the downstream icons
      return (
        <FontAwesomeIcon
          icon={(config?.icon_default as IconProp) ?? "beer-mug-empty"}
        />
      );
    } else if (!publishing && !receiving) {
      return (
        <>
          <Tooltip
            content={`Routing Error for ${garden.name}`}
            target={`#GARDEN_MENU_${garden.id}`}
            position="bottom"
          />
          <span className="fa-layers" id={`GARDEN_MENU_${garden.id}`}>
            <FontAwesomeIcon
              icon="circle"
              style={{ color: "var(--danger-color)" }}
            />
            <FontAwesomeIcon
              icon="circle-exclamation"
              style={{ color: "var(--danger-background-color)" }}
            />
          </span>
        </>
      );
    } else if (!publishing) {
      return (
        <>
          <Tooltip
            content={`Publishing Connection Error for ${garden.name}`}
            target={`#GARDEN_MENU_${garden.id}`}
            position="bottom"
          />
          <span className="fa-layers" id={`GARDEN_MENU_${garden.id}`}>
            <FontAwesomeIcon
              icon="circle"
              style={{ color: "var(--danger-color)" }}
            />
            <FontAwesomeIcon
              icon="circle-exclamation"
              style={{ color: "var(--danger-background-color)" }}
            />
          </span>
        </>
      );
    } else if (!receiving) {
      return (
        <>
          <Tooltip
            content={`Receiving Connection Error for ${garden.name}`}
            target={`#GARDEN_MENU_${garden.id}`}
            position="bottom"
          />
          <span className="fa-layers" id={`GARDEN_MENU_${garden.id}`}>
            <FontAwesomeIcon
              icon="circle"
              style={{ color: "var(--danger-color)" }}
            />
            <FontAwesomeIcon
              icon="circle-exclamation"
              style={{ color: "var(--danger-background-color)" }}
            />
          </span>
        </>
      );
    }
  };

  const generateStatusCounts = (
    garden: Garden,
    systems: System[] | undefined,
  ) => {
    const statusCounts = GenerateStatusCounts(
      gardenRef,
      associatedRunnersRef,
      garden,
      systems,
    );

    return Array.from(statusCounts, ([status, count]) => {
      if (count && count > 0) {
        const statusSeverity = GetSeverity(status);
        return (
          <div key={`${status}_${garden?.name}_count`}>
            <Tooltip
              content={`${status} Count ${count} for ${garden?.name}`}
              target={`#${status}_${garden?.id}_menu_severity_system_summary`}
              position="bottom"
            />
            <Badge
              value={count}
              id={`${status}_${garden?.id}_menu_severity_system_summary`}
              severity={statusSeverity}
              key={`${status}_${garden?.name}`}
            />
          </div>
        );
      }
      return null;
    });
  };

  const gardenTreeTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Garden Tree Menu",
    content: "Select a Garden to view its Status, Systems and Instances",
    layer: "LAYOUT",
    pos: 0,
  };

  // Sets up one time run values
  useEffect(() => {
    AddTourStep(tourStepsRef, gardenTreeTourStep);

    const MonitorRunners = (message: any) => {
      if (message.payload_type == "Instance") {
        if (
          message.name === "INSTANCE_STARTED" ||
          message.name === "INSTANCE_INITIALIZED" ||
          message.name === "INSTANCE_UPDATED"
        ) {
          if (
            associatedRunnersRef.current &&
            getUnassociatedRunners().length > 0
          ) {
            if (
              associatedRunnersRef.current.some(
                (runner) => runner.id === message.payload.metadata.runner_id,
              )
            ) {
              associatedRunnersRef.current = associatedRunnersRef.current.map(
                (runner) => {
                  if (runner.id === message.payload.metadata.runner_id) {
                    return { ...runner, instance_id: message.payload.id };
                  }
                  return runner;
                },
              );
              setAssociatedRunners(associatedRunnersRef.current);
            }
          }
        }
      }

      if (message.payload_type === "Runner") {
        if (message.name === "RUNNER_REMOVED") {
          if (associatedRunnersRef.current) {
            associatedRunnersRef.current = associatedRunnersRef.current.filter(
              (runner) => runner.id !== message.payload.id,
            );
            setAssociatedRunners(associatedRunnersRef.current);
          }
        } else {
          if (associatedRunnersRef.current) {
            if (
              associatedRunnersRef.current.some(
                (runner) => runner.id === message.payload.id,
              )
            ) {
              associatedRunnersRef.current = associatedRunnersRef.current.map(
                (runner) => {
                  if (runner.id === message.payload.id) {
                    return message.payload;
                  }
                  return runner;
                },
              );
              setAssociatedRunners(associatedRunnersRef.current);
            } else {
              associatedRunnersRef.current = [
                ...associatedRunnersRef.current,
                message.payload,
              ];
              setAssociatedRunners(associatedRunnersRef.current);
            }
          } else {
            associatedRunnersRef.current = [message.payload];
            setAssociatedRunners(associatedRunnersRef.current);
          }
        }
      }
      setUnassociatedRunners(getUnassociatedRunners());
    };

    listeners["dashboard"] = {
      listener: MonitorRunners,
    };

    if (associatedRunnersRef.current === undefined) {
      GetRunnerList()
        .then((runners) => {
          associatedRunnersRef.current = runners;
          setAssociatedRunners(associatedRunnersRef.current);
          setUnassociatedRunners(getUnassociatedRunners());
        })
        .catch((error) => {
          console.error("Error loading runners", error);
          showSnackbar({
            severity: "error",
            summary: "Error",
            detail: `Error loading runners: ${error}`,
            life: 3000,
          });
        });
    }

    return () => {
      ClearTourSteps(tourStepsRef, tourPrefix, tourUuid);
      delete listeners["dashboard"];
    };
  }, []);

  const [selectedKey, setSelectedKey] = useState<any | null>("");

  const gardenTreeNode = (node: any, options: any) => {
    return (
      <div className={options.className}>
        <div>
          {node.gardenIcon}
          <span className="ml-1">{node.label}</span>
        </div>
        <div style={{ flexWrap: "wrap" }} className="flex ml-4">
          {node.statusCounts}
        </div>
      </div>
    );
  };

  return (
    <div>
      {/* LEFT NAV TREE */}
      <div className="flex flex-wrap">
        <div
          style={{ width: "16%", minWidth: "250px" }}
          className="surface-border p-3"
        >
          <Tree
            {...GenerateTourProps(gardenTreeTourStep)}
            loading={loading}
            value={gardenMenu}
            emptyMessage={"No gardens found"}
            nodeTemplate={gardenTreeNode}
            selectionMode="single"
            selectionKeys={selectedKey}
            onSelectionChange={(e) => {
              setSelectedKey(e.value);
              if (typeof e.value === "string") {
                findSelectedGarden(e.value);
              }
            }}
            togglerTemplate={<></>}
          />
        </div>

        {/* MAIN WORKSPACE */}
        <div style={{ width: "84%", minWidth: "250px" }}>
          {/* Garden Summary */}
          <GardenSummary
            gardenRef={gardenRef}
            selectedGarden={selectedGarden}
            config={config}
            tourStepsRef={tourStepsRef}
            associatedRunners={associatedRunnersRef}
            selectedSystems={selectedSystems}
          />
          <datalist id="instance_status_multiselect_input" aria-hidden="true">
            {instanceStatuses?.map((status: string) => (
              <option key={status} value={status} />
            ))}
          </datalist>

          {loading ? (
            <Skeleton width="100%" height="350px"></Skeleton>
          ) : (
            <>
              <MultiSelect
                value={filteredStatuses}
                onChange={(e) => setFilteredStatuses(e.value)}
                options={instanceStatuses}
                itemTemplate={instanceStatusTemplate}
                placeholder="Filter by Instance Status"
                className="mb-3"
                filter
                pt={{
                  input: {
                    "aria-label": "Filter by Instance Status",
                    "aria-controls": "instance_status_multiselect_input",
                    autoComplete: "off",
                  },
                  triggerIcon: {
                    role: "img",
                    "aria-label": "Toggle Instance Status Filter",
                  },
                }}
              />

              <div className="flex justify-content-left">
                <div className="grid grid-nogutter gap-2">
                  {unassociatedRunners?.map((runnerGroup: RunnerGroup) => (
                    <div
                      key={runnerGroup.path}
                      className="mb-4 mr-2"
                      style={{ width: "26.5vw", minWidth: "250px" }}
                    >
                      <UnassociatedRunnerCard
                        runnerGroup={runnerGroup}
                        config={config}
                      />
                    </div>
                  ))}
                  {filteredSystems?.map((system: System) => (
                    <div
                      key={system.id}
                      className="mr-2 mb-2"
                      style={{ width: "26.5vw", minWidth: "250px" }}
                    >
                      <SystemCard
                        system={system}
                        tourStepsRef={tourStepsRef}
                        selectedGarden={selectedGarden?.name}
                        addRequestItem={addRequestItem}
                        config={config}
                        associatedRunners={associatedRunners}
                      />
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default GardenDashboard;
