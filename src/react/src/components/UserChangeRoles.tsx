import {
  Box,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
} from "@mui/material";
import React, { useEffect, useState } from "react";

import { Role, User } from "../models/brewtils-types";
import { useSnackbar } from "../providers/SnackbarProvider";
import { GetRoles } from "../services/role_service";
import { UpdateUserRoles } from "../services/user_service";
import { FAIcon } from "../services/util_service";
import AccessButton from "./AccessButton";
import EnhancedTable from "./EnhancedTable/components/EnhancedTable";

interface SelectedRole extends Role {
  selected: boolean;
}

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
  const showSnackbar = useSnackbar();
  const [roles, setRoles] = useState<Array<SelectedRole> | undefined>(
    undefined,
  );
  const [isLoading, setIsLoading] = useState(false);

  function selectRole(roleName: string, selected: boolean) {
    setRoles(
      roles?.map((role) => {
        if (role.name === roleName) {
          return { ...role, selected: selected };
        }
        return role;
      }),
    );
  }

  function roleSelectionTemplate(role: SelectedRole) {
    return (
      <Checkbox
        checked={role.selected}
        slotProps={{
          input: {
            "aria-label": `Row ${role.selected ? "Unselected" : "Selected"} ${role.id}`,
          },
        }}
        onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
          if (role.name) {
            selectRole(role.name, event.target.checked);
          }
        }}
      />
    );
  }

  function roleNameTemplate(role: Role) {
    if (role.protected) {
      return (
        <Box sx={{ display: "flex" }}>
          <FAIcon icon="user-shield" title="Protected Role" sx={{ mr: 1 }} />
          {role.name}
        </Box>
      );
    } else if (role.file_generated) {
      return (
        <Box sx={{ display: "flex" }}>
          <FAIcon icon="user-tag" title="File Generated Role" sx={{ mr: 1 }} />
          {role.name}
        </Box>
      );
    } else {
      return (
        <Box sx={{ display: "flex" }}>
          <FAIcon icon="user-gear" title="Unprotected Role" sx={{ mr: 1 }} />
          {role.name}
        </Box>
      );
    }
  }

  function handleUserRolesDialogClose() {
    setShowRolesDialog(false);
  }

  function updateRoles() {
    if (user.username && roles) {
      const selectedRoleNames = [] as Array<string>;
      for (const role of roles) {
        if (role.name && role.selected) {
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
          showSnackbar({
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
      setIsLoading(true);
      GetRoles()
        .then((data) => {
          setRoles(
            data.map((role: Role) => {
              return {
                ...role,
                selected: user.local_roles?.some(
                  (local_role) => local_role.name === role.name,
                ),
              } as SelectedRole;
            }),
          );
          setIsLoading(false);
        })
        .catch((error) => {
          console.error("Error fetching roles:", error);
          showSnackbar({
            severity: "error",
            summary: "Error",
            detail: `Error fetching roles: ${error}`,
            life: 3000,
          });
          setRoles([]);
          setIsLoading(false);
        });
    }
  }, [user]);

  return (
    <Dialog
      data-testid="change-roles-dialog"
      open={showRolesDialog}
      onClose={() => {
        handleUserRolesDialogClose();
      }}
      maxWidth={false}
      aria-labelledby="change-roles-dialog-title"
    >
      <DialogTitle id="change-roles-dialog-title">{`Add/Remove Roles for ${user.username}`}</DialogTitle>
      <DialogContent>
        <EnhancedTable
          data={roles ?? []}
          defaultOrderBy="name"
          columns={[
            {
              id: "selected",
              field: "selected",
              label: (
                <Checkbox
                  onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
                    setRoles(
                      roles?.map((role) => {
                        return { ...role, selected: event.target.checked };
                      }),
                    );
                  }}
                />
              ),
              template: roleSelectionTemplate,
              sortable: true,
              filterable: true,
              isBoolean: true,
            },
            {
              id: "name",
              label: "Role",
              field: "name",
              sortable: true,
              filterable: true,
              isString: true,
              template: roleNameTemplate,
            },
            {
              id: "permission",
              label: "Permission",
              field: "permission",
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
              id: "scope_gardens",
              label: "Garden Scope",
              field: "scope_gardens",
              sortable: true,
              filterable: true,
              isString: true,
            },
            {
              id: "scope_namespaces",
              label: "Namespace Scope",
              field: "scope_namespaces",
              sortable: true,
              filterable: true,
              isString: true,
            },
            {
              id: "scope_systems",
              label: "System Scope",
              field: "scope_systems",
              sortable: true,
              filterable: true,
              isString: true,
            },
            {
              id: "scope_versions",
              label: "Version Scope",
              field: "scope_versions",
              sortable: true,
              filterable: true,
              isString: true,
            },
            {
              id: "scope_instances",
              label: "Instance Scope",
              field: "scope_instances",
              sortable: true,
              filterable: true,
              isString: true,
            },
            {
              id: "scope_commands",
              label: "Command Scope",
              field: "scope_commands",
              sortable: true,
              filterable: true,
              isString: true,
            },
          ]}
          isLoading={isLoading}
        />
      </DialogContent>
      <DialogActions>
        <AccessButton onClick={handleUserRolesDialogClose} label="Close">
          Close
        </AccessButton>
        <AccessButton
          data-testid={`submit-btn-dialog`}
          color="error"
          onClick={updateRoles}
          label="Submit"
        >
          Submit
        </AccessButton>
      </DialogActions>
    </Dialog>
  );
}

export default UserChangeRoles;
