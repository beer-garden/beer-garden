import { Button } from "primereact/button";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { Stepper } from "primereact/stepper";
import { RefObject, useEffect, useState } from "react";

import { System } from "../models/brewtils-types";
import { GetSystemList } from "../services/system_service";

function SystemList({
  stepperRef,
  setSelectedSystem,
}: {
  stepperRef: RefObject<Stepper | null>;
  setSelectedSystem: any;
}) {
  const [systems, setSystems] = useState<System[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    GetSystemList()
      .then((systems: System[]) => {
        const sortedSystems = [...systems].sort((a: System, b: System) => {
          if (a?.name && b?.name) {
            return a.name.localeCompare(b.name);
          }
          return 1;
        });
        setSystems(sortedSystems);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error fetching systems:", error);
      });
  }, []);

  function actionTemplate(system: System) {
    return (
      <Button
        onClick={() => {
          setSelectedSystem(system);
          stepperRef.current?.nextCallback();
        }}
      >
        Select
      </Button>
    );
  }

  //Get a list of systems and output them to a table
  return (
    <DataTable value={systems} loading={loading} paginator rows={10}>
      <Column field="namespace" header="Namespace" sortable />
      <Column field="name" header="System Name" sortable />
      <Column field="description" header="Description" sortable />
      <Column field="version" header="Version" sortable />
      <Column header="Actions" body={actionTemplate} />
    </DataTable>
  );
}

export default SystemList;
