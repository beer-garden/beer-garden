import { FilterMatchMode } from "primereact/api";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { useEffect, useState } from "react";

import { System } from "../models/brewtils-types";
import { useSnackbar } from "../providers/SnackbarProvider";
import { GetSystemList } from "../services/system_service";
import AccessButton from "./AccessButton";

function SystemList({ systemListButtonClick }: { systemListButtonClick: any }) {
  const showSnackbar = useSnackbar();
  const [systems, setSystems] = useState<System[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [filters, setFilters] = useState({
    namespace: {
      value: null,
      matchMode: FilterMatchMode.CONTAINS,
    },
    name: {
      value: null,
      matchMode: FilterMatchMode.CONTAINS,
    },
    description: { value: null, matchMode: FilterMatchMode.CONTAINS },
    version: {
      value: null,
      matchMode: FilterMatchMode.CONTAINS,
    },
  });

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
        showSnackbar({
          severity: "error",
          summary: "Error",
          detail: `Error fetching systems: ${error}`,
          life: 3000,
        });
      });
  }, []);

  function actionTemplate(system: System) {
    return (
      <AccessButton
        tooltip={`Select System ${system.namespace} ${system.name} ${system.version}`}
        onClick={() => {
          systemListButtonClick(system);
        }}
        label="Select"
      >
        Select
      </AccessButton>
    );
  }

  //Get a list of systems and output them to a table
  return (
    <DataTable
      value={systems}
      loading={loading}
      paginator
      rows={10}
      filterDisplay="row"
      filters={filters}
      onFilter={(e) => setFilters(e.filters as typeof filters)}
    >
      <Column field="namespace" header="Namespace" sortable filter />
      <Column field="name" header="System Name" sortable filter />
      <Column field="description" header="Description" sortable filter />
      <Column field="version" header="Version" sortable filter />
      <Column header="Actions" body={actionTemplate} />
    </DataTable>
  );
}

export default SystemList;
