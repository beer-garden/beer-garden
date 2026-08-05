import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Alert, Box, Typography } from "@mui/material";
import { RefObject, useCallback, useEffect, useRef, useState } from "react";

import AccessButton from "../components/AccessButton";
import EnhancedTable from "../components/EnhancedTable/components/EnhancedTable";
import RoleCard from "../components/RoleCard";
import { Role } from "../models/brewtils-types";
import { Config, TourStepProps } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import { checkPermission } from "../services/permission_service";
import { DeleteRole, GetRoles, Rescan } from "../services/role_service";
import {
  AddTourStep,
  ClearTourSteps,
  GenerateTourProps,
} from "../services/tour_service";
import { FAIcon } from "../services/util_service";

function RoleIndex({
  config,
  tourStepsRef,
}: {
  config: Config;
  tourStepsRef: RefObject<Array<TourStepProps>>;
}) {
  const showSnackbar = useSnackbar();
  const [roles, setRoles] = useState<Array<Role>>([]);
  const [loading, setLoading] = useState(false);

  const [dialogVisible, setDialogVisible] = useState(false);
  const roleId = useRef<string | undefined>(undefined);
  const isEdit = useRef<boolean>(false);

  const tourUuid = "role_index_tour";
  const tourPrefix = "role_index";

  const rescanRolesTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Rescan Roles",
    content:
      "Rescan the roles configuration file. This is required to pick up any changes made to the file outside of Beergarden.",
    layer: "LAYOUT",
    pos: 0,
  };

  const createRoleTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Create Role",
    content:
      "Click here to create a new role. Roles define permissions for users and are required to use Beergarden when authentication is enabled.",
    layer: "LAYOUT",
    pos: 1,
  };

  const duplicateRoleTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Duplicate Role",
    content:
      "Click here to duplicate an existing role. This will copy all of the settings of the existing role into a new role which can then be modified as needed.",
    layer: "LAYOUT",
    pos: 2,
  };

  const editRoleTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Edit Role",
    content:
      "Click here to edit an existing role. This will allow you to modify the settings of the role.",
    layer: "LAYOUT",
    pos: 3,
  };

  const deleteRoleTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Delete Role",
    content:
      "Click here to delete an existing role. This will permanently delete the role from Beergarden.",
    layer: "LAYOUT",
    pos: 4,
  };

  const loadRoles = useCallback(() => {
    setLoading(true);

    GetRoles()
      .then((roles: Array<Role>) => {
        setRoles(roles);
        setLoading(false);
      })
      .catch((error) => {
        setLoading(false);
        showSnackbar({
          severity: "error",
          summary: "Error",
          detail: `Error fetching roles: ${error}`,
          life: 3000,
        });
      });
  }, [roles]);

  useEffect(() => {
    loadRoles();
  }, []);

  useEffect(() => {
    ClearTourSteps(tourStepsRef, tourUuid);

    AddTourStep(tourStepsRef, rescanRolesTourStep);
    AddTourStep(tourStepsRef, createRoleTourStep);
    if (roles && roles.length > 0) {
      AddTourStep(tourStepsRef, duplicateRoleTourStep);
      if (roles.some((r) => !r.protected && !r.file_generated)) {
        AddTourStep(tourStepsRef, editRoleTourStep);
        AddTourStep(tourStepsRef, deleteRoleTourStep);
      }
    }

    return () => {
      ClearTourSteps(tourStepsRef, tourUuid);
    };
  }, [roles]);

  function handleRescan() {
    Rescan()
      .then(() => {
        loadRoles();
        showSnackbar({
          severity: "info",
          summary: "Confirmation",
          detail: "Rescan complete",
          life: 3000,
        });
      })
      .catch((error) => {
        showSnackbar({
          severity: "error",
          summary: "Error",
          detail: `Error rescanning roles: ${error}`,
          life: 3000,
        });
      });
  }

  function openRoleDialog() {
    roleId.current = undefined;
    isEdit.current = false;
    setDialogVisible(true);
  }

  const buttonStyle = { m: 1 };

  const header = (
    <div>
      <Box
        sx={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 1,
        }}
      >
        <Typography variant="h2" component="h1">
          Role Management
        </Typography>

        <Box sx={{ display: "flex" }}>
          <AccessButton
            sx={buttonStyle}
            onClick={handleRescan}
            label="Rescan Roles"
            data-testid="rescan-btn"
            {...GenerateTourProps(rescanRolesTourStep)}
            config={config}
            permission="GARDEN_ADMIN"
            isGlobal={true}
          >
            Rescan Roles
          </AccessButton>
          <AccessButton
            sx={buttonStyle}
            onClick={openRoleDialog}
            label="Create Role"
            data-testid="create-btn"
            {...GenerateTourProps(createRoleTourStep)}
            config={config}
            permission="GARDEN_ADMIN"
            isGlobal={true}
          >
            Create Role
          </AccessButton>
        </Box>
      </Box>
      <div>
        {config?.auth_enabled == false && (
          <Alert sx={{ mx: 1, mb: 1 }} severity="error">
            Warning - Beergarden authorization is currently disabled. Changes
            made here will be persisted, but permissions will not be enforced.
            Contact your administator to enable this feature.
          </Alert>
        )}
      </div>
    </div>
  );

  function RoleTable() {
    function handleDeleteRole(role: Role) {
      if (role && role.id) {
        DeleteRole(role.id)
          .then(() => {
            setRoles((currentRoles) => {
              return currentRoles.filter((r) => r.id !== role.id);
            });
            showSnackbar({
              severity: "info",
              summary: "Role Deleted",
              detail: `Deleted role: ${role.name}`,
              life: 3000,
            });
          })
          .catch((error) => {
            showSnackbar({
              severity: "error",
              summary: "Error",
              detail: `Error deleting the role: ${error}`,
              life: 3000,
            });
          });
      }
    }

    function handleLoadRole(role: Role, isNew = true) {
      roleId.current = role.id;
      isEdit.current = !isNew;
      setDialogVisible(true);
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
            <FAIcon
              icon="user-tag"
              title="File Generated Role"
              sx={{ mr: 1 }}
            />
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

    function roleButtonTemplate(role: Role) {
      // Show delete
      if (!checkPermission(config, "GARDEN_ADMIN", { global: true })) {
        return <></>;
      }
      return (
        <Box sx={{ display: "flex" }}>
          <AccessButton
            data-testid={`duplicate-btn-${role.name}`}
            aria-label={`Duplicate ${role.name}`}
            tooltip={`Duplicate ${role.name}`}
            onClick={() => handleLoadRole(role, true)}
            {...GenerateTourProps(duplicateRoleTourStep)}
          >
            <FontAwesomeIcon icon="clone" />
          </AccessButton>
          {!role.file_generated && !role.protected && (
            <AccessButton
              data-testid={`edit-btn-${role.name}`}
              aria-label={`Edit ${role.name}`}
              tooltip={`Edit ${role.name}`}
              onClick={() => handleLoadRole(role, false)}
              {...GenerateTourProps(editRoleTourStep)}
            >
              <FontAwesomeIcon icon="pencil" />
            </AccessButton>
          )}
          {!role.file_generated && !role.protected && (
            <AccessButton
              data-testid={`delete-btn-${role.name}`}
              aria-label={`Delete ${role.name}`}
              tooltip={`Delete ${role.name}`}
              onClick={() => handleDeleteRole(role)}
              {...GenerateTourProps(deleteRoleTourStep)}
            >
              <FontAwesomeIcon icon="trash-can" />
            </AccessButton>
          )}
        </Box>
      );
    }

    return (
      <div>
        <EnhancedTable
          data-testid="role-datatable"
          data={roles}
          isLoading={loading}
          columns={[
            {
              id: "name",
              field: "name",
              label: "Role",
              sortable: true,
              filterable: true,
              isString: true,
              template: roleNameTemplate,
            },
            {
              id: "permission",
              field: "permission",
              label: "Permission",
              sortable: true,
              filterable: true,
              isString: true,
            },
            {
              id: "description",
              field: "description",
              label: "Description",
              sortable: true,
              filterable: true,
              isString: true,
            },
            {
              id: "scope_gardens",
              field: "scope_gardens",
              label: "Garden Scope",
              sortable: true,
              filterable: true,
              isStrArray: true,
            },
            {
              id: "scope_namespaces",
              field: "scope_namespaces",
              label: "Namespace Scope",
              sortable: true,
              filterable: true,
              isStrArray: true,
            },
            {
              id: "scope_systems",
              field: "scope_systems",
              label: "System Scope",
              sortable: true,
              filterable: true,
              isStrArray: true,
            },
            {
              id: "scope_versions",
              field: "scope_versions",
              label: "Version Scope",
              sortable: true,
              filterable: true,
              isStrArray: true,
            },
            {
              id: "scope_instances",
              field: "scope_instances",
              label: "Instance Scope",
              sortable: true,
              filterable: true,
              isStrArray: true,
            },
            {
              id: "scope_commands",
              field: "scope_commands",
              label: "Command Scope",
              sortable: true,
              filterable: true,
              isStrArray: true,
            },
            {
              id: "action",
              label: "",
              template: roleButtonTemplate,
            },
          ]}
          header={header}
          defaultOrderBy="name"
          defaultOrder="desc"
        />
      </div>
    );
  }

  function updateRoles(updatedRole: Role) {
    setRoles((currentRoles) => {
      const newRoles = currentRoles.map((role) => {
        if (role.id == updatedRole.id) {
          role = updatedRole;
        }
        return { ...role };
      });
      return newRoles;
    });
  }

  return (
    <div>
      {dialogVisible && (
        <RoleCard
          isEdit={isEdit.current}
          roleId={roleId.current}
          dialogVisible={dialogVisible}
          updateRoles={updateRoles}
          onClose={() => {
            setDialogVisible(false);
            loadRoles();
          }}
        />
      )}
      <RoleTable />
    </div>
  );
}

export default RoleIndex;
