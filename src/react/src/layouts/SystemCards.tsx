import "primeflex/primeflex.css";

import { Badge } from "primereact/badge";
import { Button } from "primereact/button";
import { ConfirmDialog, confirmDialog } from "primereact/confirmdialog";
import { DataView } from "primereact/dataview";
import { Panel } from "primereact/panel";
import { Toast } from "primereact/toast";
import { useEffect, useRef, useState } from "react";

import SystemCard from "../components/SystemCard";
import { Instance, System } from "../models/brewtils-types";
import { ClearAllQueues } from "../services/queue_service";
import { GetSystemList, Rescan } from "../services/system_service";

function SystemCards({ listeners }: { listeners: Record<string, any> }) {
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

    return <SystemCard key={system.id} system={system} toast={toast} />;
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
