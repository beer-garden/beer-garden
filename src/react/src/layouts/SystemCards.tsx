import { System, Instance } from "../models/brewtils-types";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "primereact/button";
import { classNames } from "primereact/utils";
import { DataView } from "primereact/dataview";
import "primeflex/primeflex.css";
import { useState, useEffect, useRef } from "react";
import { GetSystemList } from "../services/system_service";
import { Panel } from "primereact/panel";
import { Badge } from "primereact/badge";
import { Menu } from "primereact/menu";

function SystemCards() {
  const [systems, setSystems] = useState<Array<System>>([]);

  useEffect(() => {
    GetSystemList().then((data: Array<System>) => {
      setSystems(data);
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

    let list = instances.map((instance: Instance, index: number) => {
      return instanceTemplate(instance, index);
    });

    return <div className="grid grid-nogutter">{list}</div>;
  };

  const systemTemplateGrid = (system: System, index: number) => {
    if (!system) {
      return;
    }

    let statusCounts = new Map();

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

    const headerTemplate = (options: any) => {
      const className = `${options.className} justify-content-space-between`;

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
        {systems.map((system, index) => systemTemplateGrid(system, index))}
      </div>
    );
  };
  let systemGroup = new Map<string, System[]>();

  const groupField = "namespace";
  // const groupField = "version";
  systems.forEach((system) => {
    systemGroup.set(system[groupField] as string, [
      ...(systemGroup.get(system[groupField] as string) || []),
      ...[system],
    ]);
  });

  let groups = Array(systemGroup.keys()).sort();

  const groupHeaderTemplate = (options: any) => {
    const className = `${options.className} justify-content-space-between`;

    let statusCounts = new Map();

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

  return (
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
  );
}
export default SystemCards;
