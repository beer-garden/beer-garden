import React, { Children, useEffect, useRef, useState } from "react";
import { Tree } from "primereact/tree";
import { Card } from "primereact/card";
import { Button } from "primereact/button";
import { Panel } from "primereact/panel";
import { DataTable } from "primereact/datatable";
import { Column } from "primereact/column";
import { Tag } from "primereact/tag";
import { Divider } from "primereact/divider";
import {Instance, System, Connection, Garden} from "../models/brewtils-types";
import {
  DeleteGarden,
  GetRootGarden,
  RescanGarden,
  SyncGarden,
  SyncUsersGarden,
  UpdateApiGarden,
  GetGarden,
} from "../services/garden_service";
import { GetConfig } from "../services/config_service";
import { Badge } from "primereact/badge";

function GardenDashboard() {
  const gardenRef = useRef<Garden>(null);

  const [selectedGarden, setSelectedGarden] = useState<Garden>();

  const [gardenMenu, setGardenMenu] = useState<Array<any>>();

  const findSelectedGarden = (garden_id: string, gardens ?: Array<Garden>) => {

    if (gardens === undefined || gardens === null) {
      if (gardenRef.current){
        findSelectedGarden(garden_id, [gardenRef.current]);
      }
    }
    if (gardens !== undefined){
      for (const garden of gardens){
        if (garden.id === garden_id){
          setSelectedGarden(garden)
          return;
        } else if (garden?.children && garden.children.length > 0){
          findSelectedGarden(garden_id, garden?.children);
        }
      }
    }
  }

  const generateMenu = (garden: Garden) => {
    return {
      key: garden.id,
      label: garden.name,
      icon: "pi pi-sitemap",
      statusCounts: generateStatusCounts(garden),
      connectionCounts : generateConnectionStatus(garden),
      children: (garden?.children && garden.children.length > 0 ? garden.children.map((child: Garden) => generateMenu(child)): [])
    }
  }

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
    if (status === "DISABLED"){
      return "warning";
    }
    if (status === "OPERATIONAL") {
      return "success";
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

  const generateConnectionStatus = (garden: Garden) => {
    const statusCounts = new Map();

    const mapStatus = (status: string) => {
      if (status === "NOT_CONFIGURED"){
        return;
      } else if (["PUBLISHING", "RECEIVING"].includes(status)){  
        statusCounts.set("HEALTHY",(statusCounts.get("HEALTHY") || 0) + 1,);  
      } else {
        statusCounts.set(status,(statusCounts.get(status) || 0) + 1,);
        }
    }

    if (garden.receiving_connections && garden.receiving_connections.length > 0){
      for (const connection of garden.receiving_connections){
        mapStatus(connection.status);
      }
    }

    if (garden.publishing_connections && garden.publishing_connections.length > 0){
      for (const connection of garden.publishing_connections){
        mapStatus(connection.status);
      }
    }
    if (statusCounts.size === 0) {
      return undefined;
    }

    const getConnectionSeverity = (status: string) => {
      if (status === "HEALTHY") {
        return "success";
      }
      if (status === "DISABLED") {
        return "warning";
      }
      return "danger";
    }

    return (Array.from(statusCounts, ([status, count]) => {
                  if (count && count > 0) {
                    const statusSeverity = getConnectionSeverity(status);
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
                }))


  }

  const generateStatusCounts = (garden: Garden) => {
    const statusCounts = new Map();

    
    if (garden?.systems && garden.systems.length > 0){
      for (const system of garden.systems){

        system?.instances?.forEach((instance: Instance) => {
          if (instance.status) {
            statusCounts.set(
              instance.status,
              (statusCounts.get(instance.status) || 0) + 1,
            );
          }
        });
      }
    }

    if (statusCounts.size === 0) {
      return undefined;
    }

    return (Array.from(statusCounts, ([status, count]) => {
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
                }))
  }

  useEffect(() => {
    if (gardenRef.current === null || gardenRef.current === undefined){
      GetConfig()
              .then((config) => {
                GetRootGarden(config, {})
                  .then((response_garden: Garden) => {
                    gardenRef.current = response_garden;
                    setSelectedGarden({...gardenRef.current});
                    setGardenMenu([generateMenu(response_garden)]);
                  })
                  .catch((error) => {
                    console.error("Error fetching root garden:", error);
                  });
              })
              .catch((error) => {
                console.error("Error fetching root garden:", error);
              });
    }
  })


  const statusTemplate = (row: any) => {
    const severity =
      row.status === "Running"
        ? "success"
        : row.status === "Stopped"
        ? "warning"
        : "info";

    return <Tag value={row.status} severity={severity} />;
  };

  const instanceActions = () => (
    <div className="flex gap-2">
      <Button icon="pi pi-play" rounded text severity="success" />
      <Button icon="pi pi-stop" rounded text severity="warning" />
      <Button icon="pi pi-file" rounded text severity="info" />
    </div>
  );

  const connectionActions = () => (
    <div className="flex gap-2">
      <Button label="Start" icon="pi pi-play" size="small" />
      <Button label="Stop" icon="pi pi-stop" severity="warning" size="small" />
    </div>
  );

  const totalInstances =
    selectedGarden?.systems && selectedGarden.systems?.reduce(
      (acc: number, sys: System) => acc + (sys.instances?.length || 0),
      0
    ) || 0;
const [selectedKey, setSelectedKey] = useState<any | null>('');

const gardenTreeNode = (node: any, options: any) => {
  
  return <span className={options.className}><b>{node.label}</b> {node.statusCounts && ("Systems: ")}{node.statusCounts} {node.connectionCounts && ("API: ")}{node.connectionCounts}</span>; 
}
  
return (
    <div className="grid h-screen">

      {/* LEFT NAV TREE */}
      <div className="col-3 surface-border p-3">
        <h3>Select Garden</h3>
        <Tree value={gardenMenu} nodeTemplate={gardenTreeNode} selectionMode="single" selectionKeys={selectedKey} 
          onSelectionChange={(e) => {
            setSelectedKey(e.value);
            if (typeof e.value === 'string'){
              findSelectedGarden(e.value);
            }
            }}/>
            
      </div>

      {/* MAIN WORKSPACE */}
      <div className="col-9 p-4 overflow-auto">

        {/* Garden Summary */}
        <Card title={`Garden Summary: ${selectedGarden?.name}`} className="mb-4">
          <div className="flex gap-2">
              <Button label="Rescan Plugins" icon="pi pi-refresh" />
              <Button label="Sync" icon="pi pi-sync" />
              <Button
                label="Delete Garden"
                icon="pi pi-trash"
                severity="danger"
              />
            </div>
          <div className="grid">
            <div className="col-3">
              <h4>Version</h4>
              <p>{selectedGarden?.version}</p>     
            </div>
            <div className="col-3">
              <h4>Systems</h4>
              {generateStatusCounts(selectedGarden ?? {})}            
            </div>
{selectedGarden?.children && selectedGarden?.children.length > 0 && (
            <div className="col-3">
              <h4>Children</h4>
              
              {selectedGarden?.children && selectedGarden?.children.length > 0 && (<ul> {Array.from(selectedGarden.children ?? [], (child: Garden) => {
                  return (<li>{child.name}</li>);
                })}</ul>)}    
            </div>)}

            {selectedGarden?.receiving_connections && selectedGarden.receiving_connections.length > 0 && (
            <div className="col-3">
              <h4>Receiving</h4>
              {generateConnectionStatus({"receiving_connections": selectedGarden?.receiving_connections} as Garden)}
             
            </div>)}

            {selectedGarden?.publishing_connections && selectedGarden.publishing_connections.length > 0 && (<div className="col-3">
              <h4>Publishing</h4>
              {generateConnectionStatus({"publishing_connections": selectedGarden?.publishing_connections} as Garden)}          
            </div>)}

            

          </div>
        </Card>

        {/* Connections */}
        {((selectedGarden?.publishing_connections && selectedGarden?.publishing_connections.length > 0) || (selectedGarden?.receiving_connections && selectedGarden?.receiving_connections.length > 0)) && (<Panel header="Connections" className="mb-4">
          <div
        className="grid grid-nogutter"

      >
          <Panel
            key="RECEIVING"
            header="RECEIVING"
            className="mb-4"
            style={{width:"50%"}}
          >
            <DataTable
            value={[
              ...(selectedGarden?.receiving_connections.filter((connection: Connection) => connection.status !== "NOT_CONFIGURED") || [])
            ]}
 
          >
            <Column field="api" header="API" />
            <Column field="status" header="Status" body={statusTemplate} />
            <Column header="Actions" body={connectionActions} />
          </DataTable></Panel>
          <Panel
            key="PUBLISHING"
            header="PUBLISHING"
            className="mb-4"
            style={{width:"50%"}}
          ><DataTable
            value={[
              ...(selectedGarden?.publishing_connections.filter((connection: Connection) => connection.status !== "NOT_CONFIGURED") || [])
            ]}

          >
            <Column field="api" header="API" />
            <Column field="status" header="Status" body={statusTemplate} />
            <Column header="Actions" body={connectionActions} />
          </DataTable></Panel>
          </div>
          
        </Panel>)}

        {/* Systems */}
        <div
        className="grid grid-nogutter"
        style={{ gridTemplateColumns: `repeat(auto-fit, minmax(250px, 1fr))` }}
      >
        {selectedGarden?.systems?.map((system: System) => (
          <Panel
            key={system.id}
            header={`${system.name} (${system.version})`}
            className="mb-4"
            toggleable
            style={{width:"33%"}}
          
          >
            <Button
                label="Delete System"
                icon="pi pi-trash"
                severity="danger"
                size="small"
              />
            <div className="flex justify-content-between mb-3">
              <div style={{overflowWrap: "break-word", width: "80%"}}>{system.description}</div>
              
            </div>

            <Divider />

            <DataTable value={system.instances} >
              <Column field="name" header="Instance" />
              <Column field="status" header="Status" body={statusTemplate} />
              <Column header="Actions" body={instanceActions} />
            </DataTable>
          </Panel>
        ))}
        </div>
      </div>
    </div>
  );
}

export default GardenDashboard;