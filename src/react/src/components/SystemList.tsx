import { useEffect, useState } from "react";

import { System } from "../models/brewtils-types";
import { useSnackbar } from "../providers/SnackbarProvider";
import { GetSystemList } from "../services/system_service";
import AccessButton from "./AccessButton";
import EnhancedTable from "./EnhancedTable/components/EnhancedTable";

function SystemList({ systemListButtonClick }: { systemListButtonClick: any }) {
  const showSnackbar = useSnackbar();
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
    <EnhancedTable
      data={systems}
      isLoading={loading}
      columns={[
        {
          id: "namespace",
          label: "Namespace",
          field: "namespace",
          sortable: true,
          filterable: true,
          isString: true,
        },
        {
          id: "name",
          label: "System Name",
          field: "name",
          sortable: true,
          filterable: true,
          isString: true,
        },
        {
          id: "description",
          label: "Description",
          field: "description",
          sortable: true,
          filterable: true,
          isString: true,
        },
        {
          id: "version",
          label: "Version",
          field: "version",
          sortable: true,
          filterable: true,
          isString: true,
        },
        {
          id: "actions",
          label: "Actions",
          template: actionTemplate,
        },
      ]}
    />
  );
}

export default SystemList;
