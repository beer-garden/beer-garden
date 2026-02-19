import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Badge } from "primereact/badge";
import { Button } from "primereact/button";
import { DataView } from "primereact/dataview";
import { Menu } from "primereact/menu";
import { Panel } from "primereact/panel";
import { classNames } from "primereact/utils";
import { useEffect, useRef, useState } from "react";

import { Instance, System } from "../../models/brewtils-types";
import { ScratchPadValue } from "../../models/models";
import { GetSystem } from "../../services/system_service";

function SystemViewCard({
  padItem,
  updatePadItem,
  reloadScratchPad,
  listeners,
}: {
  padItem: ScratchPadValue;
  updatePadItem: (padItem: ScratchPadValue) => void;
  reloadScratchPad: () => void;
  listeners: Record<string, any>;
}) {
  const systemId = useRef<string | null | undefined>(null);
  const [system, setSystem] = useState<System | null>(
    padItem?.values?.system ? padItem.values.system : null,
  );

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

  const updateScratchPadValues = () => {
    updatePadItem({
      ...padItem,
      values: {
        ...padItem.values,
        system: system,
        systemId: systemId,
      },
    });
  };

  const MonitorSystemId = (message: any) => {
    if (message.payload_type === "System") {
      if (
        systemId.current &&
        message.payload.id &&
        message.payload.id === systemId.current
      ) {
        setSystem(message.payload as System);
        updateScratchPadValues();
      }
    }
    if (message.payload_type === "Instance") {
      if (
        system &&
        systemId.current && 
        message.payload.id
      ) {
        if (system.instances) {
          const inst_index = system.instances.findIndex(i => i.id == message.payload.id)
          if (inst_index > -1) {
            // Update on status changes
            if (system.instances[inst_index].status != message.payload.status) {
              system.instances[inst_index] = message.payload as Instance;
              setSystem(system);
              updateScratchPadValues();
              // Must call this to force scratchpad to trigger reload
              reloadScratchPad();
            }
          }
        }
      }
    }
  };

  if (!systemId.current) {
    systemId.current = padItem?.values?.systemId
      ? padItem.values.systemId
      : null;
  }

  useEffect(() => {
    if (!system && systemId.current) {
      GetSystem(systemId.current, {})
        .then((data: System) => {
          setSystem(data);
          updateScratchPadValues();

          if (systemId.current && !(systemId.current in listeners)) {
            listeners[systemId.current] = {
              listener: MonitorSystemId,
            };
          }
        })
        .catch((error) => {
          console.error("Error fetching system:", error);
        });
    }

    if (
      system &&
      systemId.current &&
      !(systemId.current in listeners)
    ) {
      listeners[systemId.current] = {
        listener: MonitorSystemId,
      };
    }

    return () => {
      if (systemId.current) {
        delete listeners[systemId.current];
      }
    };
  }, [system, listeners, padItem, updatePadItem]);

  const systemConfigMenu = useRef<Menu>(null);
  const systemMenuItems = [
    {
      label: "Start",
      icon: <FontAwesomeIcon icon="play" />,
    },
    {
      label: "Stop",
      icon: <FontAwesomeIcon icon="stop" />,
    },
    {
      label: "Restart",
      icon: <FontAwesomeIcon icon="refresh" />,
    },
    {
      separator: true,
    },
    {
      label: "Delete",
      icon: <FontAwesomeIcon icon="trash" />,
    },
  ];

  const instanceTemplate = (instance: Instance, index: number) => {
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
              <Button className="mr-2">
                <FontAwesomeIcon icon="play" />
              </Button>
              <Button className="mr-2">
                <FontAwesomeIcon icon="stop" />
              </Button>
              <Button className="mr-2">
                <FontAwesomeIcon icon="file-lines" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const instanceListTemplate = (instances: System[]) => {
    if (!instances || instances.length === 0) return null;

    const list = instances.map((instance: Instance, index: number) => {
      return instanceTemplate(instance, index);
    });

    return <div className="grid grid-nogutter">{list}</div>;
  };

  const headerTemplate = (options: any) => {
    const className = `${options.className} justify-content-space-between`;

    return (
      <div className={className}>
        <div className="flex align-items-center gap-2">
          <label className="max-w-10rem">
            {system?.name}/ {system?.version}
          </label>

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

  return (
    <Panel
      headerTemplate={headerTemplate}
      key={system?.id}
      className="flex-1 m-2"
      toggleable
      collapsed
    >
      <p className="m-0">{system?.description}</p>
      <DataView value={system?.instances} listTemplate={instanceListTemplate} />
    </Panel>
  );
}

export default SystemViewCard;
