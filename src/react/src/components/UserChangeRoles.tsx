import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { Dialog } from "primereact/dialog";
import { useEffect, useState } from "react";

import { Role, User } from "../models/brewtils-types";
import { useToast } from "../providers/ToastProvider";
import { GetRoles } from "../services/role_service";
import { UpdateUserRoles } from "../services/user_service";
import AccessButton from "./AccessButton";

function UserChangeRoles({
  user,
  showRolesDialog,
  setShowRolesDialog,
  callback,
}: {
  user: User;
  showRolesDialog: boolean;
  setShowRolesDialog: (show: boolean) => void;
  callback?: () => void;
}) {
  const showToast = useToast();
  const [roles, setRoles] = useState<Array<Role> | undefined>(undefined);
  const [selectedRoles, setSelectedRoles] = useState<Array<Role>>([]);

  function roleNameTemplate(role: Role) {
    if (role.protected) {
      return (
        <div className="flex">
          <FontAwesomeIcon
            icon="user-shield"
            title="Protected Role"
            className="mr-1"
          />
          {role.name}
        </div>
      );
    } else if (role.file_generated) {
      return (
        <div className="flex">
          <FontAwesomeIcon
            icon="user-tag"
            title="File Generated Role"
            className="mr-1"
          />
          {role.name}
        </div>
      );
    } else {
      return (
        <div className="flex">
          <FontAwesomeIcon
            icon="user-gear"
            title="Unprotected Role"
            className="mr-1"
          />
          {role.name}
        </div>
      );
    }
  }

  function handleUserRolesDialogClose() {
    setShowRolesDialog(false);
  }

  function updateRoles() {
    if (user.username && selectedRoles) {
      const selectedRoleNames = [] as Array<string>;
      for (const role of selectedRoles) {
        if (role.name) {
          selectedRoleNames.push(role.name);
        }
      }
      UpdateUserRoles(user.username, selectedRoleNames)
        .then(() => {
          if (callback) {
            callback();
          }
          handleUserRolesDialogClose();
        })
        .catch((error) => {
          console.error("Error updating user roles:", error);
          showToast({
            severity: "error",
            summary: "Error",
            detail: `Failed to update roles for user ${user.username}`,
            life: 3000,
          });
        });
    }
  }

  useEffect(() => {
    if (roles === undefined) {
      GetRoles()
        .then((data) => {
          setRoles(data);
        })
        .catch((error) => {
          console.error("Error fetching roles:", error);
          setRoles([]);
        });
    }
    if (user.local_roles) {
      setSelectedRoles(user.local_roles);
    }
  }, [user]);

  return (
    <Dialog
      data-testid="change-roles-dialog"
      header={`Add/Remove Roles for ${user.username}`}
      footer={
        <>
          <AccessButton onClick={handleUserRolesDialogClose} label="Close" />
          <AccessButton
            data-testid={`submit-btn-dialog`}
            severity="danger"
            onClick={updateRoles}
            label="Submit"
          />
        </>
      }
      visible={showRolesDialog}
      onHide={() => {
        handleUserRolesDialogClose();
      }}
    >
      <DataTable
        value={roles}
        selectionMode={"checkbox"}
        selection={selectedRoles}
        onSelectionChange={(e) => setSelectedRoles(e.value)}
        dataKey="id"
      >
        <Column
          selectionMode="multiple"
          headerStyle={{ width: "3rem" }}
        ></Column>
        <Column field="name" sortable header="Role" body={roleNameTemplate} />
        <Column field="permission" sortable header="Permission" />
        <Column field="description" sortable header="Description" />
        <Column field="scope_gardens" sortable header="Garden Scope" />
        <Column field="scope_namespaces" sortable header="Namespace Scope" />
        <Column field="scope_systems" sortable header="System Scope" />
        <Column field="scope_versions" sortable header="Version Scope" />
        <Column field="scope_instances" sortable header="Instance Scope" />
        <Column field="scope_commands" sortable header="Command Scope" />
      </DataTable>
    </Dialog>
  );
}

export default UserChangeRoles;
