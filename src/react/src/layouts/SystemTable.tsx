import "primeflex/primeflex.css";

import { Column } from "primereact/column";
import { TreeTable, TreeTableSelectionEvent } from "primereact/treetable";
import { Children,useEffect, useState } from "react";

import { System } from "../models/brewtils-types";
import { GetSystemList } from "../services/system_service";

function SystemTable() {
  const [systems, setSystems] = useState<Array<System>>([]);
  const [nodes, setNodes] = useState([] as any[]);
  const [selectedNodeKeys, setSelectedNodeKeys] = useState<any | null>(null);

  GetSystemList().then((data: Array<System>) => {
    setSystems(data);
  });

  useEffect(() => {
    const systemNodes: any[] = [];

    if (systems && systems.length > 0) {
      systems.forEach((system) => {
        let systemPos = -1;
        systemNodes.forEach((value, index) => {
          if (value.key === system.name) {
            systemPos = index;
          }
        });
        if (systemPos < 0) {
          systemNodes.push({
            key: system.name,
            data: { name: system.name },
            children: [] as Array<any>,
          });
          systemPos = systemNodes.length - 1;
        }

        let namespaceVersionPos = -1;

        systemNodes[systemPos].children.forEach((value: any, index: any) => {
          if (value.key === system.namespace + "/" + system.version) {
            namespaceVersionPos = index;
          }
        });
        if (namespaceVersionPos < 0) {
          systemNodes[systemPos].children.push({
            key: system.namespace + "/" + system.version,
            data: {
              name: system.namespace + "/" + system.version,
              description: system.description,
            },
            children: [] as Array<any>,
          });
          namespaceVersionPos = systemNodes[systemPos].children.length - 1;
        }
        system.instances?.forEach((instance) => {
          systemNodes[systemPos].children[namespaceVersionPos].children.push({
            key: instance.name,
            data: {
              status: instance.status,
              instance_id: instance.id,
              name: instance.name,
            },
          });
        });
      });
    }

    setNodes(systemNodes);
  }, [systems]);

  return (
    <div className="card">
      <TreeTable
        value={nodes}
        selectionMode="checkbox"
        selectionKeys={selectedNodeKeys}
        onSelectionChange={(e: TreeTableSelectionEvent) =>
          setSelectedNodeKeys(e.value)
        }
        tableStyle={{ minWidth: "50rem" }}
      >
        <Column field="name" header="Name" expander></Column>
        <Column field="description" header="Description"></Column>
        <Column field="status" header="Status"></Column>
      </TreeTable>
    </div>
  );
}
export default SystemTable;
