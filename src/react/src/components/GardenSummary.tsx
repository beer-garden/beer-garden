import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  Alert,
  Box,
  Chip,
  Divider,
  Skeleton,
  Tooltip,
  Typography,
} from "@mui/material";
import { RefObject, useEffect, useState } from "react";

import EnhancedTable from "../components/EnhancedTable/components/EnhancedTable";
import { Connection, Garden, Runner, System } from "../models/brewtils-types";
import { Config } from "../models/models";
import { TourStepProps } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
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
import {
  FAIcon,
  GenerateStatusCounts,
  GetSeverity,
} from "../services/util_service";
import AccessButton from "./AccessButton";
import { ColumnField } from "./EnhancedTable/models/EnhancedTableModels";

interface GardenConnection {
  garden: string;
  api: string;
  status: string;
  type: string;
  direction: string;
  config?: any;
}

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
  const showSnackbar = useSnackbar();
  const tourUuid = selectedGarden?.id;
  const tourPrefix = "garden_summary";

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

  const getDownstreamConnections = () => {
    const connections = [] as GardenConnection[];

    if (gardenRef?.current?.name === selectedGarden?.name) {
      if (selectedGarden?.receiving_connections) {
        for (const connection of selectedGarden.receiving_connections) {
          if (connection.status !== "NOT_CONFIGURED") {
            connections.push({
              garden: selectedGarden.parent ?? "UPSTREAM",
              api: connection.api,
              status: connection.status,
              type: "RECEIVING",
              direction: "UPSTREAM",
              config: connection.config,
            });
          }
        }
      }

      if (selectedGarden?.publishing_connections) {
        for (const connection of selectedGarden.publishing_connections) {
          if (connection.status !== "NOT_CONFIGURED") {
            connections.push({
              garden: selectedGarden.parent ?? "UPSTREAM",
              api: connection.api,
              status: connection.status,
              type: "PUBLISHING",
              direction: "UPSTREAM",
              config: connection.config,
            });
          }
        }
      }
    }
    if (selectedGarden?.children) {
      for (const child of selectedGarden.children) {
        if (child?.receiving_connections) {
          for (const connection of child.receiving_connections) {
            if (connection.status !== "NOT_CONFIGURED") {
              connections.push({
                garden: child.name,
                api: connection.api,
                status: connection.status,
                type: "RECEIVING",
                direction: "DOWNSTREAM",
                config: connection.config,
              });
            }
          }
        }
        if (child?.publishing_connections) {
          for (const connection of child.publishing_connections) {
            if (connection.status !== "NOT_CONFIGURED") {
              connections.push({
                garden: child.name,
                api: connection.api,
                status: connection.status,
                type: "PUBLISHING",
                direction: "DOWNSTREAM",
                config: connection.config,
              });
            }
          }
        }
      }
    }
    return connections;
  };

  const [invalidRouting, setInvalidRouting] = useState(false);
  const [systemCounts, setSystemCounts] =
    useState<Map<string, number>>(getSystemCounts());

  const [downstreamConnections, setDownstreamConnections] = useState(
    getDownstreamConnections(),
  );

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

  const parentRoutingCheck = (
    garden: Garden,
    targetParent: string,
    upstreamRouting: boolean,
  ) => {
    let isValid = true;

    if (garden.name !== gardenRef.current?.name) {
      isValid =
        garden?.receiving_connections.every(
          (connection: Connection) =>
            connection.status !== undefined &&
            ["NOT_CONFIGURED", "PUBLISHING", "RECEIVING"].includes(
              connection.status,
            ),
        ) &&
        garden?.publishing_connections.every(
          (connection: Connection) =>
            connection.status !== undefined &&
            ["NOT_CONFIGURED", "PUBLISHING", "RECEIVING"].includes(
              connection.status,
            ),
        );
    }
    if (garden.name === targetParent) {
      setInvalidRouting(!(isValid && upstreamRouting));
      return;
    }
    if (garden?.children) {
      for (const child of garden.children) {
        parentRoutingCheck(child, targetParent, isValid && upstreamRouting);
      }
    }
  };

  useEffect(() => {
    setSystemCounts(getSystemCounts());
    setDownstreamConnections(getDownstreamConnections());

    if (tourStepsRef !== undefined) {
      ClearTourSteps(tourStepsRef, tourPrefix, tourUuid);

      AddTourStep(tourStepsRef, rescanPluginTourStep);
      AddTourStep(tourStepsRef, rescanDownstreamTourStep);
      AddTourStep(tourStepsRef, clearPluginsQueuesTourStep);

      if (gardenRef.current) {
        if (gardenRef.current.name === selectedGarden?.name) {
          AddTourStep(tourStepsRef, syncAllTourStep);
        } else {
          if (selectedGarden?.parent) {
            parentRoutingCheck(gardenRef.current, selectedGarden?.parent, true);
          }
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

  const apiTemplate = (connection: GardenConnection, type: string) => {
    let url = "";

    if (connection.config?.host !== undefined) {
      url = url + connection.config?.host;
    }
    if (connection.config?.port !== undefined) {
      url = url + ":" + connection.config?.port;
    }

    if (
      connection.config?.url_prefix !== undefined &&
      connection.config?.url_prefix != null &&
      connection.config?.url_prefix != "" &&
      connection.config?.url_prefix != "/"
    ) {
      url = url + "/" + connection.config?.url_prefix;
    }

    if (type === "RECEIVING") {
      if (connection.config?.subscribe_destination !== undefined) {
        const sub_dest = connection.config?.subscribe_destination.replace(
          /^\/+/,
          "",
        );
        url = url.replace(/\/+$/, "");
        url = url.concat("/", sub_dest);
      }
    } else {
      if (connection.config?.send_destination !== undefined) {
        const send_dest = connection.config?.send_destination.replace(
          /^\/+/,
          "",
        );
        url = url.replace(/\/+$/, "");
        url = url.concat("/", send_dest);
      }
    }

    const targetId = `Connection_${type}_${connection.api}`;

    return (
      <>
        {connection.api}
        {url.length > 0 && (
          <FAIcon icon="server" title={url} id={targetId} sx={{ ml: 1 }} />
        )}
      </>
    );
  };

  const statusTemplate = (row: GardenConnection) => {
    const severity = GetSeverity(row.status);

    return <Chip label={row.status} color={severity} />;
  };

  const getConnectionColumns = () => {
    const columns = [
      {
        id: "garden",
        field: "garden",
        label: "Garden",
        template: (row) => {
          return (
            <span
              title={
                row.direction === "DOWNSTREAM"
                  ? `Downstream: ${row.garden}\n${selectedGarden?.name} send Operations and accept Events from ${row.garden}`
                  : `Upstream: ${row.garden}\n${selectedGarden?.name} send events to ${row.garden}`
              }
            >
              <FAIcon
                icon={
                  row.direction === "DOWNSTREAM" ? "arrow-down" : "arrow-up"
                }
                sx={{ mr: 2 }}
              />
              {row.garden}
            </span>
          );
        },
      },
      {
        id: "type",
        field: "type",
        label: "Type",
      },
      {
        id: "api",
        field: "api",
        label: "API",
        template: (row) => apiTemplate(row, row.type),
      },
      {
        id: "status",
        field: "status",
        label: "Status",
        template: statusTemplate,
      },
    ] as ColumnField[];

    if (gardenRef?.current?.name === selectedGarden?.name) {
      columns.push({
        id: "actions",
        label: "Actions",
        template: (node: any) => connectionActions(node, node.type),
      });
    }
    return columns;
  };
  const connectionActions = (node: GardenConnection, type: string) => {
    return (
      <Box sx={{ display: "flex", gap: 2 }}>
        <AccessButton
          data-testid={`${node.garden}_${type}_${node?.api}_START`}
          {...GenerateTourProps({
            prefix: tourPrefix,
            uuid: tourUuid,
            label: `${type} START ${node?.api}`,
          })}
          onClick={() => {
            if (node?.status && node?.api) {
              UpdateApiGarden(node.garden, type, node.api, type)
                .then(() => {
                  showSnackbar({
                    severity: "success",
                    summary: "Success",
                    detail: `Stopped Garden API connection ${node.api}`,
                    life: 3000,
                  });
                })
                .catch((error) => {
                  console.error("Error Updating Garden API Connection:", error);
                  showSnackbar({
                    severity: "error",
                    summary: "Error",
                    detail: `Error Updating Garden API Connection: ${error}`,
                    life: 3000,
                  });
                });
            } else if (node?.api === null || node?.api === undefined) {
              throw Error(`Error missing ${JSON.stringify(node)}`);
            }
          }}
          title={
            node.type === "RECEIVING"
              ? node.direction === "DOWNSTREAM"
                ? `Start acceping events from ${node.garden} to ${selectedGarden?.name} over ${node.api}`
                : `Start acceping operation from ${node.garden} to ${selectedGarden?.name} over ${node.api}`
              : node.direction === "DOWNSTREAM"
                ? `Start sending operations from ${selectedGarden?.name} to ${node.garden} over ${node.api}`
                : `Start sending events from ${selectedGarden?.name} to ${node.garden} over ${node.api}`
          }
          config={config}
          permission="GARDEN_ADMIN"
          hasGardenName={selectedGarden?.name}
        >
          <FontAwesomeIcon icon="play" />
        </AccessButton>
        <AccessButton
          color="warning"
          data-testid={`${node.garden}_${type}_${node?.api}_STOP`}
          {...GenerateTourProps({
            prefix: tourPrefix,
            uuid: tourUuid,
            label: `${type} STOP ${node?.api}`,
          })}
          onClick={() => {
            if (node?.status && node?.api) {
              UpdateApiGarden(node.garden, "DISABLED", node.api, type)
                .then(() => {
                  showSnackbar({
                    severity: "success",
                    summary: "Success",
                    detail: `Started Garden API connection ${node.api}`,
                    life: 3000,
                  });
                })
                .catch((error) => {
                  console.error("Error Updating Garden API Connection:", error);
                  showSnackbar({
                    severity: "error",
                    summary: "Error",
                    detail: `Error Updating Garden API Connection: ${error}`,
                    life: 3000,
                  });
                });
            }
          }}
          title={
            node.type === "RECEIVING"
              ? node.direction === "DOWNSTREAM"
                ? `Stop acceping events from ${node.garden} to ${selectedGarden?.name} over ${node.api}`
                : `Stop acceping operation from ${node.garden} to ${selectedGarden?.name} over ${node.api}`
              : node.direction === "DOWNSTREAM"
                ? `Stop sending operations from ${selectedGarden?.name} to ${node.garden} over ${node.api}`
                : `Stop sending events from ${selectedGarden?.name} to ${node.garden} over ${node.api}`
          }
          config={config}
          permission="GARDEN_ADMIN"
          hasGardenName={selectedGarden?.name}
        >
          <FontAwesomeIcon icon="stop" />
        </AccessButton>
      </Box>
    );
  };

  return (
    <Box sx={{ mb: 4, width: "100%" }} key={selectedGarden?.name}>
      <Box
        sx={{
          display: "flex",
          ml: 1,
          pb: "9px",
          margin: "20px 0 20px",
        }}
      >
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h4" component="h1" sx={{ fontWeight: "bold" }}>
            {selectedGarden?.name
              ? `Garden Summary: ${selectedGarden?.name}`
              : "Garden Summary"}
          </Typography>
          <Box sx={{ display: "flex" }}>
            <Box sx={{ display: "flex", mr: 2 }}>
              <Typography
                variant="subtitle1"
                sx={{ mr: 2, fontWeight: "bold" }}
              >
                Version:
              </Typography>
              <Typography variant="subtitle1">
                {selectedGarden?.version}
              </Typography>
            </Box>
            <Box sx={{ display: "flex" }}>
              <Typography sx={{ mr: 2, fontWeight: "bold" }}>
                Systems:{" "}
              </Typography>
              <Box sx={{ display: "flex", alignItems: "center" }}>
                {Array.from(systemCounts, ([status, count]) => {
                  if (count && count > 0) {
                    const statusSeverity = GetSeverity(status);
                    return (
                      <div key={`${status}_Summary`}>
                        <Tooltip title={`${status} Count ${count}`}>
                          <Box component="span" aria-label={undefined}>
                            <Chip
                              data-testid={`${status}_severity_system_summary`}
                              id={`${status}_${selectedGarden?.id}_severity_system_summary`}
                              label={count}
                              color={statusSeverity}
                              key={status}
                            />
                          </Box>
                        </Tooltip>
                      </div>
                    );
                  }

                  return null;
                })}
              </Box>
            </Box>
          </Box>
        </Box>
        {selectedGarden?.name && (
          <div>
            <AccessButton
              {...GenerateTourProps(rescanPluginTourStep)}
              label="Rescan Plugins"
              tooltip={`Rescan Plugins for Garden ${selectedGarden?.name}`}
              data-testid={"RESCAN_PLUGINS"}
              sx={{ mr: 1 }}
              onClick={() => {
                if (selectedGarden?.name) {
                  Rescan(selectedGarden.name)
                    .then(() => {
                      showSnackbar({
                        severity: "success",
                        summary: "Success",
                        detail: `Rescanned Plugins for Garden ${selectedGarden?.name}`,
                        life: 3000,
                      });
                    })
                    .catch((error) => {
                      console.error(
                        "Error Rescanning Garden Plugin Dir:",
                        error,
                      );
                      showSnackbar({
                        severity: "error",
                        summary: "Error",
                        detail: `Error Rescanning Garden Plugin Dir: ${error}`,
                        life: 3000,
                      });
                    });
                }
              }}
              config={config}
              permission="GARDEN_ADMIN"
              hasGardenName={selectedGarden?.name}
            >
              Rescan Plugins
            </AccessButton>
            <AccessButton
              label="Rescan Downstream"
              tooltip={`Rescan Downstream for Garden ${selectedGarden?.name}`}
              {...GenerateTourProps(rescanDownstreamTourStep)}
              data-testid={"RESCAN_DOWNSTREAM"}
              sx={{ mr: 1 }}
              onClick={() => {
                if (selectedGarden?.name) {
                  RescanGarden(selectedGarden.name)
                    .then(() => {
                      showSnackbar({
                        severity: "success",
                        summary: "Success",
                        detail: `Rescanned Downstream for Garden ${selectedGarden?.name}`,
                        life: 3000,
                      });
                    })
                    .catch((error) => {
                      console.error("Error Rescanning Garden:", error);
                      showSnackbar({
                        severity: "error",
                        summary: "Error",
                        detail: `Error Rescanning Garden: ${error}`,
                        life: 3000,
                      });
                    });
                }
              }}
              config={config}
              permission="GARDEN_ADMIN"
              hasGardenName={selectedGarden?.name}
            >
              Rescan Downstream
            </AccessButton>
            <AccessButton
              label="Clear Plugin Queues"
              tooltip={`Clear Plugin Queues for Garden ${selectedGarden?.name}`}
              {...GenerateTourProps(clearPluginsQueuesTourStep)}
              data-testid={"CLEAR_PLUGIN_QUEUES"}
              sx={{ mr: 1 }}
              color="warning"
              onClick={() => {
                if (selectedGarden?.name) {
                  ClearAllQueues(selectedGarden.name)
                    .then(() => {
                      showSnackbar({
                        severity: "success",
                        summary: "Success",
                        detail: `Cleared Plugin Queues for Garden ${selectedGarden?.name}`,
                        life: 3000,
                      });
                    })
                    .catch((error) => {
                      console.error("Error clearing Plugin Queue:", error);
                      showSnackbar({
                        severity: "error",
                        summary: "Error",
                        detail: `Error clearing Plugin Queue: ${error}`,
                        life: 3000,
                      });
                    });
                }
              }}
              config={config}
              permission="GARDEN_ADMIN"
              hasGardenName={selectedGarden?.name}
            >
              Clear Plugin Queues
            </AccessButton>
            {gardenRef.current &&
              gardenRef.current.name !== selectedGarden?.name && (
                <AccessButton
                  label="Sync"
                  tooltip={`Sync Garden ${selectedGarden?.name}`}
                  {...GenerateTourProps(syncGardenTourStep)}
                  data-testid={"SYNC_GARDEN"}
                  sx={{ mr: 1 }}
                  onClick={() => {
                    if (selectedGarden?.name) {
                      SyncGarden(selectedGarden.name)
                        .then(() => {
                          showSnackbar({
                            severity: "success",
                            summary: "Success",
                            detail: `Synced Garden ${selectedGarden?.name}`,
                            life: 3000,
                          });
                        })
                        .catch((error) => {
                          console.error("Error Syncing Garden:", error);
                          showSnackbar({
                            severity: "error",
                            summary: "Error",
                            detail: `Error Syncing Garden: ${error}`,
                            life: 3000,
                          });
                        });
                    }
                  }}
                  config={config}
                  permission="GARDEN_ADMIN"
                  hasGardenName={selectedGarden?.name}
                >
                  Sync
                </AccessButton>
              )}
            {gardenRef.current &&
              gardenRef.current.name === selectedGarden?.name && (
                <AccessButton
                  label="Sync All"
                  {...GenerateTourProps(syncAllTourStep)}
                  data-testid={"SYNC_ALL"}
                  sx={{ mr: 1 }}
                  onClick={() => {
                    SyncGarden()
                      .then(() => {
                        showSnackbar({
                          severity: "success",
                          summary: "Success",
                          detail: `Synced Garden ${selectedGarden?.name}`,
                          life: 3000,
                        });
                      })
                      .catch((error) => {
                        console.error("Error Syncing Garden:", error);
                        showSnackbar({
                          severity: "error",
                          summary: "Error",
                          detail: `Error Syncing Garden: ${error}`,
                          life: 3000,
                        });
                      });
                  }}
                  config={config}
                  permission="GARDEN_ADMIN"
                  hasGardenName={selectedGarden?.name}
                >
                  Sync All
                </AccessButton>
              )}
            {gardenRef.current &&
              gardenRef.current.name !== selectedGarden?.name && (
                <AccessButton
                  label="Sync Users"
                  tooltip={`Sync Users for Garden ${selectedGarden?.name}`}
                  {...GenerateTourProps(syncUsersTourStep)}
                  data-testid={"SYNC_USERS"}
                  sx={{ mr: 1 }}
                  onClick={() => {
                    if (selectedGarden?.name) {
                      SyncUsersGarden(selectedGarden.name)
                        .then(() => {
                          showSnackbar({
                            severity: "success",
                            summary: "Success",
                            detail: `Synced Users for Garden ${selectedGarden?.name}`,
                            life: 3000,
                          });
                        })
                        .catch((error) => {
                          console.error(
                            "Error Syncing Users in Garden:",
                            error,
                          );
                          showSnackbar({
                            severity: "error",
                            summary: "Error",
                            detail: `Error Syncing Users in Garden: ${error}`,
                            life: 3000,
                          });
                        });
                    }
                  }}
                  config={config}
                  permission="GARDEN_ADMIN"
                  hasGardenName={selectedGarden?.name}
                >
                  Sync Users
                </AccessButton>
              )}
            {gardenRef.current &&
              gardenRef.current.name !== selectedGarden?.name && (
                <AccessButton
                  label="Delete Garden"
                  tooltip={`Delete Garden ${selectedGarden?.name}`}
                  {...GenerateTourProps(deleteGardenTourStep)}
                  data-testid={"DELETE_GARDEN"}
                  color="error"
                  sx={{ mr: 1 }}
                  onClick={() => {
                    if (selectedGarden?.name) {
                      DeleteGarden(selectedGarden.name)
                        .then(() => {
                          showSnackbar({
                            severity: "success",
                            summary: "Success",
                            detail: `Deleted Garden ${selectedGarden?.name}`,
                            life: 3000,
                          });
                        })
                        .catch((error) => {
                          console.error("Error Deleting Garden:", error);
                          showSnackbar({
                            severity: "error",
                            summary: "Error",
                            detail: `Error Deleting Garden: ${error}`,
                            life: 3000,
                          });
                        });
                    }
                  }}
                  config={config}
                  permission="GARDEN_ADMIN"
                  hasGardenName={selectedGarden?.name}
                >
                  Delete Garden
                </AccessButton>
              )}
          </div>
        )}
      </Box>
      <Divider />
      {selectedGarden?.name ? (
        <div>
          {invalidRouting && (
            <Alert
              sx={{
                mx: 1,
                mb: 1,
              }}
              severity="warning"
              icon={
                <FAIcon
                  icon="triangle-exclamation"
                  role="img"
                  aria-label="Warning alert icon"
                />
              }
            >
              Warning - Upstream routing error. Requests or Syncs might be
              interrupted or missed. Please contact your Garden Admin
            </Alert>
          )}
          <Box sx={{ mt: 2 }}>
            {downstreamConnections && downstreamConnections.length > 0 && (
              <EnhancedTable
                data={downstreamConnections}
                groupBy="garden"
                size="small"
                displayAll={true}
                columns={getConnectionColumns()}
              />
            )}
          </Box>
        </div>
      ) : (
        <Skeleton width="100%" height="150px"></Skeleton>
      )}
    </Box>
  );
}

export default GardenSummary;
