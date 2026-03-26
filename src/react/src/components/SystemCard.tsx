import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Badge } from "primereact/badge";
import { Button } from "primereact/button";
import { confirmDialog } from "primereact/confirmdialog";
import { DataView } from "primereact/dataview";
import { Menu } from "primereact/menu";
import { Panel } from "primereact/panel";
import { Toast } from "primereact/toast";
import { classNames } from "primereact/utils";
import { RefObject, useRef, useState } from "react";

import InstanceCancelDeleteDialog from "../components/InstanceCancelDeleteRequestsDialog";
import InstanceManageQueueDialog from "../components/InstanceManageQueueDialog";
import InstanceShowLogsDialog from "../components/InstanceShowLogsDialog";
import { Instance, System } from "../models/brewtils-types";
import { StartInstance, StopInstance } from "../services/instance_service";
import { DeleteSystem, ReloadSystem } from "../services/system_service";

interface SystemCardProps {
  system: System;
  toast?: RefObject<Toast | null>;
  PushToPad?: any;
}

function SystemCard({ system, toast, PushToPad }: SystemCardProps) {
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

  const headerTemplate = (options: any) => {
    const className = `${options.className} justify-content-space-between`;
    const systemConfigMenu = useRef<Menu>(null);

    const systemMenuItems = [
      {
        label: "Start",
        icon: <FontAwesomeIcon icon="play" />,
        command: () => startSystem(system),
      },
      {
        label: "Stop",
        icon: <FontAwesomeIcon icon="stop" />,
        command: () => stopSystem(system),
      },
      {
        label: "Restart",
        icon: <FontAwesomeIcon icon="refresh" />,
        command: () => reloadSystem(system),
      },
      {
        separator: true,
      },
      {
        label: "Delete",
        icon: <FontAwesomeIcon icon="trash" />,
        command: () => deleteSystem(system),
      },
    ];

    return (
      <div className={className}>
        <div className="flex align-items-center gap-2">
          <label className="max-w-10rem">
            {system.name}/ {system.version}
          </label>
          {PushToPad && (
            <Button
              rounded
              raised
              link
              onClick={() => PushToPad(system)}
              tooltip={"Push to Pad " + system.name}
            >
              <FontAwesomeIcon icon="arrow-right-from-bracket" />{" "}
            </Button>
          )}

          {Array.from(statusCounts, ([status, count]) => {
            if (count && count > 0) {
              const statusSeverity = getSeverity(status);
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
        <div>
          <Menu
            model={systemMenuItems}
            popup
            ref={systemConfigMenu}
            id="config_menu"
          />
          <button
            className="p-panel-header-icon p-link mr-2"
            onClick={(e) => systemConfigMenu?.current?.toggle(e)}
          >
            <FontAwesomeIcon icon="cog" />
          </button>
          {options.togglerElement}
        </div>
      </div>
    );
  };

  const instanceTemplate = (
    system: System,
    instance: Instance,
    index: number,
  ) => {
    const instanceConfigMenu = useRef<Menu>(null);

    const [logsVisible, setLogsVisible] = useState(false);
    const closeLogsDialog = () => setLogsVisible(false);
    const [queueVisible, setQueueVisible] = useState(false);
    const closeQueueDialog = () => setQueueVisible(false);
    const [cancelDeleteVisible, setCancelDeleteVisible] = useState(false);
    const closeCancelDeleteDialog = () => setCancelDeleteVisible(false);

    const statusSeverity = getSeverity(instance?.status);

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
      <div className="col-12" key={instance.id}>
        <div
          className={classNames(
            "flex flex-column xl:flex-row xl:align-items-start p-4 ",
            { "border-top-1 surface-border": index !== 0 },
          )}
        >
          <div className="mt-4">
            <div>
              <FontAwesomeIcon icon="folder" />
              <label>{instance.name}</label>
              <Badge value={instance.status} severity={statusSeverity} />
            </div>
            <div>
              <Button
                className="mr-2"
                title={`Start Instance ${instance.name}`}
                onClick={() => handleStartInstance(instance, system)}
              >
                <FontAwesomeIcon icon="play" />
              </Button>
              <Button
                className="mr-2"
                title={`Stop Instance ${instance.name}`}
                onClick={() => handleStopInstance(instance, system)}
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
                  className="mr-2"
                  title={`Admin Tools for ${instance.name}`}
                  onClick={(e) => instanceConfigMenu?.current?.toggle(e)}
                >
                  <FontAwesomeIcon icon="bars" />
                </Button>
              </>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const instanceListTemplate = (instances: Instance[]) => {
    if (!instances || instances.length === 0) return null;

    const list = instances.map((instance: Instance, index: number) => {
      return instanceTemplate(system, instance, index);
    });

    return <div className="grid grid-nogutter">{list}</div>;
  };

  return (
    <>
      <Panel
        headerTemplate={headerTemplate}
        key={system?.id}
        className="flex-1 m-2"
        toggleable
        collapsed
      >
        <p className="m-0">{system?.description}</p>
        <DataView
          value={system?.instances}
          listTemplate={instanceListTemplate}
        />
      </Panel>
    </>
  );
}

export default SystemCard;
