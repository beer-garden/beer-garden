import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Badge } from "primereact/badge";
import { Button } from "primereact/button";
import { Card } from "primereact/card";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { Skeleton } from "primereact/skeleton";
import { Tag } from "primereact/tag";
import { RefObject, useEffect, useState } from "react";

import HasAccess from "../components/HasAccess";
import { Connection, Garden, Runner, System } from "../models/brewtils-types";
import { Config } from "../models/models";
import { TourStepProps } from "../models/models";
import {
  DeleteGarden,
  RescanGarden,
  SyncGarden,
  SyncUsersGarden,
  UpdateApiGarden,
} from "../services/garden_service";
import { ClearAllQueues } from "../services/queue_service";
import { Rescan } from "../services/system_service";
import {
  AddTourStep,
  ClearTourSteps,
  GenerateTourProps,
} from "../services/tour_service";
import { GenerateStatusCounts, GetSeverity } from "../services/util_service";

function GardenSummary({
  gardenRef,
  selectedGarden,
  selectedSystems,
  associatedRunners,
  tourStepsRef,
  config,
}: {
  gardenRef: RefObject<Garden | undefined>;
  selectedGarden: Garden | undefined;
  selectedSystems: System[] | undefined;
  associatedRunners: RefObject<Runner[] | undefined>;
  tourStepsRef?: RefObject<Array<TourStepProps>>;
  config: Config;
}) {
  const tourUuid = selectedGarden?.id;
  const tourPrefix = "garden_summary";
  const getPublishingConnections = () => {
    if (selectedGarden?.publishing_connections) {
      return selectedGarden.publishing_connections.filter(
        (connection: Connection) => connection.status !== "NOT_CONFIGURED",
      );
    } else {
      return [];
    }
  };

  const getReceivingConnections = () => {
    if (selectedGarden?.receiving_connections) {
      return selectedGarden.receiving_connections.filter(
        (connection: Connection) => connection.status !== "NOT_CONFIGURED",
      );
    } else {
      return [];
    }
  };

  const getSystemCounts = () => {
    if (selectedGarden) {
      return GenerateStatusCounts(
        gardenRef,
        associatedRunners,
        selectedGarden,
        selectedSystems,
      );
    }

    return new Map();
  };

  const [publishingConnections, setPublishingConnections] = useState<
    Array<Connection>
  >(getPublishingConnections());
  const [receivingConnections, setReceivingonnections] = useState<
    Array<Connection>
  >(getReceivingConnections());
  const [systemCounts, setSystemCounts] =
    useState<Map<string, number>>(getSystemCounts());

  const rescanPluginTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Rescan Plugins",
    content: "Rescan the plugins for the selected garden",
    layer: "COMPONENT",
    pos: 0,
  };
  const rescanDownstreamTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Rescan Downstream",
    content: "Rescan the downstream connections for the selected garden",
    layer: "COMPONENT",
    pos: 1,
  };

  const clearPluginsQueuesTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Clear Plugin Queues",
    content: "Clear all plugin queues for the selected garden",
    layer: "COMPONENT",
    pos: 2,
  };

  const syncGardenTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Sync",
    content: "Sync the selected garden with its upstream gardens",
    layer: "COMPONENT",
    pos: 3,
  };

  const syncAllTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Sync All",
    content: "Sync all gardens with their upstream gardens",
    layer: "COMPONENT",
    pos: 4,
  };

  const syncUsersTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Sync Users",
    content: "Sync users in the selected garden with its upstream garden",
    layer: "COMPONENT",
    pos: 5,
  };

  const deleteGardenTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Delete Garden",
    content: "Delete the selected garden. This action is irreversible.",
    layer: "COMPONENT",
    pos: 6,
  };

  useEffect(() => {
    setPublishingConnections(getPublishingConnections());
    setReceivingonnections(getReceivingConnections());
    setSystemCounts(getSystemCounts());

    if (tourStepsRef !== undefined) {
      ClearTourSteps(tourStepsRef, tourPrefix, tourUuid);

      AddTourStep(tourStepsRef, rescanPluginTourStep);
      AddTourStep(tourStepsRef, rescanDownstreamTourStep);
      AddTourStep(tourStepsRef, clearPluginsQueuesTourStep);

      if (gardenRef.current) {
        if (gardenRef.current.name === selectedGarden?.name) {
          AddTourStep(tourStepsRef, syncAllTourStep);
        } else {
          AddTourStep(tourStepsRef, syncGardenTourStep);
          AddTourStep(tourStepsRef, syncUsersTourStep);
          AddTourStep(tourStepsRef, deleteGardenTourStep);
        }
      }

      if (selectedGarden?.receiving_connections) {
        selectedGarden.receiving_connections.forEach(
          (connection: Connection) => {
            if (connection.status !== "NOT_CONFIGURED") {
              AddTourStep(tourStepsRef, {
                prefix: tourPrefix,
                uuid: tourUuid,
                label: `RECEIVING START ${connection.api}`,
                content: `Start receiving connection for ${connection.api}`,
                layer: "COMPONENT",
                pos: 7,
              });
              AddTourStep(tourStepsRef, {
                prefix: tourPrefix,
                uuid: tourUuid,
                label: `RECEIVING STOP ${connection.api}`,
                content: `Stop receiving connection for ${connection.api}`,
                layer: "COMPONENT",
                pos: 8,
              });
            }
          },
        );
      }

      if (selectedGarden?.publishing_connections) {
        selectedGarden.publishing_connections.forEach(
          (connection: Connection) => {
            if (connection.status !== "NOT_CONFIGURED") {
              AddTourStep(tourStepsRef, {
                prefix: tourPrefix,
                uuid: tourUuid,
                label: `PUBLISHING START ${connection.api}`,
                content: `Start publishing connection for ${connection.api}`,
                layer: "COMPONENT",
                pos: 9,
              });
              AddTourStep(tourStepsRef, {
                prefix: tourPrefix,
                uuid: tourUuid,
                label: `PUBLISHING STOP ${connection.api}`,
                content: `Stop publishing connection for ${connection.api}`,
                layer: "COMPONENT",
                pos: 10,
              });
            }
          },
        );
      }

      return () => {
        ClearTourSteps(tourStepsRef, tourPrefix, tourUuid);
      };
    }
  }, [selectedGarden, selectedSystems]);

  const statusTemplate = (row: any) => {
    const severity = GetSeverity(row.status);

    return <Tag value={row.status} severity={severity} />;
  };

  const connectionActions = (node: Connection, type: string) => (
    <HasAccess
      config={config}
      permission="GARDEN_ADMIN"
      hasGardenName={selectedGarden?.name}
    >
      <div className="flex gap-2">
        <Button
          data-testid={type + "_" + node?.api + "_START"}
          {...GenerateTourProps({
            prefix: tourPrefix,
            uuid: tourUuid,
            label: `${type} START ${node?.api}`,
          })}
          onClick={() => {
            if (selectedGarden?.name && node?.status && node?.api) {
              UpdateApiGarden(selectedGarden.name, type, node.api, type).catch(
                (error) => {
                  console.error("Error Updating Garden API Connection:", error);
                },
              );
            } else if (node?.api === null || node?.api === undefined) {
              throw Error(`Error missing ${JSON.stringify(node)}`);
            }
          }}
        >
          <FontAwesomeIcon icon="play" />
        </Button>
        <Button
          severity="warning"
          data-testid={type + "_" + node?.api + "_STOP"}
          {...GenerateTourProps({
            prefix: tourPrefix,
            uuid: tourUuid,
            label: `${type} STOP ${node?.api}`,
          })}
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
    </HasAccess>
  );

  return (
    <Card
      className="mb-4"
      style={{ width: "100%" }}
      unstyled
      key={selectedGarden?.name}
    >
      <div className="flex ml-2 page-header">
        <h2 className="flex-1">
          {selectedGarden?.name
            ? `Garden Summary: ${selectedGarden?.name}`
            : "Garden Summary"}
        </h2>
        {selectedGarden?.name && (
          <HasAccess
            config={config}
            permission="GARDEN_ADMIN"
            hasGardenName={selectedGarden?.name}
          >
            <div>
              <Button
                {...GenerateTourProps(rescanPluginTourStep)}
                label="Rescan Plugins"
                data-testid={"RESCAN_PLUGINS"}
                className="mr-2"
                onClick={() => {
                  if (selectedGarden?.name) {
                    Rescan(selectedGarden.name).catch((error) => {
                      console.error(
                        "Error Rescanning Garden Plugin Dir:",
                        error,
                      );
                    });
                  }
                }}
              />
              <Button
                label="Rescan Downstream"
                {...GenerateTourProps(rescanDownstreamTourStep)}
                data-testid={"RESCAN_DOWNSTREAM"}
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
                {...GenerateTourProps(clearPluginsQueuesTourStep)}
                data-testid={"CLEAR_PLUGIN_QUEUES"}
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
                    {...GenerateTourProps(syncGardenTourStep)}
                    data-testid={"SYNC_GARDEN"}
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
                    {...GenerateTourProps(syncAllTourStep)}
                    data-testid={"SYNC_ALL"}
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
                    {...GenerateTourProps(syncUsersTourStep)}
                    data-testid={"SYNC_USERS"}
                    className="mr-2"
                    onClick={() => {
                      if (selectedGarden?.name) {
                        SyncUsersGarden(selectedGarden.name).catch((error) => {
                          console.error(
                            "Error Syncing Users in Garden:",
                            error,
                          );
                        });
                      }
                    }}
                  />
                )}
              {gardenRef.current &&
                gardenRef.current.name !== selectedGarden?.name && (
                  <Button
                    label="Delete Garden"
                    {...GenerateTourProps(deleteGardenTourStep)}
                    data-testid={"DELETE_GARDEN"}
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
          </HasAccess>
        )}
      </div>
      {selectedGarden?.name ? (
        <div>
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
                      data-testid={`${status}_severity_system_summary`}
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
            {selectedGarden?.children &&
              selectedGarden?.children.length > 0 && (
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
                  <Column
                    field="status"
                    header="Status"
                    body={statusTemplate}
                  />
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
                  <Column
                    field="status"
                    header="Status"
                    body={statusTemplate}
                  />
                  <Column
                    header="Actions"
                    body={(node: any) => connectionActions(node, "PUBLISHING")}
                  />
                </DataTable>
              </div>
            )}
          </div>
        </div>
      ) : (
        <>
          <Skeleton width="100%" height="200px" className="mb-2"></Skeleton>
          <Skeleton width="100%" height="300px"></Skeleton>
        </>
      )}
    </Card>
  );
}

export default GardenSummary;
