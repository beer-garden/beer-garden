import { Badge } from "primereact/badge";
import { ConfirmDialog } from "primereact/confirmdialog";
import { Toast } from "primereact/toast";
import { Tree } from "primereact/tree";
import { RefObject, useEffect, useRef, useState } from "react";

import GardenSummary from "../components/GardenSummary";
import SystemCard from "../components/SystemCard";
import UnassociatedRunnerCard from "../components/UnassociatedRunnerCard";
import { Garden, Runner, System } from "../models/brewtils-types";
import { Config } from "../models/models";
import { RequestItem, RunnerGroup, TourStepProps } from "../models/models";
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
  const [unassociatedRunners, setUnassociatedRunners] = useState<RunnerGroup[]>(
    [],
  );

  const [gardenMenu, setGardenMenu] = useState<Array<any>>();
  const toast = useRef<Toast>(null);

  const [loading, setLoading] = useState<boolean>(true);

  const updateSelectedGarden = (garden?: Garden) => {
    if (garden) {
      const matchedSystems = getSelectedSystems(garden);
      setSelectedSystems(matchedSystems);
      setSelectedGarden({ ...garden });
      selectedGardenRef.current = { ...garden };
      setUnassociatedRunners(getUnassociatedRunners());
    } else {
      selectedGardenRef.current = undefined;
      setSelectedGarden(undefined);
      setSelectedSystems([]);
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

  useEffect(() => {
    const MonitorRunners = (message: any) => {
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
      getUnassociatedRunners();
    };

    listeners["dashboard"] = {
      listener: MonitorRunners,
    };

    return () => {
      delete listeners["dashboard"];
    };
  });

  useEffect(() => {
    if (associatedRunnersRef.current === undefined) {
      GetRunnerList()
        .then((runners) => {
          associatedRunnersRef.current = runners;
          setAssociatedRunners(associatedRunnersRef.current);
          setUnassociatedRunners(getUnassociatedRunners());
        })
        .catch((error) => console.error("Error loading runners", error));
    } else {
      getUnassociatedRunners();
    }
  }, [selectedSystems]);

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

    getUnassociatedRunners();
  }, [gardenState, systemState]);

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

  const generateMenu = (garden: Garden, systems: System[] | undefined) => {
    return {
      key: garden.id,
      label: garden.name,
      statusCounts: generateStatusCounts(garden, systems),
      connectionCounts: generateConnectionStatus(garden),
      expanded: true,
      children:
        garden?.children && garden.children.length > 0
          ? garden.children.map((child: Garden) => generateMenu(child, systems))
          : [],
    };
  };

  const generateConnectionStatus = (garden: Garden) => {
    const statusCounts = new Map();

    const mapStatus = (status: string) => {
      if (status === "NOT_CONFIGURED") {
        return;
      } else if (["PUBLISHING", "RECEIVING"].includes(status)) {
        statusCounts.set("HEALTHY", (statusCounts.get("HEALTHY") || 0) + 1);
      } else {
        statusCounts.set(status, (statusCounts.get(status) || 0) + 1);
      }
    };

    if (
      garden.receiving_connections &&
      garden.receiving_connections.length > 0
    ) {
      for (const connection of garden.receiving_connections) {
        mapStatus(connection.status);
      }
    }

    if (
      garden.publishing_connections &&
      garden.publishing_connections.length > 0
    ) {
      for (const connection of garden.publishing_connections) {
        mapStatus(connection.status);
      }
    }
    if (statusCounts.size === 0) {
      return undefined;
    }

    return Array.from(statusCounts, ([status, count]) => {
      if (count && count > 0) {
        const statusSeverity = GetSeverity(status);
        return (
          <Badge
            value={count}
            severity={statusSeverity}
            key={status}
            title={status}
          />
        );
      }
      return null;
    });
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
          <Badge
            value={count}
            severity={statusSeverity}
            key={status}
            title={status}
          />
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

  useEffect(() => {
    AddTourStep(tourStepsRef, gardenTreeTourStep);
    return () => {
      ClearTourSteps(tourStepsRef, tourPrefix, tourUuid);
    };
  }, []);

  const [selectedKey, setSelectedKey] = useState<any | null>("");

  const gardenTreeNode = (node: any, options: any) => {
    return (
      <span className={options.className}>
        <div className="flex gap-1">
          <b className="flex-1">{node.label}</b>
          <div style={{ width: "30%" }}>
            {"Systems"} {node.statusCounts}
          </div>

          <div style={{ width: "25%" }}>
            {"Connections"} {node.connectionCounts}
          </div>
        </div>
      </span>
    );
  };

  return (
    <div className="grid h-screen">
      <Toast ref={toast} />
      <ConfirmDialog />
      {/* LEFT NAV TREE */}
      <div className="col-3 surface-border p-3">
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
      <div className="col-9">
        {/* Garden Summary */}
        <GardenSummary
          gardenRef={gardenRef}
          selectedGarden={selectedGarden}
          config={config}
          tourStepsRef={tourStepsRef}
          associatedRunners={associatedRunnersRef}
          selectedSystems={selectedSystems}
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
                  toast={toast}
                  config={config}
                />
              </div>
            ))}
            {selectedSystems?.map((system: System) => (
              <div
                key={system.id}
                className="mr-2 mb-2"
                style={{ width: "26.5vw", minWidth: "250px" }}
              >
                <SystemCard
                  system={system}
                  toast={toast}
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
      </div>
    </div>
  );
}

export default GardenDashboard;
