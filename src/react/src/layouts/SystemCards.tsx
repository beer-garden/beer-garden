import "primeflex/primeflex.css";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Badge } from "primereact/badge";
import { Button } from "primereact/button";
import { ConfirmDialog, confirmDialog } from "primereact/confirmdialog";
import { DataView } from "primereact/dataview";
import { Menu } from "primereact/menu";
import { MenuPassThroughMethodOptions } from "primereact/menu";
import { Panel } from "primereact/panel";
import { Toast } from "primereact/toast";
import { classNames } from "primereact/utils";
import { useEffect, useRef, useState } from "react";

import InstanceCancelDeleteDialog from "../components/InstanceCancelDeleteRequestsDialog";
import InstanceManageQueueDialog from "../components/InstanceManageQueueDialog";
import InstanceShowLogsDialog from "../components/InstanceShowLogsDialog";
import { Instance, System } from "../models/brewtils-types";
import { StartInstance, StopInstance } from "../services/instance_service";
import { ClearAllQueues } from "../services/queue_service";
import { PushToScratchPad } from "../services/scratchpad_service";
import {
  DeleteSystem,
  GetSystemList,
  ReloadSystem,
  Rescan,
} from "../services/system_service";

function SystemCards({
  listeners,
  setReloadScratchPad,
}: {
  listeners: Record<string, any>;
  setReloadScratchPad: any;
}) {
  const [systems, setSystems] = useState<Array<System>>([]);

  const MonitorSystemEvents = (message: any) => {
    if (message.name == "SYSTEM_CREATED") {
      setSystems((prevSystems) => {
        return [...prevSystems, message.payload];
      });
      const sessSystems = sessionStorage.getItem("systems");
      if (sessSystems) {
        const jsonSystems = JSON.parse(sessSystems);
        const newSystems = [...jsonSystems, message.payload];
        sessionStorage.setItem("systems", JSON.stringify(newSystems));
      }
    } else if (message.name == "SYSTEM_UPDATED") {
      setSystems((prevSystems) => {
        const newSystems = prevSystems.map((system) => {
          if (system.id == message.payload.id) {
            system = message.payload;
          }
          return { ...system };
        });
        return newSystems;
      });
      const sessSystems = sessionStorage.getItem("systems");
      if (sessSystems) {
        const jsonSystems = JSON.parse(sessSystems);
        const newSessSystems = jsonSystems.map((system: System) => {
          if (system.id == message.payload.id) {
            system = message.payload;
          }
          return { ...system };
        });
        sessionStorage.setItem("systems", JSON.stringify(newSessSystems));
      }
    } else if (message.name == "SYSTEM_REMOVED") {
      setSystems((prevSystems) => {
        return prevSystems.filter((s) => s.id != message.payload.id);
      });
      const sessSystems = sessionStorage.getItem("systems");
      if (sessSystems) {
        const jsonSystems = JSON.parse(sessSystems);
        sessionStorage.setItem(
          "systems",
          JSON.stringify(
            jsonSystems.filter((s: System) => s.id != message.payload.id),
          ),
        );
      }
    } else if (
      message.name == "INSTANCE_STARTED" ||
      message.name == "INSTANCE_STOPPED" ||
      message.name == "INSTANCE_UPDATED" ||
      message.name == "INSTANCE_INITIALIZED"
    ) {
      setSystems((prevSystems) => {
        const newSystems = prevSystems.map((system) => {
          system.instances?.map((instance) => {
            if (instance.id == message.payload.id) {
              instance.status = message.payload.status;
            }
          });
          return { ...system };
        });
        return newSystems;
      });
      const sessSystems = sessionStorage.getItem("systems");
      if (sessSystems) {
        const jsonSystems = JSON.parse(sessSystems);
        const newSessSystems = jsonSystems.map((system: System) => {
          system.instances?.map((instance: Instance) => {
            if (instance.id == message.payload.id) {
              instance.status = message.payload.status;
            }
          });
          return { ...system };
        });
        sessionStorage.setItem("systems", JSON.stringify(newSessSystems));
      }
    }
  };

  useEffect(() => {
    GetSystemList()
      .then((data: Array<System>) => {
        setSystems(data);
        listeners["SYSTEM_EVENTS"] = {
          listener: MonitorSystemEvents,
        };
      })
      .catch((error) => {
        console.error("Error fetching systems:", error);
      });
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

  const systemTemplateGrid = (system: System) => {
    if (!system) {
      return;
    }

    const statusCounts = new Map();

    statusList.forEach((status) => {
      // statusCounts[status] = {count: 0, severity:getSeverity(status)}
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
            toast.current?.show({
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

    const PushToPad = (system: System) => {
      if (system) {
        PushToScratchPad("SYSTEM_VIEW", {
          systemId: system.id,
          system: system,
        });
        setReloadScratchPad(new Date());
      }
    };

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

      console.log(options.togglerElement);
      const toggleIcon = collapsed ? (
        <FontAwesomeIcon icon="plus" />
      ) : (
        <FontAwesomeIcon icon="minus" />
      );

      return (
        <div className={className}>
          <div className="flex align-items-center gap-2">
            <label className="max-w-10rem">
              {system.name}/ {system.version}
            </label>
            <Button
              rounded
              raised
              link
              onClick={() => PushToPad(system)}
              tooltip={"Push to Pad " + system.name}
            >
              <FontAwesomeIcon icon="arrow-right-from-bracket" />{" "}
            </Button>

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
              data-testid={`system-menu-${system.name}`}
              pt={{
                menuitem: ({ context }: MenuPassThroughMethodOptions) => ({
                  "data-testid": `system-menu-item-${system.name}-${context.item.label}`,
                }),
                action: ({ context }: MenuPassThroughMethodOptions) => ({
                  "data-testid": `system-menu-item-action-${system.name}-${context.item.label}`,
                }),
              }}
            />
            <button
              className="p-panel-header-icon p-link mr-2"
              data-testid={`system-menu-${system.name}-button`}
              onClick={(e) => systemConfigMenu?.current?.toggle(e)}
            >
              <FontAwesomeIcon icon="cog" />
            </button>
            <Button
              icon={toggleIcon}
              className="p-panel-header-icon p-panel-toggler p-link"
              onClick={togglePanel}
              aria-label="Toggle Panel"
              data-testid={`panel-toggler-${system.name}-button`}
            />
            {/* {options.togglerElement} */}
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
        <div
          className="col-12"
          key={instance.id}
          data-testid={`instance-template-${system.name}`}
        >
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
                    data-testid={`instance-menu-${instance.name}`}
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

    const [collapsed, setCollapsed] = useState(true);

    const togglePanel = () => {
      setCollapsed(!collapsed);
    };

    return (
      <Panel
        headerTemplate={headerTemplate}
        key={system.id}
        className="m-2"
        style={{ width: "20%" }}
        collapsed={collapsed}
        onToggle={(e) => setCollapsed(e.value)} // Keep onToggle for internal panel logic/accessibility
        toggleable
      >
        <p className="m-0">{system.description}</p>
        <DataView
          value={system.instances}
          listTemplate={instanceListTemplate}
        />
      </Panel>
    );
  };

  const systemListTemplate = (systems: System[]) => {
    if (!Array.isArray(systems) && typeof systems === "object") {
      const newSystems = [] as System[];
      Object.values(systems).forEach((system) => {
        newSystems.push(system as System);
      });
      systems = newSystems;
    }
    return (
      <div
        className="grid grid-nogutter"
        style={{ gridTemplateColumns: `repeat(auto-fit, minmax(250px, 1fr))` }}
      >
        {systems.map((system) => systemTemplateGrid(system))}
      </div>
    );
  };

  const systemGroup = new Map<string, System[]>();

  const groupField = "namespace";
  // const groupField = "version";
  systems.forEach((system) => {
    systemGroup.set(system[groupField] as string, [
      ...(systemGroup.get(system[groupField] as string) || []),
      ...[system],
    ]);
  });

  const groupHeaderTemplate = (options: any) => {
    const className = `${options.className} justify-content-space-between`;

    const statusCounts = new Map();

    statusList.forEach((status) => {
      // statusCounts[status] = {count: 0, severity:getSeverity(status)}
      statusCounts.set(status, 0);
    });
    const groupSystems = systemGroup.get(options.props.title) || [];
    groupSystems.forEach((system: System) => {
      system?.instances?.forEach((instance) => {
        if (instance.status) {
          statusCounts.set(
            instance.status,
            (statusCounts.get(instance.status) || 0) + 1,
          );
        }
      });
    });

    return (
      <div className={className}>
        <div className="flex align-items-center gap-2">
          <label>{options.props.title}</label>

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
        <div>{options.togglerElement}</div>
      </div>
    );
  };

  // Toast ref
  const toast = useRef<Toast>(null);

  function handleClearAllQueues() {
    const accept = () => {
      toast.current?.show({
        severity: "info",
        summary: "Confirmation",
        detail: "Clearing All Queues",
        life: 3000,
      });
      void ClearAllQueues();
    };

    const reject = () => {};

    const confirm = () => {
      confirmDialog({
        message: "Are you sure you want to delete all Queues?",
        header: "Confirmation",
        icon: "pi pi-exclamation-triangle",
        defaultFocus: "accept",
        accept,
        reject,
      });
    };

    confirm();
  }

  const handleRescan = () => {
    Rescan()
      .then(() => {
        toast.current?.show({
          severity: "info",
          summary: "Confirmation",
          detail: "Rescan complete",
          life: 3000,
        });
      })
      .catch((error) => {
        console.error("Error deleting system:", error);
      });
  };

  return (
    <>
      <div className="flex items-end ml-2 page-header">
        <h1 className="flex-1">Systems Management</h1>
        <div>
          <Toast ref={toast} />
          <ConfirmDialog />
          <Button onClick={handleClearAllQueues} label="Clear All Queues" />
          <Button onClick={handleRescan} label="Rescan Plugin Directory" />
        </div>
      </div>
      <div>
        {Array.from(systemGroup, ([group, groupedSystems]) => (
          <Panel
            headerTemplate={groupHeaderTemplate}
            toggleable
            // collapsed
            title={group}
            key={group}
            className="m-2"
            style={{ width: "100%" }}
          >
            <DataView
              value={groupedSystems}
              listTemplate={systemListTemplate}
              layout="grid"
            />
          </Panel>
        ))}
      </div>
    </>
  );
}
export default SystemCards;
