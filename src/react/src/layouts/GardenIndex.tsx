import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Badge } from "primereact/badge";
import { Button } from "primereact/button";
import { Column } from "primereact/column";
import { Dialog } from "primereact/dialog";
import { MenuItem } from "primereact/menuitem";
import { SplitButton } from "primereact/splitbutton";
import { TreeTable } from "primereact/treetable";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { Connection, Garden } from "../models/brewtils-types";
import { GetConfig } from "../services/config_service";
import {
  DeleteGarden,
  GetRootGarden,
  RescanGarden,
  SyncGarden,
  SyncUsersGarden,
  UpdateApiGarden,
} from "../services/garden_service";

function GardenTable({ listeners }: { listeners: Record<string, any> }) {
  const gardenRef = useRef<Garden | null>(null);
  const [rootGarden, setRootGarden] = useState<Garden | null>(null);
  const [gardenNode, setGardenNode] = useState<any>([{}]);
  const [expandedKeys, setExpandedKeys] = useState<any>({});

  function setGarden(garden: Garden | null) {
    gardenRef.current = garden;
    setRootGarden(garden ? { ...garden } : null);
  }

  function parseGarden(garden: Garden, is_one_hop: boolean = false): any {
    function findStatus(connections: Array<Connection>, api: string) {
      const matchedAPIs = connections.filter((connection: Connection) => {
        return (
          connection.api?.toLowerCase() === api.toLowerCase() &&
          connection.status !== "NOT_CONFIGURED"
        );
      });

      if (matchedAPIs && matchedAPIs.length === 1) {
        return matchedAPIs[0].status;
      }
      return null;
    }

    function findLastSynced(connections: Array<Connection>): string | null {
      if (connections.length === 0) {
        return null;
      }
      const sortedConnections = connections.sort((a, b) => {
        const dateA = new Date(a?.status_info?.heartbeat || 0).getTime();
        const dateB = new Date(b?.status_info?.heartbeat || 0).getTime();
        return dateB - dateA; // Sort in descending order
      });
      return sortedConnections[0]?.status_info?.heartbeat || null;
    }

    const item = {
      key: garden.id,
      data: {
        id: garden.id,
        name: garden.name,
        version: garden.version,
        http_receiving: findStatus(garden.receiving_connections, "HTTP"),
        http_publishing: findStatus(garden.publishing_connections, "HTTP"),
        stomp_receiving: findStatus(garden.receiving_connections, "STOMP"),
        stomp_publishing: findStatus(garden.publishing_connections, "STOMP"),
        receiving_connections: garden.receiving_connections,
        publishing_connections: garden.publishing_connections,
        is_one_hop: is_one_hop,
        last_synced: findLastSynced(garden.receiving_connections),
      },
      children: [] as Array<any>,
    };

    if (
      typeof garden.children !== "undefined" &&
      garden.children !== null &&
      garden.children.length > 0
    ) {
      garden.children.forEach((childGarden: Garden) => {
        const child_item = parseGarden(childGarden);
        child_item.key = item.key + "-" + child_item.key;
        item.children.push(child_item);
      });
    }

    return item;
  }

  function getAllKeys(nodes: any) {
    let keys = {} as any;
    if (nodes && nodes.length) {
      for (const node of nodes) {
        keys[node.key] = true; // Mark as expanded
        if (node.children && node.children.length) {
          keys = { ...keys, ...getAllKeys(node.children) };
        }
      }
    }
    return keys;
  }

  const MonitorGardenEvents = useCallback(
    (message: any) => {
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
        setGarden(
          removeGarden(message.payload.id, gardenRef.current as Garden),
        );
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
        setGarden(upsertGarden(message.payload, gardenRef.current as Garden));
      }
    },
    [gardenRef],
  );

  useEffect(() => {
    if (rootGarden) {
      if (
        typeof rootGarden.children !== "undefined" &&
        rootGarden.children !== null &&
        rootGarden.children.length > 0
      ) {
        const newGardenNodes = [];
        for (const child of rootGarden.children) {
          newGardenNodes.push(parseGarden(child, true));
        }
        setGardenNode(newGardenNodes);
        setExpandedKeys(getAllKeys(newGardenNodes));
      } else {
        setGardenNode([]);
        setExpandedKeys({});
      }
    } else {
      GetConfig()
        .then((config) => {
          GetRootGarden(config, {})
            .then((response_garden: Garden) => {
              setGarden(response_garden);
              listeners["GARDEN_EVENTS"] = {
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
    }
  }, [rootGarden, MonitorGardenEvents, listeners]);

  const connectionTemplate = (node: any, field: string) => {
    if (node.data[field]) {
      const severityLevel = (status: string) => {
        if (["PUBLISHING", "RECEIVING"].includes(status)) {
          return "success";
        }
        if (["DISABLED"].includes(status)) {
          return "warning";
        }
        return "danger";
      };
      return (
        <div>
          <Badge
            className="mr-2"
            value={node.data[field]}
            severity={severityLevel(node.data[field])}
          />
          {node.data.is_one_hop && (
            <Button
              className="mr-2"
              data-testid={node.data.id + "_" + field + "_START"}
              onClick={() => {
                UpdateApiGarden(
                  node.data.name,
                  ["http_publishing", "stomp_publishing"].includes(field)
                    ? "PUBLISHING"
                    : "RECEIVING",
                  ["http_publishing", "http_receiving"].includes(field)
                    ? "HTTP"
                    : "STOMP",
                  ["http_publishing", "stomp_publishing"].includes(field)
                    ? "PUBLISHING"
                    : "RECEIVING",
                ).catch((error) => {
                  console.error("Error Updating Garden API Connection:", error);
                });
              }}
            >
              <FontAwesomeIcon icon="play" />
            </Button>
          )}
          {node.data.is_one_hop && (
            <Button
              className="mr-2"
              data-testid={node.data.id + "_" + field + "_STOP"}
              onClick={() => {
                UpdateApiGarden(
                  node.data.name,
                  "DISABLED",
                  ["http_publishing", "http_receiving"].includes(field)
                    ? "HTTP"
                    : "STOMP",
                  ["http_publishing", "stomp_publishing"].includes(field)
                    ? "PUBLISHING"
                    : "RECEIVING",
                ).catch((error) => {
                  console.error("Error Updating Garden API Connection:", error);
                });
              }}
            >
              <FontAwesomeIcon icon="stop" />
            </Button>
          )}
        </div>
      );
    }
  };

  const gardenActionsTemplate = (node: any) => {
    const items: MenuItem[] = [];
    const [visibleConfig, setVisibleConfig] = useState<boolean>(false);

    items.push({
      label: "Delete",
      icon: <FontAwesomeIcon className="mr-2" icon="circle-minus" />,
      command: () => {
        DeleteGarden(node.data.name).catch((error) => {
          console.error("Error Deleting Garden:", error);
        });
      },
    });

    if (node?.data?.is_one_hop) {
      items.push({
        label: "Configuration",
        icon: <FontAwesomeIcon className="mr-2" icon="file-code" />,
        command: () => {
          setVisibleConfig(true);
        },
      });
    }

    items.push({
      label: "Rescan Plugins",
      icon: <FontAwesomeIcon className="mr-2" icon="magnifying-glass" />,
      command: () => {},
    });

    items.push({
      label: "Rescan Downstream",
      icon: <FontAwesomeIcon className="mr-2" icon="magnifying-glass" />,
      command: () => {
        RescanGarden(node.data.name).catch((error) => {
          console.error("Error Rescanning Garden:", error);
        });
      },
    });

    items.push({
      label: "Clear Plugin Queues",
      icon: <FontAwesomeIcon className="mr-2" icon="eraser" />,
      command: () => {},
    });

    items.push({
      label: "Sync Users",
      icon: <FontAwesomeIcon className="mr-2" icon="users" />,
      command: () => {
        SyncUsersGarden(node.data.name).catch((error) => {
          console.error("Error Syncing Users in Garden:", error);
        });
      },
    });

    const configs = {
      http_publishing_config: undefined,
      stomp_publishing_config: undefined,
      stomp_receiving_config: undefined,
    };

    if (node?.data?.publishing_connections) {
      for (const connection of node.data.publishing_connections) {
        if (connection.api.toUpperCase() === "HTTP") {
          configs.http_publishing_config = connection.config;
        }
        if (connection.api.toUpperCase() === "STOMP") {
          configs.stomp_publishing_config = connection.config;
        }
      }
    }
    if (node?.data?.receiving_connections) {
      for (const connection of node.data.receiving_connections) {
        if (connection.api.toUpperCase() === "STOMP") {
          configs.stomp_receiving_config = connection.config;
        }
      }
    }

    return (
      <div>
        <SplitButton
          label="Sync"
          icon={<FontAwesomeIcon className="mr-2" icon="arrows-rotate" />}
          onClick={() => {
            SyncGarden(node.data.name).catch((error) => {
              console.error("Error Syncing Garden:", error);
            });
          }}
          model={items ? items : []}
          data-testid={node?.data?.id + "_ACTIONS"}
        />
        <Dialog
          header={"Configuration: " + node?.data?.name}
          visible={visibleConfig}
          onHide={() => {
            if (!visibleConfig) return;
            setVisibleConfig(false);
          }}
          style={{ width: "50vw" }}
          breakpoints={{ "960px": "75vw", "641px": "100vw" }}
        >
          <p className="m-0">
            {configs.http_publishing_config && (
              <>
                <h5>HTTP Publishing Configuration</h5>
                <pre>
                  {JSON.stringify(configs.http_publishing_config, null, 2)}
                </pre>
              </>
            )}
            {configs.stomp_publishing_config && (
              <>
                <h5>STOMP Publishing Configuration</h5>
                <pre>
                  {JSON.stringify(configs.stomp_publishing_config, null, 2)}
                </pre>
              </>
            )}
            {configs.stomp_receiving_config && (
              <>
                <h5>STOMP Receiving Configuration</h5>
                <pre>
                  {JSON.stringify(configs.stomp_receiving_config, null, 2)}
                </pre>
              </>
            )}
          </p>
        </Dialog>
      </div>
    );
  };

  const isNestedColumnEmpty = (field: string, nodes: Array<any>) => {
    if (
      nodes.some(
        (garden: any) =>
          garden !== undefined &&
          garden !== null &&
          garden.data !== undefined &&
          garden.data !== null &&
          garden.data[field] !== null &&
          garden.data[field] !== undefined &&
          garden.data[field] !== "",
      )
    ) {
      return false;
    }
    for (const node of nodes) {
      if (node.children && node.children.length > 0) {
        if (!isNestedColumnEmpty(field, node.children)) {
          return false;
        }
      }
    }

    return true;
  };

  const isColumnEmpty = (field: string) => {
    // Returns true if all nodes have null/undefined/empty string for the field

    if (gardenNode && gardenNode.length > 0) {
      if (!isNestedColumnEmpty(field, gardenNode)) {
        return false;
      }
    }
    return true;
  };

  const formatDate = (value: string) => {
    if (value === null || value === undefined || value === "") {
      return "UNKNOWN";
    }
    const date = new Date(value);
    return date.toLocaleDateString() + " " + date.toLocaleTimeString();
  };

  const columns = useMemo(() => {
    const cols = [
      { field: "version", header: "Version", body: undefined },
      {
        field: "last_synced",
        header: "Last Sync Seen",
        body: (node: any) => formatDate(node?.data?.last_synced),
      },
      {
        field: "http_receiving",
        header: "HTTP Receiving",
        body: (node: any) => connectionTemplate(node, "http_receiving"),
      },
      {
        field: "http_publishing",
        header: "HTTP Publishing",
        body: (node: any) => connectionTemplate(node, "http_publishing"),
      },
      {
        field: "stomp_receiving",
        header: "STOMP Receiving",
        body: (node: any) => connectionTemplate(node, "stomp_receiving"),
      },
      {
        field: "stomp_publishing",
        header: "STOMP Publishing",
        body: (node: any) => connectionTemplate(node, "stomp_publishing"),
      },
    ];

    // Filter out columns where isColumnEmpty is true
    return cols.filter((col) => !isColumnEmpty(col.field));
  }, [gardenNode]);

  const header = (
    <div>
      <Button
        className="mr-2"
        label="Sync All"
        onClick={() => {
          SyncGarden().catch((error) => {
            console.error("Error Syncing Gardens:", error);
          });
        }}
      />
      <Button
        className="mr-2"
        label="Rescan Downstream Configurations"
        onClick={() => {
          RescanGarden().catch((error) => {
            console.error("Error Rescanning Gardens:", error);
          });
        }}
      />
    </div>
  );

  return (
    gardenNode && (
      <TreeTable
        value={gardenNode}
        header={header}
        resizableColumns
        showGridlines
        expandedKeys={expandedKeys}
        onToggle={(e) => setExpandedKeys(e.value)}
      >
        <Column field="name" expander header="Name"></Column>
        {columns.map((col) => (
          <Column
            key={col.field}
            field={col.field}
            header={col.header}
            body={col.body}
          />
        ))}
        <Column body={gardenActionsTemplate} header="Actions"></Column>
      </TreeTable>
    )
  );
}

export default GardenTable;
