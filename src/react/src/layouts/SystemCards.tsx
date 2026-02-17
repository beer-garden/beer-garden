import "primeflex/primeflex.css";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Badge } from "primereact/badge";
import { Button } from "primereact/button";
import { ConfirmDialog, confirmDialog } from "primereact/confirmdialog";
import { DataView } from "primereact/dataview";
import { Menu } from "primereact/menu";
import { Panel } from "primereact/panel";
import { Toast } from "primereact/toast";
import { classNames } from "primereact/utils";
import { useEffect, useRef, useState } from "react";

import { Instance, System } from "../models/brewtils-types";
import { StartInstance, StopInstance } from "../services/instance_service";
import { ClearAllQueues } from "../services/queue_service";
import {
  DeleteSystem,
  GetSystemList,
  ReloadSystem,
  Rescan,
} from "../services/system_service";

function SystemCards() {
  const [systems, setSystems] = useState<Array<System>>([]);
  const [updated, setUpdated] = useState<boolean>(false);

  useEffect(() => {
    GetSystemList()
      .then((data: Array<System>) => {
        console.log(data);
        setSystems(data);
      })
      .catch((error) => {
        console.error("Error fetching systems:", error);
      });
  }, [updated]);

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
        StartInstance(instance, system).then(() => {
          setUpdated(!updated);
        });
      });
    }

    function stopSystem(system: System) {
      system.instances?.forEach((instance) => {
        StopInstance(instance, system).then(() => {
          setUpdated(!updated);
        });
      });
    }

    function reloadSystem(system: System) {
      void ReloadSystem(system).then(() => {
        setUpdated(!updated);
      });
    }

    function hasRunningInstances(system: System) {
      return system.instances?.some((instance) => {
        return instance.status == 'RUNNING';
      });
    };

    function deleteSystem(system: System) {
      const accept = () => {
        DeleteSystem(system).then(() => {
          setUpdated(!updated);
        });
      }
      const reject = () => {}
      const confirm = () => {
        confirmDialog({
            message: 'Are you sure you want to delete a system with running instances?',
            header: 'Confirmation',
            icon: 'pi pi-exclamation-triangle',
            defaultFocus: 'accept',
            accept,
            reject
        });
      };

      if (hasRunningInstances(system)) {
        confirm();
      } else {
        DeleteSystem(system);
      }
    }

    function handleStartInstance(instance: Instance, system: System) {
      StartInstance(instance, system).then(() => {
        setUpdated(!updated);
      });
    }

    function handleStopInstance(instance: Instance, system: System){
      StopInstance(instance, system).then(() => {
        setUpdated(!updated);
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

            {Array.from(statusCounts, ([status, count]) => {
              if (count && count > 0) {
                const statusSeverity = getSeverity(status);
                return (
                  <Badge
                    value={count}
                    severity={statusSeverity}
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
      const statusSeverity = getSeverity(instance?.status);
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
                <Button
                  className="mr-2"
                  title={`Admin Tools for ${instance.name}`}
                >
                  <FontAwesomeIcon icon="bars" />
                </Button>
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
      <Panel
        headerTemplate={headerTemplate}
        key={system.id}
        className="m-2"
        style={{ width: "20%" }}
        toggleable
        collapsed
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
                <Badge value={count} severity={statusSeverity} title={status} />
              );
            }
            return null;
          })}
        </div>
        <div>{options.togglerElement}</div>
      </div>
    );
  };

  // Confirm Dialog visibility
  const [confirmVisible, setConfirmVisible] = useState(false);
  // Toast ref
  const toast = useRef<Toast>(null);

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

  const handleRescan = () => {
    Rescan().then(() => {
      setUpdated(!updated);
    });
  };

  return (
    <>
      <div className="flex items-end ml-2 page-header">
        <h1 className="flex-1">Systems Management</h1>
        <div>
          <Toast ref={toast} />
          <ConfirmDialog />
          <ConfirmDialog
            id="dlg_confirmation"
            visible={confirmVisible}
            onHide={() => setConfirmVisible(false)}
            message="Are you sure you want to delete all Queues?"
            header="Confirmation"
            icon="pi pi-exclamation-triangle"
            accept={accept}
            reject={reject}
          />
          <Button onClick={() => setConfirmVisible(true)} label="Clear All Queues" />
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
