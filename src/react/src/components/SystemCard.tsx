import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "primereact/button";
import { Column } from "primereact/column";
import { confirmDialog } from "primereact/confirmdialog";
import { DataTable } from "primereact/datatable";
import { Menu } from "primereact/menu";
import { Panel } from "primereact/panel";
import { Tag } from "primereact/tag";
import { Toast } from "primereact/toast";
import { RefObject, useEffect, useRef, useState } from "react";

import InstanceCancelDeleteDialog from "../components/InstanceCancelDeleteRequestsDialog";
import InstanceManageQueueDialog from "../components/InstanceManageQueueDialog";
import InstanceShowLogsDialog from "../components/InstanceShowLogsDialog";
import { Instance, System } from "../models/brewtils-types";
import { TourStepProps } from "../models/models";
import { StartInstance, StopInstance } from "../services/instance_service";
import { DeleteSystem, ReloadSystem } from "../services/system_service";
import {
  AddTourStep,
  ClearTourSteps,
  GenerateTourProps,
} from "../services/tour_service";

interface SystemCardProps {
  system: System;
  selectedGarden?: string;
  toast?: RefObject<Toast | null>;
  tourStepsRef: RefObject<Array<TourStepProps>>;
}

function SystemCard({
  system,
  selectedGarden,
  toast,
  tourStepsRef,
}: SystemCardProps) {
  const tourUuid = system.id;
  const tourPrefix = "system_summary";

  const startInstancesTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Start All Instances",
    content: "Start all instances for the selected system",
  };

  const stopInstancesTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Stop All Instances",
    content: "Stop all instances for the selected system",
  };

  const restartSystemTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Restart System",
    content: "Restart the selected system",
  };

  const deleteSystemTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Delete System",
    content: "Delete the selected system",
  };

  const startInstanceTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: `Instance Start`,
    content: `Start individual instance`,
  };
  const stopInstanceTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: `Instance Stop`,
    content: `Stop individual instance`,
  };

  const statusInstanceTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: `Instance Status`,
    content: `Status of individual instance`,
  };

  const nameInstanceTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: `Instance Name`,
    content: `Name of individual instance`,
  };

  useEffect(() => {
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
      if (system?.instances) {
        system.instances.forEach((instance) => {
          ClearTourSteps(tourStepsRef, tourPrefix, instance.id);
        });
      }
    };
  }, []);

  const getSeverity = (
    status?: string,
  ):
    | "warning"
    | "success"
    | "info"
    | "danger"
    | "secondary"
    | "contrast"
    | null
    | undefined => {
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
      return "danger";
    }
    if (status === "UNRESPONSIVE") {
      return "danger";
    }
    if (status === "STARTING") {
      return "warning";
    }
    if (status === "STOPPING") {
      return "warning";
    }
    if (status === "UNKNOWN") {
      return "danger";
    }
    if (status === "AWAITING_SYSTEM") {
      return "warning";
    }
    if (status === "ERROR") {
      return "danger";
    }
    return "danger";
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
          if (toast && toast.current) {
            toast.current?.show({
              severity: "info",
              summary: "Confirmation",
              detail: `Deleted system ${system.name}`,
              life: 3000,
            });
          }
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
      <Tag
        value={instance.status}
        severity={statusSeverity}
        {...GenerateTourProps(statusInstanceTourStep)}
      />
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
  const instanceActions = (instance: Instance) => {
    const instanceConfigMenu = useRef<Menu>(null);

    const [logsVisible, setLogsVisible] = useState(false);
    const closeLogsDialog = () => setLogsVisible(false);
    const [queueVisible, setQueueVisible] = useState(false);
    const closeQueueDialog = () => setQueueVisible(false);
    const [cancelDeleteVisible, setCancelDeleteVisible] = useState(false);
    const closeCancelDeleteDialog = () => setCancelDeleteVisible(false);

    const instanceMenuItems = [
      {
        label: "Show Logs",
        command: () => setLogsVisible(true),
      },
      {
        label: "Manage Queue",
        command: () => setQueueVisible(true),
      },
      {
        label: "Cancel/Delete Requests",
        command: () => setCancelDeleteVisible(true),
      },
    ];

    return (
      <div>
        <Button
          severity="success"
          size="small"
          onClick={() => handleStartInstance(instance, system)}
          {...GenerateTourProps(startInstanceTourStep)}
        >
          <FontAwesomeIcon icon="play" />
        </Button>
        <Button
          severity="warning"
          size="small"
          onClick={() => handleStopInstance(instance, system)}
          {...GenerateTourProps(stopInstanceTourStep)}
        >
          <FontAwesomeIcon icon="stop" />
        </Button>
        <>
          <Menu
            model={instanceMenuItems}
            popup
            ref={instanceConfigMenu}
            id="instance_menu"
          />
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
          <Button
            severity="info"
            size="small"
            title={`Admin Tools for ${instance.name}`}
            onClick={(e) => instanceConfigMenu?.current?.toggle(e)}
          >
            <FontAwesomeIcon icon="bars" />
          </Button>
        </>
      </div>
    );
  };

  const headerTemplate = (options: any) => {
    const className = `${options.className} justify-content-space-between`;

    return (
      <div className={className}>
        <div className="flex align-items-center gap-2">
          <label className="max-w-20rem font-semibold">
            {selectedGarden === system.namespace
              ? ""
              : `${system.namespace} / `}
            {system.name} ({system.version})
          </label>
        </div>
      </div>
    );
  };

  return (
    <>
      <Panel key={system.id} headerTemplate={headerTemplate}>
        <div className="flex justify-content-between mb-3">
          <div
            className="flex-1 mr-2"
            style={{ overflowWrap: "break-word", width: "80%" }}
          >
            {system.description}
          </div>
          <div>
            <Button
              severity="success"
              size="small"
              title="Start"
              onClick={() => startSystem(system)}
              {...GenerateTourProps(startInstancesTourStep)}
            >
              <FontAwesomeIcon icon="play" />
            </Button>
            <Button
              severity="warning"
              size="small"
              title="Stop"
              onClick={() => stopSystem(system)}
              {...GenerateTourProps(stopInstancesTourStep)}
            >
              <FontAwesomeIcon icon="stop" />
            </Button>
            <Button
              severity="info"
              size="small"
              title="Refresh"
              onClick={() => reloadSystem(system)}
              className="mr-2"
              {...GenerateTourProps(restartSystemTourStep)}
            >
              <FontAwesomeIcon icon="refresh" />
            </Button>
            <Button
              severity="danger"
              size="small"
              title="Delete"
              onClick={() => deleteSystem(system)}
              {...GenerateTourProps(deleteSystemTourStep)}
            >
              <FontAwesomeIcon icon="trash" />
            </Button>
          </div>
        </div>
        <DataTable
          value={system.instances}
          key={JSON.stringify(system.instances)}
          size="small"
          className="flex-1"
        >
          <Column
            field="icon"
            header="Icon"
            headerStyle={{ display: "none" }}
            body={<FontAwesomeIcon icon="folder" />}
          />
          <Column
            field="status"
            header="Status"
            headerStyle={{ display: "none" }}
            body={statusTemplate}
          />
          <Column
            field="name"
            header="Instance"
            body={instanceNameTemplate}
            headerStyle={{ display: "none" }}
          />
          <Column
            header="Actions"
            headerStyle={{ display: "none" }}
            style={{ textAlign: "right" }}
            body={instanceActions}
          />
        </DataTable>
      </Panel>
    </>
  );
}

export default SystemCard;
