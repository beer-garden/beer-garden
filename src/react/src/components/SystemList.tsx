import { useEffect, useState } from "react";

import { System } from "../models/brewtils-types";
import { useSnackbar } from "../providers/SnackbarProvider";
import { CompareVersions, GetSystemList } from "../services/system_service";
import AccessButton from "./AccessButton";
import EnhancedTable from "./EnhancedTable/components/EnhancedTable";
import VersionList from "./VersionList";

function SystemList({ systemListButtonClick }: { systemListButtonClick: any }) {
  const showSnackbar = useSnackbar();
  const [allSystems, setAllSystems] = useState<System[]>([]);
  const [systems, setSystems] = useState<System[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    GetSystemList()
      .then((systems: System[]) => {
        setAllSystems(systems);
        // Sort systems by name and version
        const sortedSystems = [...systems].sort((a: System, b: System) => {
          if (a?.name && b?.name) {
            const nameCompare = a.name.localeCompare(b.name);
            if (nameCompare !== 0) {
              return nameCompare;
            }
            return CompareVersions(a.version!, b.version!);
          }
          return 1;
        });
        const uniqueSystems = [
          ...new Map(sortedSystems.map((item) => [item.name, item])).values(),
        ];

        setSystems(uniqueSystems);
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

  function versionTemplate(system: System) {
    return (
      <VersionList
        system={system}
        systems={allSystems}
        setSystems={setSystems}
      />
    );
  }

  function actionTemplate(system: System) {
    return (
      <AccessButton
        tooltip={`Select System ${system.namespace} ${system.name}`}
        onClick={() => {
          systemListButtonClick(
            systems.find(
              (s) => s.namespace === system.namespace && s.name === system.name,
            ),
          );
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
          template: versionTemplate,
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
