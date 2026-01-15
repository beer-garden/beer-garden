import { useState, useEffect } from "react";
import { Connection, Garden } from "../models/brewtils-types";
import { OrganizationChart } from "primereact/organizationchart";
import { GetRootGarden } from "../services/garden_service";
import { GetConfig } from "../services/config_service";
import { SplitButton } from "primereact/splitbutton";
import { MenuItem } from "primereact/menuitem";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { DataView } from "primereact/dataview";

function GardenIndex() {
  const [garden, setGarden] = useState<Garden | null>(null);
  const [gardenNode, setGardenNode] = useState<any>([{}]);

  const mapNode = (garden: Garden) => {
    let node = {
      label: garden.name as string,
      expanded: true,
      children: [] as Array<any>,
    };

    if (garden.children) {
      garden.children.forEach((childGarden: Garden) => {
        node.children.push(mapNode(childGarden));
      });
    }
    return node;
  };
  useEffect(() => {
    if (garden) {
      setGardenNode([mapNode(garden)]);
    }
  }, [garden]);

  useEffect(() => {
    GetConfig().then((config) => {
      GetRootGarden(config, {}).then((response_garden: Garden) => {
        setGarden(response_garden);
      });
    });
  }, []);

  const connectionTemplate = (connection: Connection, index: number) => {
    return <div></div>;
  };

  const connectionsListTemplate = (connections: Array<Connection>) => {
    if (!connections || connections.length === 0) return null;

    let list = connections.map((connection, index) => {
      return connectionTemplate(connection, index);
    });

    return <div className="grid grid-nogutter">{list}</div>;
  };

  const gardenTemplate = (node: any) => {
    const items: MenuItem[] = [];

    items.push({
      label: "Delete",
      icon: <FontAwesomeIcon icon="download" />,
      command: () => {},
    });

    items.push({
      label: "Accept Flow",
      icon: <FontAwesomeIcon icon="download" />,
      command: () => {},
    });

    items.push({
      label: "Block Flow",
      icon: <FontAwesomeIcon icon="download" />,
      command: () => {},
    });

    items.push({
      label: "Info",
      icon: <FontAwesomeIcon icon="download" />,
      command: () => {},
    });

    items.push({
      label: "Rescan Plugins",
      icon: <FontAwesomeIcon icon="download" />,
      command: () => {},
    });

    items.push({
      label: "Rescan Downstream",
      icon: <FontAwesomeIcon icon="download" />,
      command: () => {},
    });

    items.push({
      label: "Clear Plugin Queues",
      icon: <FontAwesomeIcon icon="download" />,
      command: () => {},
    });

    return (
      <div className="flex flex-column align-items-center">
        <label>{node.label}</label>
        <SplitButton
          label="Sync"
          icon="pi pi-plus"
          onClick={() => {}}
          model={items}
        />
      </div>
    );
  };
  return (
    <div>
      <OrganizationChart value={gardenNode} nodeTemplate={gardenTemplate} />
    </div>
  );
}

export default GardenIndex;
