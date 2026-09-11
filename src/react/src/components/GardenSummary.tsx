import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  Alert,
  Box,
  Chip,
  Divider,
  Grid,
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

  const [invalidRouting, setInvalidRouting] = useState(false);
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

  const apiTemplate = (connection: Connection, type: string) => {
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
        <Tooltip title={url ?? ""}>
          <Box component="span" aria-label={undefined} id={targetId}>
            {connection.api}
          </Box>
        </Tooltip>
      </>
    );
  };

  const statusTemplate = (row: Connection) => {
    const severity = GetSeverity(row.status);

    return <Chip label={row.status} color={severity} />;
  };

  const connectionActions = (node: Connection, type: string) => {
    if (
      gardenRef.current?.name === selectedGarden?.name ||
      (selectedGarden?.has_parent === true &&
        selectedGarden.parent !== undefined &&
        selectedGarden.parent !== gardenRef.current?.name)
    ) {
      return <></>;
    }
    return (
      <Box sx={{ display: "flex", gap: 2 }}>
        <AccessButton
          data-testid={type + "_" + node?.api + "_START"}
          {...GenerateTourProps({
            prefix: tourPrefix,
            uuid: tourUuid,
            label: `${type} START ${node?.api}`,
          })}
          onClick={() => {
            if (selectedGarden?.name && node?.status && node?.api) {
              UpdateApiGarden(selectedGarden.name, type, node.api, type)
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
          tooltip={`${type} START ${node?.api}`}
          config={config}
          permission="GARDEN_ADMIN"
          hasGardenName={selectedGarden?.name}
        >
          <FontAwesomeIcon icon="play" />
        </AccessButton>
        <AccessButton
          color="warning"
          data-testid={type + "_" + node?.api + "_STOP"}
          {...GenerateTourProps({
            prefix: tourPrefix,
            uuid: tourUuid,
            label: `${type} STOP ${node?.api}`,
          })}
          onClick={() => {
            if (selectedGarden?.name && node?.status && node?.api) {
              UpdateApiGarden(selectedGarden.name, "DISABLED", node.api, type)
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
          tooltip={`${type} STOP ${node?.api}`}
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
        <Typography
          variant="h4"
          component="h1"
          sx={{ flexGrow: 1, fontWeight: "bold" }}
        >
          {selectedGarden?.name
            ? `Garden Summary: ${selectedGarden?.name}`
            : "Garden Summary"}
        </Typography>
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
          <Grid container spacing={1}>
            <Grid size={3}>
              <h2>Version</h2>
              <p>{selectedGarden?.version}</p>
            </Grid>
            <Grid size={3}>
              <h2>Systems</h2>
              <Box sx={{ display: "flex" }}>
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
            </Grid>

            {selectedGarden?.children &&
              selectedGarden?.children.length > 0 && (
                <Grid size={3}>
                  <h2>Downstream</h2>

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
                </Grid>
              )}
            {selectedGarden?.parent && (
              <Grid size={3}>
                <h2>Upstream</h2>
                <ul>
                  <li>{selectedGarden?.parent}</li>
                </ul>
              </Grid>
            )}
          </Grid>
          <Grid container spacing={1}>
            {receivingConnections && receivingConnections.length > 0 && (
              <Grid size={4}>
                <h2>Receiving</h2>

                <EnhancedTable
                  data={receivingConnections}
                  displayAll={true}
                  columns={[
                    {
                      id: "api",
                      field: "api",
                      label: "API",
                      template: (row) => apiTemplate(row, "RECEIVING"),
                    },
                    {
                      id: "status",
                      field: "status",
                      label: "Status",
                      template: statusTemplate,
                    },
                    {
                      id: "actions",
                      label: "Actions",
                      template: (node: any) =>
                        connectionActions(node, "RECEIVING"),
                    },
                  ]}
                />
              </Grid>
            )}
            {publishingConnections && publishingConnections.length > 0 && (
              <Grid size={4}>
                <h2>Publishing</h2>
                <EnhancedTable
                  data={publishingConnections}
                  displayAll={true}
                  columns={[
                    {
                      id: "api",
                      field: "api",
                      label: "API",
                      template: (row) => apiTemplate(row, "PUBLISHING"),
                    },
                    {
                      id: "status",
                      field: "status",
                      label: "Status",
                      template: statusTemplate,
                    },
                    {
                      id: "actions",
                      label: "Actions",
                      template: (node: any) =>
                        connectionActions(node, "PUBLISHING"),
                    },
                  ]}
                />
              </Grid>
            )}
          </Grid>
        </div>
      ) : (
        <Skeleton width="100%" height="150px"></Skeleton>
      )}
    </Box>
  );
}

export default GardenSummary;
