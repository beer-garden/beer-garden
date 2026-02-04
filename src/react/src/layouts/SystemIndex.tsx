import "primeflex/primeflex.css";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "primereact/button";
import { Card } from "primereact/card";
import { DataView } from "primereact/dataview";
import { classNames } from "primereact/utils";
import { useEffect,useState } from "react";

import { Instance,System } from "../models/brewtils-types";
import { GetSystemList } from "../services/system_service";

function SystemIndex() {
  const [systems, setSystems] = useState<Array<System>>([]);

  useEffect(() => {
    GetSystemList().then((data: Array<System>) => {
      setSystems(data);
    });
  }, []);

  const instanceTemplate = (instance: Instance, index: number) => {
    return (
      <div className="col-12" key={instance.id}>
        <div
          className={classNames(
            "flex flex-column xl:flex-row xl:align-items-start p-4 gap-4",
            { "border-top-1 surface-border": index !== 0 },
          )}
        >
          <div className="mt-4">
            <FontAwesomeIcon icon="folder" /> {instance.name}
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

  const systemTemplateGrid = (system: System, index: number) => {
    if (!system) {
      return;
    }

    const title =
      system.namespace + " / " + system.name + " / " + system.version;
    return (
      <Card
        title={title}
        key={system.id}
        className="m-2"
        style={{ width: "20%" }}
      >
        <p className="m-0">{system.description}</p>
        <div className="mt-4">
          <Button className="mr-2">
            <FontAwesomeIcon icon="play" />
          </Button>
          <Button className="mr-2">
            <FontAwesomeIcon icon="stop" />
          </Button>
          <Button className="mr-2">
            <FontAwesomeIcon icon="refresh" />
          </Button>
          <Button className="mr-2">
            <FontAwesomeIcon icon="trash" />
          </Button>
          <Button className="mr-2">
            <FontAwesomeIcon icon="file-circle-plus" />
          </Button>
        </div>
        <DataView
          value={system.instances}
          listTemplate={instanceListTemplate}
        />
      </Card>
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

  return (
    <div className="card">
      <DataView
        value={systems}
        listTemplate={systemListTemplate}
        layout="grid"
      />
    </div>
  );
}
export default SystemIndex;
