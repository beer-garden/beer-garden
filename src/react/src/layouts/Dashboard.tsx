import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Badge } from "primereact/badge";
import { Button } from "primereact/button";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { Divider } from "primereact/divider";
import { Panel } from "primereact/panel";
import { Tag } from "primereact/tag";
import { Tree } from "primereact/tree";
import { useCallback, useEffect, useRef, useState } from "react";

import GardenSummary from "../components/GardenSummary";
import { Garden, Instance, System } from "../models/brewtils-types";
import { GetConfig } from "../services/config_service";
import { GetRootGarden } from "../services/garden_service";
import { GetSeverity } from "../services/util_service";

function GardenDashboard({
  listeners,
}: {
  listeners: Record<string, any>;
}) {
  const gardenRef = useRef<Garden>(null);
  const selectedGardenRef = useRef<Garden>(null);

  const [selectedGarden, setSelectedGarden] = useState<Garden>();

  const [gardenMenu, setGardenMenu] = useState<Array<any>>();

  const updateSelectedGarden = (garden?: Garden) => {
    if (garden) {
      selectedGardenRef.current = { ...sortSystems(garden) };
      setSelectedGarden({ ...selectedGardenRef.current });
    } else {
      selectedGardenRef.current = null;
      setSelectedGarden(undefined);
    }
  };

  const MonitorGardenEvents = useCallback(
    (message: any) => {
      let updatedRef = false;
      if (message.name === "GARDEN_REMOVED") {
        const removeGarden = (
          gardenId: string,
          compareGarden: Garden,
        ): Garden | null => {
          if (gardenId === compareGarden.id) {
            return null;
          } else {
            compareGarden.children = compareGarden.children
              .map((child: Garden) => removeGarden(gardenId, child))
              .filter(
                (child: Garden | null) => child !== null,
              ) as Array<Garden>;
          }
          return compareGarden;
        };
        if (message.payload.id === selectedGardenRef.current?.id) {
          updateSelectedGarden();
        }
        gardenRef.current = removeGarden(
          message.payload.id,
          gardenRef.current as Garden,
        );
        updatedRef = true;
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
              compareGarden.connection_type !== "Remote"
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
        gardenRef.current = upsertGarden(
          message.payload,
          gardenRef.current as Garden,
        );
        if (message.payload.id === selectedGardenRef.current?.id) {
          updateSelectedGarden(message.payload);
        }
        updatedRef = true;
      }

      if (updatedRef) {
        if (gardenRef.current) {
          setGardenMenu([generateMenu(gardenRef.current)]);
        } else {
          setGardenMenu([]);
        }
      }
    },
    [gardenRef],
  );

  const sortSystems = (garden: Garden) => {
    if (garden.systems && garden.systems.length > 0) {
      garden.systems = [
        ...garden.systems.sort((a: System, b: System) => {
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
        }),
      ];
    }
    return garden;
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

  const generateMenu = (garden: Garden) => {
    return {
      key: garden.id,
      label: garden.name,
      icon: "pi pi-sitemap",
      statusCounts: generateStatusCounts(garden),
      connectionCounts: generateConnectionStatus(garden),
      expanded: true,
      children:
        garden?.children && garden.children.length > 0
          ? garden.children.map((child: Garden) => generateMenu(child))
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

  const generateStatusCounts = (garden: Garden) => {
    const statusCounts = new Map();

    if (garden?.systems && garden.systems.length > 0) {
      for (const system of garden.systems) {
        system?.instances?.forEach((instance: Instance) => {
          if (instance.status) {
            statusCounts.set(
              instance.status,
              (statusCounts.get(instance.status) || 0) + 1,
            );
          }
        });
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

  useEffect(() => {
    if (gardenRef.current === null || gardenRef.current === undefined) {
      GetConfig()
        .then((config) => {
          GetRootGarden(config, {})
            .then((response_garden: Garden) => {
              gardenRef.current = response_garden;
              updateSelectedGarden(gardenRef.current);
              setGardenMenu([generateMenu(response_garden)]);
              listeners["DASHBOARD"] = {
                listener: MonitorGardenEvents,
              };
            })
            .catch((error) => {
              console.error("Error fetching root garden:", error);
            });
        })
        .catch((error) => {
          console.error("Error fetching root garden:", error);
        });
      return () => {
        // Cleanup function for when component unmounts
        delete listeners["DASHBOARD"];
      };
    }
  }, [MonitorGardenEvents, listeners]);

  const statusTemplate = (row: any) => {
    const severity = GetSeverity(row.status);

    return <Tag value={row.status} severity={severity} />;
  };

  const instanceActions = () => (
    <div className="flex gap-2">
      <Button rounded severity="success">
        <FontAwesomeIcon icon="play" />
      </Button>
      <Button rounded severity="warning">
        <FontAwesomeIcon icon="stop" />
      </Button>
    </div>
  );

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
      {/* LEFT NAV TREE */}
      <div className="col-3 surface-border p-3">
        <h3>Select Garden</h3>
        <Tree
          value={gardenMenu}
          nodeTemplate={gardenTreeNode}
          selectionMode="single"
          selectionKeys={selectedKey}
          onSelectionChange={(e) => {
            setSelectedKey(e.value);
            if (typeof e.value === "string") {
              findSelectedGarden(e.value);
            }
          }}
        />
      </div>

      {/* MAIN WORKSPACE */}
      <div
        className="col-9 p-4 grid grid-nogutter"
        style={{
          gridTemplateColumns: `repeat(auto-fit, minmax(250px, 1fr))`,
        }}
      >
        {/* Garden Summary */}
        {selectedGarden && (
          <GardenSummary
            gardenRef={gardenRef}
            selectedGarden={selectedGarden}
          />
        )}
        {selectedGarden?.systems?.map((system: System) => (
          <Panel
            key={system.id}
            header={`${selectedGarden.name === system.namespace ? "" : `${system.namespace} / `}${system.name} (${system.version})`}
            className="mb-4"
            toggleable
            style={{ width: "33%" }}
          >
            <div className="flex justify-content-between mb-3">
              <div
                className="flex-1"
                style={{ overflowWrap: "break-word", width: "80%" }}
              >
                {system.description}
              </div>
              <div>
                <Button severity="warning" size="small">
                  <FontAwesomeIcon icon="refresh" />
                </Button>
                <Button severity="danger" size="small">
                  <FontAwesomeIcon icon="trash" />
                </Button>
              </div>
            </div>

            <Divider />

            <DataTable value={system.instances}>
              <Column field="name" header="Instance" />
              <Column field="status" header="Status" body={statusTemplate} />
              <Column header="Actions" body={instanceActions} />
            </DataTable>
          </Panel>
        ))}
      </div>
    </div>
  );
}

export default GardenDashboard;
