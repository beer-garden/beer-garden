import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { DataView } from "primereact/dataview";
import { MenuItem } from "primereact/menuitem";
import { OrganizationChart } from "primereact/organizationchart";
import { Panel } from "primereact/panel";
import { SplitButton } from "primereact/splitbutton";
import { useEffect, useState, useMemo } from "react";
import { DataTable } from "primereact/datatable";
import { Connection, Garden } from "../models/brewtils-types";
import { GetConfig } from "../services/config_service";
import { GetRootGarden } from "../services/garden_service";
import { Button } from "primereact/button";
import { Badge } from "primereact/badge";
import { TreeTable } from "primereact/treetable";
import { Column } from "primereact/column";
import { ColumnGroup } from "primereact/columngroup";
import { Row } from "primereact/row";
import { SelectButton } from "primereact/selectbutton";

function GardenTable() {
  const [garden, setGarden] = useState<Garden | null>(null);
  const [gardenNode, setGardenNode] = useState<any>([{}]);

  function parseGarden(garden: Garden) {
    function findStatus(connections: Array<Connection>, api: string) {
      const matchedAPIs = connections.filter((connection: Connection) => {
        return connection.api?.toLowerCase() === api.toLowerCase();
      });

      if (matchedAPIs && matchedAPIs.length === 1) {
        return matchedAPIs[0].status;
      }
      return null;
    }

    const item = {
      key: garden.id,
      data: {
        id: garden.id,
        name: garden.name,
        version: garden.version,
        http_receiving: findStatus(garden.receiving_connections, "HTTP"),
        http_publishing: findStatus(garden.publishing_connections, "HTTP"),
        stomp_receiving: findStatus(garden.receiving_connections, "STOMP"),
        stomp_publishing: findStatus(garden.publishing_connections, "STOMP"),
        // stomp_receiving: garden.name === "default" ? null : "ERROR",
        // stomp_publishing: garden.name === "default" ? null : "ERROR",
        receiving_connections: garden.receiving_connections,
        publishing_connections: garden.publishing_connections,
      },
      expanded: true,
      children: [] as Array<any>,
    };

    if (
      typeof garden.children !== "undefined" &&
      garden.children !== null &&
      garden.children.length > 0
    ) {
      garden.children.forEach((childGarden: Garden) => {
        const child_item = parseGarden(childGarden);
        child_item.key = item.key + "-" + child_item.key;
        item.children.push(child_item);
      });
    }

    return item;
  }

  useEffect(() => {
    if (garden) {
      if (
      typeof garden.children !== "undefined" &&
      garden.children !== null &&
      garden.children.length > 0
    ) {
      const newGardenNodes = [];
      for (const child of garden.children){
        newGardenNodes.push(parseGarden(child))
      }
      setGardenNode(newGardenNodes);
    }
      // setGardenNode([parseGarden(garden)]);
    }
  }, [garden]);

  useEffect(() => {
    GetConfig()
      .then((config) => {
        GetRootGarden(config, {})
          .then((response_garden: Garden) => {
            setGarden(response_garden);
          })
          .catch((error) => {
            console.error("Error fetching root garden:", error);
          });
      })
      .catch((error) => {
        console.error("Error fetching root garden:", error);
      });
  }, []);

  const connectionTemplate = (node: any, field: string) => {
    if (node.data[field]) {
      const severityLevel = (status: string) => {
        if (["PUBLISHING", "RECEIVING"].includes(status)) {
          return "success";
        }
        if (["DISABLED"].includes(status)) {
          return "warning";
        }
        return "danger";
      };
      return (
        <div>
          <Badge
            className="mr-2"
            value={node.data[field]}
            severity={severityLevel(node.data[field])}
          />
          <Button className="mr-2">
            <FontAwesomeIcon icon="play" />
          </Button>
          <Button className="mr-2">
            <FontAwesomeIcon icon="stop" />
          </Button>
        </div>
      );
    }
  };


  const gardenActionsTemplate = (node: any) => {
    const items: MenuItem[] = [];

    items.push({
      label: "Delete",
      icon: <FontAwesomeIcon icon="download" />,
      command: () => {},
    });

    // items.push({
    //   label: "Info",
    //   icon: <FontAwesomeIcon icon="download" />,
    //   command: () => {},
    // });

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
      <SplitButton
        label="Sync"
        icon="pi pi-plus"
        onClick={() => {}}
        model={items ? items : []}
      />
    );
  };

  const isNestedColumnEmpty = (field: string, nodes: Array<any>) => {
    if (
      nodes.some(
        (garden: any) =>
          garden !== undefined &&
          garden !== null &&
          garden.data !== undefined &&
          garden.data !== null &&
          garden.data[field] !== null &&
          garden.data[field] !== undefined &&
          garden.data[field] !== "",
      )
    ) {
      return false;
    }
    for (const node of nodes) {
      if (node.children && node.children.length > 0) {
        if (!isNestedColumnEmpty(field, node.children)) {
          return false;
        }
      }
    }

    return true;
  };

  const isColumnEmpty = (field: string) => {
    // Returns true if all nodes have null/undefined/empty string for the field

    if (gardenNode && gardenNode.length > 0) {
      if (!isNestedColumnEmpty(field, gardenNode)) {
        return false;
      }
    }
    return true;
  };

  const columns = useMemo(() => {
    const cols = [
      { field: "http_receiving", header: "HTTP Receiving" },
      { field: "http_publishing", header: "HTTP Publishing" },
      { field: "stomp_receiving", header: "STOMP Receiving" },
      { field: "stomp_publishing", header: "STOMP Publishing" },
    ];

    // Filter out columns where isColumnEmpty is true
    return cols.filter((col) => !isColumnEmpty(col.field));
  }, [gardenNode]);

  const header = (<div><Button className="mr-2" label="Sync All"/><Button className="mr-2" label="Rescan Downstream Configurations"/></div>);

  return (
    gardenNode && (
      <TreeTable value={gardenNode} header={header} resizableColumns showGridlines>
        <Column field="name" expander header="Name"></Column>
        <Column field="version" header="Version"></Column>
        <Column body={gardenActionsTemplate} header="Actions"></Column>

        {columns.map((col) => (
          <Column
            key={col.field}
            field={col.field}
            header={col.header}
            body={(node) => connectionTemplate(node, col.field)}
          />
        ))}
      </TreeTable>
    )
  );
}

export default GardenTable;
