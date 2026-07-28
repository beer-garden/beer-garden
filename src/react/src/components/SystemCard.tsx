import { IconProp } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { ButtonGroup, Chip, MenuItem, Tooltip } from "@mui/material";
import { Menu } from "@mui/material";
import { confirmDialog } from "primereact/confirmdialog";
import { Divider } from "primereact/divider";
import { Panel } from "primereact/panel";
import React, { RefObject, useEffect, useState } from "react";

import AccessButton from "../components/AccessButton";
import InstanceCancelDeleteDialog from "../components/InstanceCancelDeleteRequestsDialog";
import InstanceManageQueueDialog from "../components/InstanceManageQueueDialog";
import InstanceShowLogsDialog from "../components/InstanceShowLogsDialog";
import { Instance, Runner, System } from "../models/brewtils-types";
import { Config, PermissionCheck } from "../models/models";
import { RequestCommand, RequestItem, TourStepProps } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import { StartInstance, StopInstance } from "../services/instance_service";
import { checkPermission } from "../services/permission_service";
import { DeleteSystem, ReloadSystem } from "../services/system_service";
import {
  AddTourStep,
  ClearTourSteps,
  GenerateTourProps,
} from "../services/tour_service";

interface SystemCardProps {
  system: System;
  selectedGarden?: string;
  config: Config;
  tourStepsRef?: RefObject<Array<TourStepProps>>;
  addRequestItem: (itemParams?: Partial<RequestItem>) => void;
  associatedRunners: Runner[];
}

function SystemCard({
  system,
  selectedGarden,
  config,
  tourStepsRef,
  addRequestItem,
  associatedRunners,
}: SystemCardProps) {
  const showSnackbar = useSnackbar();
  const [instanceMenuAnchor, setInstanceMenuAnchor] = useState<
    HTMLElement | undefined
  >(undefined);
  const instanceMenuOpen = Boolean(instanceMenuAnchor);
  const handleInstanceMenuOpen = (
    event: React.MouseEvent<HTMLButtonElement>,
  ) => {
    setInstanceMenuAnchor(event.currentTarget);
  };
  const handleInstanceMenuClose = () => {
    setInstanceMenuAnchor(undefined);
  };

  const [logsVisible, setLogsVisible] = useState(false);
  const closeLogsDialog = () => setLogsVisible(false);
  const [queueVisible, setQueueVisible] = useState(false);
  const closeQueueDialog = () => setQueueVisible(false);
  const [cancelDeleteVisible, setCancelDeleteVisible] = useState(false);
  const closeCancelDeleteDialog = () => setCancelDeleteVisible(false);

  const tourUuid = system.id;
  const tourPrefix = "system_summary";

  const startInstancesTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Start All Instances",
    content: "Start all instances for the selected system",
    layer: "COMPONENT",
    pos: 0,
  };

  const stopInstancesTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Stop All Instances",
    content: "Stop all instances for the selected system",
    layer: "COMPONENT",
    pos: 1,
  };

  const restartSystemTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Restart System",
    content: "Restart the selected system",
    layer: "COMPONENT",
    pos: 2,
  };

  const deleteSystemTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Delete System",
    content: "Delete the selected system",
    layer: "COMPONENT",
    pos: 3,
  };

  const statusInstanceTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: `Instance Status`,
    content: `Status of individual instance`,
    layer: "COMPONENT",
    pos: 4,
  };

  const nameInstanceTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: `Instance Name`,
    content: `Name of individual instance`,
    layer: "COMPONENT",
    pos: 5,
  };

  const startInstanceTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: `Instance Start`,
    content: `Start individual instance`,
    layer: "COMPONENT",
    pos: 6,
  };
  const stopInstanceTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: `Instance Stop`,
    content: `Stop individual instance`,
    layer: "COMPONENT",
    pos: 7,
  };

  useEffect(() => {
    if (tourStepsRef === undefined) {
      return;
    }
    ClearTourSteps(tourStepsRef, tourPrefix, tourUuid);

    AddTourStep(tourStepsRef, startInstancesTourStep);
    AddTourStep(tourStepsRef, stopInstancesTourStep);
    AddTourStep(tourStepsRef, restartSystemTourStep);
    AddTourStep(tourStepsRef, deleteSystemTourStep);

    if (system?.instances && system.instances.length > 0) {
      AddTourStep(tourStepsRef, statusInstanceTourStep);
      AddTourStep(tourStepsRef, nameInstanceTourStep);
      AddTourStep(tourStepsRef, startInstanceTourStep);
      AddTourStep(tourStepsRef, stopInstanceTourStep);
    }
    return () => {
      ClearTourSteps(tourStepsRef, tourPrefix, tourUuid);
    };
  }, [system]);

  const getSeverity = (
    status?: string,
  ): "warning" | "success" | "info" | "error" | "primary" | "secondary" => {
    if (status === "INITIALIZING") {
      return "warning";
    }
    if (status === "RUNNING") {
      return "success";
    }
    if (status === "PAUSED") {
      return "info";
    }
    if (status === "STOPPED") {
      return "info";
    }
    if (status === "DEAD") {
      return "error";
    }
    if (status === "UNRESPONSIVE") {
      return "error";
    }
    if (status === "STARTING") {
      return "warning";
    }
    if (status === "STOPPING") {
      return "warning";
    }
    if (status === "UNKNOWN") {
      return "error";
    }
    if (status === "AWAITING_SYSTEM") {
      return "warning";
    }
    if (status === "ERROR") {
      return "error";
    }
    return "error";
  };

  const statusList = [
    "INITIALIZING",
    "RUNNING",
    "PAUSED",
    "STOPPED",
    "DEAD",
    "UNRESPONSIVE",
    "STARTING",
    "STOPPING",
    "UNKNOWN",
    "AWAITING_SYSTEM",
    "ERROR",
  ] as Array<string>;

  if (!system) {
    return;
  }

  const statusCounts = new Map();

  statusList.forEach((status) => {
    statusCounts.set(status, 0);
  });

  system?.instances?.forEach((instance) => {
    if (instance.status) {
      statusCounts.set(
        instance.status,
        (statusCounts.get(instance.status) || 0) + 1,
      );
    }
  });

  function startSystem(system: System) {
    system.instances?.forEach((instance) => {
      StartInstance(instance, system)
        .then(() => {})
        .catch((error) => {
          console.error("Error starting system:", error);
        });
    });
  }

  function stopSystem(system: System) {
    system.instances?.forEach((instance) => {
      StopInstance(instance, system)
        .then(() => {})
        .catch((error) => {
          console.error("Error stopping system:", error);
        });
    });
  }

  function reloadSystem(system: System) {
    ReloadSystem(system)
      .then(() => {})
      .catch((error) => {
        console.error("Error reloading system:", error);
      });
  }

  function hasRunningInstances(system: System) {
    return system.instances?.some((instance) => {
      return instance.status == "RUNNING";
    });
  }

  function deleteSystem(system: System) {
    const accept = () => {
      DeleteSystem(system)
        .then(() => {
          showSnackbar({
            severity: "info",
            summary: "Confirmation",
            detail: `Deleted system ${system.name}`,
            life: 3000,
          });
        })
        .catch((error) => {
          console.error("Error deleting system:", error);
        });
    };
    const reject = () => {};
    const confirm = () => {
      confirmDialog({
        message:
          "Are you sure you want to delete a system with running instances?",
        header: `Confirm Delete ${system.name}`,
        icon: "pi pi-exclamation-triangle",
        defaultFocus: "accept",
        accept,
        reject,
      });
    };

    if (hasRunningInstances(system)) {
      confirm();
    } else {
      accept();
    }
  }

  function handleStartInstance(instance: Instance, system: System) {
    StartInstance(instance, system)
      .then(() => {})
      .catch((error) => {
        console.error("Error starting instance:", error);
      });
  }

  function handleStopInstance(instance: Instance, system: System) {
    StopInstance(instance, system)
      .then(() => {})
      .catch((error) => {
        console.error("Error deleting stopping instance:", error);
      });
  }

  function statusTemplate(instance: Instance) {
    const statusSeverity = getSeverity(instance.status);

    return (
      <>
        <Tooltip
          title={`Status ${instance.status} for instance ${instance.name} in system ${system.namespace}.${system.name}.${system.version}`}
          placement="bottom"
        >
          <Chip
            label={instance.status}
            color={statusSeverity}
            {...GenerateTourProps(statusInstanceTourStep)}
            id={`status_${instance.id}`}
          />
        </Tooltip>
      </>
    );
  }

  function instanceNameTemplate(instance: Instance) {
    return (
      <div
        style={{ overflowWrap: "break-word", width: "100%" }}
        {...GenerateTourProps(nameInstanceTourStep)}
      >
        {instance.name}
      </div>
    );
  }

  function instanceIconTemplate(instance: Instance) {
    let label = undefined;
    let icon = undefined;

    if (
      instance?.metadata?.runner_id &&
      instance?.metadata?.runner_id.length > 0
    ) {
      for (const runner of associatedRunners) {
        if (runner.id === instance?.metadata?.runner_id) {
          label = `../${runner.path}`;
          if (runner.dead) {
            label = `Subprocess dead: ../${runner.path}`;
            icon = "skull";
          }
        }
      }
      if (system.local && label === undefined) {
        label = "Unable to find Local Runner";
      }
    }

    if (label === undefined) {
      label = "Externally Managed";
    }

    if (icon === undefined) {
      if (instance.status == "UNRESPONSIVE") {
        icon = "triangle-exclamation";
      } else if (instance.status == "AWAITING_SYSTEM") {
        icon = "hourglass";
      } else if (system.local) {
        icon = "folder-open";
      } else {
        icon = "rss";
      }
    }

    return (
      <>
        <Tooltip title={label}>
          <FontAwesomeIcon id={`ICON_${instance.id}`} icon={icon as IconProp} />
        </Tooltip>
      </>
    );
  }

  const instanceActions = (instance: Instance) => {
    if (
      !checkPermission(config, "OPERATOR", {
        gardenName: system.garden_name,
        namespace: system.namespace,
        systemName: system.name,
        systemVersion: system.version,
        instanceName: instance.name,
      } as PermissionCheck)
    ) {
      return <></>;
    }

    const permissions = {
      config: config,
      hasGardenName: system.garden_name,
      hasSystemName: system.name,
      hasSystemVersion: system.version,
      hasNamespace: system.namespace,
      hasInstanceName: instance.name,
    };

    return (
      <div>
        <ButtonGroup>
          <AccessButton
            size="small"
            onClick={() => handleStartInstance(instance, system)}
            title={`Start Instance ${instance.name} in ${system.namespace}.${system.name}.${system.version}`}
            {...GenerateTourProps(startInstanceTourStep)}
            {...permissions}
            raised
            basic
            permission="PLUGIN_ADMIN"
          >
            <FontAwesomeIcon icon="play" />
          </AccessButton>
          <AccessButton
            size="small"
            onClick={() => handleStopInstance(instance, system)}
            title={`Stop Instance ${instance.name} in ${system.namespace}.${system.name}.${system.version}`}
            {...GenerateTourProps(stopInstanceTourStep)}
            {...permissions}
            raised
            basic
            permission="PLUGIN_ADMIN"
          >
            <FontAwesomeIcon icon="stop" />
          </AccessButton>

          <Menu
            id="instance_menu"
            anchorEl={instanceMenuAnchor}
            open={instanceMenuOpen}
            onClose={handleInstanceMenuClose}
          >
            <MenuItem
              onClick={() => {
                handleInstanceMenuClose();
                addRequestItem({
                  type: "REQUEST",
                  requestCommandInput: {
                    namespace: system.namespace,
                    systemName: system.name,
                    version: system.version,
                    instance: instance.name,
                  } as RequestCommand,
                });
              }}
            >
              Create Requests
            </MenuItem>
            {checkPermission(config, "PLUGIN_ADMIN", {
              gardenName: system.garden_name,
              namespace: system.namespace,
              systemName: system.name,
              systemVersion: system.version,
              instanceName: instance.name,
            } as PermissionCheck) && (
              <>
                <MenuItem
                  onClick={() => {
                    handleInstanceMenuClose();
                    setLogsVisible(true);
                  }}
                >
                  Show Logs
                </MenuItem>
                <MenuItem
                  onClick={() => {
                    handleInstanceMenuClose();
                    setQueueVisible(true);
                  }}
                >
                  Manage Queue
                </MenuItem>
                <MenuItem
                  onClick={() => {
                    handleInstanceMenuClose();
                    setCancelDeleteVisible(true);
                  }}
                >
                  Cancel/Delete Requests
                </MenuItem>
              </>
            )}
          </Menu>
          <InstanceShowLogsDialog
            instance={instance}
            system={system}
            isVisible={logsVisible}
            onClose={closeLogsDialog}
          />
          <InstanceManageQueueDialog
            instance={instance}
            system={system}
            isVisible={queueVisible}
            onClose={closeQueueDialog}
          />
          <InstanceCancelDeleteDialog
            instance={instance}
            system={system}
            isVisible={cancelDeleteVisible}
            onClose={closeCancelDeleteDialog}
          />
          <AccessButton
            size="small"
            title={`Admin Tools for ${instance.name}`}
            onClick={handleInstanceMenuOpen}
            {...permissions}
            permission="OPERATOR"
            raised
            basic
          >
            <FontAwesomeIcon icon="bars" />
          </AccessButton>
        </ButtonGroup>
      </div>
    );
  };

  const headerTemplate = (options: any) => {
    const className = `${options.className} justify-content-space-between`;

    return (
      <div className={className}>
        <div className="flex align-items-center gap-2">
          <FontAwesomeIcon
            icon={system.icon_name ? system.icon_name : "gears"}
            aria-label={system.name}
          />
          <span className="max-w-20rem font-semibold">
            {selectedGarden === system.namespace
              ? ""
              : `${system.namespace} / `}
            {system.name} ({system.version})
          </span>
        </div>
      </div>
    );
  };

  const permissions = {
    config: config,
    hasGardenName: system.garden_name,
    hasSystemName: system.name,
    hasSystemVersion: system.version,
    hasNamespace: system.namespace,
  };
  return (
    <>
      <Panel key={system.id} id={system.id} headerTemplate={headerTemplate}>
        <div className="mb-3">
          <div style={{ float: "right", marginLeft: "2px" }}>
            <ButtonGroup>
              <AccessButton
                size="small"
                title={`Start System ${system.namespace}.${system.name}.${system.version}`}
                onClick={() => startSystem(system)}
                {...GenerateTourProps(startInstancesTourStep)}
                {...permissions}
                permission="PLUGIN_ADMIN"
                raised
                basic
              >
                <FontAwesomeIcon icon="play" />
              </AccessButton>
              <AccessButton
                size="small"
                title={`Stop System ${system.namespace}.${system.name}.${system.version}`}
                onClick={() => stopSystem(system)}
                className="mr-2"
                {...GenerateTourProps(stopInstancesTourStep)}
                {...permissions}
                permission="PLUGIN_ADMIN"
                raised
                basic
              >
                <FontAwesomeIcon icon="stop" />
              </AccessButton>
            </ButtonGroup>
            <ButtonGroup>
              <AccessButton
                size="small"
                title={`Reload configuration for System ${system.namespace}.${system.name}.${system.version}`}
                onClick={() => reloadSystem(system)}
                {...GenerateTourProps(restartSystemTourStep)}
                {...permissions}
                permission="PLUGIN_ADMIN"
                raised
                basic
              >
                <FontAwesomeIcon icon="refresh" />
              </AccessButton>

              <AccessButton
                size="small"
                title={`Delete System ${system.namespace}.${system.name}.${system.version}`}
                onClick={() => deleteSystem(system)}
                {...GenerateTourProps(deleteSystemTourStep)}
                {...permissions}
                permission="PLUGIN_ADMIN"
                raised
                basic
              >
                <FontAwesomeIcon icon="trash" />
              </AccessButton>
            </ButtonGroup>
          </div>

          <div style={{ minHeight: "40px" }}>{system.description}</div>
          <Divider className="my-2" style={{ clear: "right" }} />
        </div>
        {system.instances?.map((instance: Instance, index: number) => (
          <div key={JSON.stringify(instance)}>
            <div className="flex flex-wrap justify-content-between align-items-center">
              <div>{instanceIconTemplate(instance)}</div>
              <div>{statusTemplate(instance)}</div>
              <div>{instanceNameTemplate(instance)}</div>
              <div>{instanceActions(instance)}</div>
            </div>
            {index < system.instances!.length - 1 && (
              <Divider className="my-2" />
            )}
          </div>
        ))}
      </Panel>
    </>
  );
}

export default SystemCard;
