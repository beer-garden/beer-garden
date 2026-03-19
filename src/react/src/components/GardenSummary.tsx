import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Badge } from "primereact/badge";
import { Button } from "primereact/button";
import { Card } from "primereact/card";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { Tag } from "primereact/tag";
import { RefObject, useEffect, useState } from "react";

import { Connection, Garden, Instance } from "../models/brewtils-types";
import {
  DeleteGarden,
  RescanGarden,
  SyncGarden,
  SyncUsersGarden,
  UpdateApiGarden,
} from "../services/garden_service";
import { ClearAllQueues } from "../services/queue_service";
import { Rescan } from "../services/system_service";
import { GetSeverity } from "../services/util_service";

function GardenSummary({
  gardenRef,
  selectedGarden,
}: {
  gardenRef: RefObject<Garden | null>;
  selectedGarden: Garden;
}) {
  const [publishingConnections, setPublishingConnections] = useState<
    Array<Connection>
  >([]);
  const [receivingConnections, setReceivingonnections] = useState<
    Array<Connection>
  >([]);
  const [systemCounts, setSystemCounts] = useState<Map<string, number>>(
    new Map(),
  );

  useEffect(() => {
    if (selectedGarden.publishing_connections) {
      setPublishingConnections(
        selectedGarden.publishing_connections.filter(
          (connection: Connection) => connection.status !== "NOT_CONFIGURED",
        ),
      );
    } else {
      setPublishingConnections([]);
    }
    if (selectedGarden.receiving_connections) {
      setReceivingonnections(
        selectedGarden.receiving_connections.filter(
          (connection: Connection) => connection.status !== "NOT_CONFIGURED",
        ),
      );
    } else {
      setReceivingonnections([]);
    }

    const statusCounts = new Map();

    if (selectedGarden?.systems && selectedGarden.systems.length > 0) {
      for (const system of selectedGarden.systems) {
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
    setSystemCounts(statusCounts);
  }, [selectedGarden]);

  const statusTemplate = (row: any) => {
    const severity = GetSeverity(row.status);

    return <Tag value={row.status} severity={severity} />;
  };

  const connectionActions = (node: Connection, type: string) => (
    <div className="flex gap-2">
      <Button
        onClick={() => {
          if (selectedGarden?.name && node?.status && node?.api) {
            UpdateApiGarden(selectedGarden.name, type, node.api, type).catch(
              (error) => {
                console.error("Error Updating Garden API Connection:", error);
              },
            );
          }
        }}
      >
        <FontAwesomeIcon icon="play" />
      </Button>
      <Button
        severity="warning"
        onClick={() => {
          if (selectedGarden?.name && node?.status && node?.api) {
            UpdateApiGarden(
              selectedGarden.name,
              "DISABLED",
              node.api,
              type,
            ).catch((error) => {
              console.error("Error Updating Garden API Connection:", error);
            });
          }
        }}
      >
        <FontAwesomeIcon icon="stop" />
      </Button>
    </div>
  );

  return (
    <Card className="mb-4" style={{ width: "100%" }} key={selectedGarden?.name}>
      <div className="flex ml-2 page-header">
        <h2 className="flex-1">{`Garden Summary: ${selectedGarden?.name}`}</h2>
        <div>
          <Button
            label="Rescan Plugins"
            className="mr-2"
            onClick={() => {
              if (selectedGarden?.name) {
                Rescan(selectedGarden.name).catch((error) => {
                  console.error("Error Rescanning Garden Plugin Dir:", error);
                });
              }
            }}
          />
          <Button
            label="Rescan Downstream"
            className="mr-2"
            onClick={() => {
              if (selectedGarden?.name) {
                RescanGarden(selectedGarden.name).catch((error) => {
                  console.error("Error Rescanning Garden:", error);
                });
              }
            }}
          />
          <Button
            label="Clear Plugin Queues"
            className="mr-2"
            severity="warning"
            onClick={() => {
              if (selectedGarden?.name) {
                ClearAllQueues(selectedGarden.name).catch((error) => {
                  console.error("Error clearing Plugin Queue:", error);
                });
              }
            }}
          />
          {gardenRef.current &&
            gardenRef.current.name !== selectedGarden?.name && (
              <Button
                label="Sync"
                className="mr-2"
                onClick={() => {
                  if (selectedGarden?.name) {
                    SyncGarden(selectedGarden.name).catch((error) => {
                      console.error("Error Syncing Garden:", error);
                    });
                  }
                }}
              />
            )}
          {gardenRef.current &&
            gardenRef.current.name === selectedGarden?.name && (
              <Button
                label="Sync All"
                className="mr-2"
                onClick={() => {
                  SyncGarden().catch((error) => {
                    console.error("Error Syncing Garden:", error);
                  });
                }}
              />
            )}
          {gardenRef.current &&
            gardenRef.current.name !== selectedGarden?.name && (
              <Button
                label="Sync Users"
                className="mr-2"
                onClick={() => {
                  if (selectedGarden?.name) {
                    SyncUsersGarden(selectedGarden.name).catch((error) => {
                      console.error("Error Syncing Users in Garden:", error);
                    });
                  }
                }}
              />
            )}
          {gardenRef.current &&
            gardenRef.current.name !== selectedGarden?.name && (
              <Button
                label="Delete Garden"
                severity="danger"
                className="mr-2"
                onClick={() => {
                  if (selectedGarden?.name) {
                    DeleteGarden(selectedGarden.name).catch((error) => {
                      console.error("Error Deleting Garden:", error);
                    });
                  }
                }}
              />
            )}
        </div>
      </div>
      <div className="grid">
        <div className="col-3">
          <h4>Version</h4>
          <p>{selectedGarden?.version}</p>
        </div>
        <div className="col-3">
          <h4>Systems</h4>
          {Array.from(systemCounts, ([status, count]) => {
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
          })}
        </div>
        {selectedGarden?.children && selectedGarden?.children.length > 0 && (
          <div className="col-3">
            <h4>Downstream</h4>

            {selectedGarden?.children &&
              selectedGarden?.children.length > 0 && (
                <ul>
                  {" "}
                  {Array.from(
                    selectedGarden.children ?? [],
                    (child: Garden) => {
                      return <li key={child.name}>{child.name}</li>;
                    },
                  )}
                </ul>
              )}
          </div>
        )}
        {selectedGarden?.parent && (
          <div className="col-3">
            <h4>Upstream</h4>
            <ul>
              <li>{selectedGarden?.parent}</li>
            </ul>
          </div>
        )}
      </div>
      <div className="grid">
        {receivingConnections && receivingConnections.length > 0 && (
          <div className="col-4">
            <h4>Receiving</h4>

            <DataTable value={receivingConnections}>
              <Column field="api" header="API" />
              <Column field="status" header="Status" body={statusTemplate} />
              <Column
                header="Actions"
                body={(node: any) => connectionActions(node, "RECEIVING")}
              />
            </DataTable>
          </div>
        )}

        {publishingConnections && publishingConnections.length > 0 && (
          <div className="col-4">
            <h4>Publishing</h4>
            <DataTable value={publishingConnections}>
              <Column field="api" header="API" />
              <Column field="status" header="Status" body={statusTemplate} />
              <Column
                header="Actions"
                body={(node: any) => connectionActions(node, "PUBLISHING")}
              />
            </DataTable>
          </div>
        )}
      </div>
    </Card>
  );
}

export default GardenSummary;
