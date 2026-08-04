import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  Alert,
  Autocomplete,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Grid,
  TextField,
} from "@mui/material";
import { ChangeEvent, useEffect, useState } from "react";

import AccessButton from "../components/AccessButton";
import RoleScopeCard from "../components/RoleScopeCard";
import { Role } from "../models/brewtils-types";
import { useSnackbar } from "../providers/SnackbarProvider";
import { CreateRole, EditRole, GetRole } from "../services/role_service";

function RoleCard({
  roleId,
  targetRole,
  isEdit,
  disabled = false,
  dialogVisible = false,
  updateRoles,
  onClose,
}: {
  roleId?: string;
  targetRole?: Role;
  isEdit?: boolean;
  disabled?: boolean;
  dialogVisible?: boolean;
  updateRoles?: (role: Role) => void;
  onClose: () => void;
}) {
  const showSnackbar = useSnackbar();

  const [roleName, setRoleName] = useState<string>("");
  const [roleDescription, setRoleDescription] = useState<string>("");
  const [rolePermission, setRolePermission] = useState<string>("");
  const [gardenScopeList, setGardenScopeList] = useState<Array<string>>([""]);
  const [namespaceScopeList, setNamespaceScopeList] = useState<Array<string>>([
    "",
  ]);
  const [systemScopeList, setSystemScopeList] = useState<Array<string>>([""]);
  const [versionScopeList, setVersionScopeList] = useState<Array<string>>([""]);
  const [instanceScopeList, setInstanceScopeList] = useState<Array<string>>([
    "",
  ]);
  const [commandScopeList, setCommandScopeList] = useState<Array<string>>([""]);

  interface AlertObj {
    severity: "success" | "info" | "warning" | "error";
    detail: string;
  }

  const [alert, setAlert] = useState<AlertObj | undefined>(undefined);

  const permissions = ["GARDEN_ADMIN", "PLUGIN_ADMIN", "OPERATOR", "READ_ONLY"];

  function setRole(role: Role) {
    setRoleName(isEdit === true || disabled ? role.name || "" : "");
    setRoleDescription(role.description || "");
    setRolePermission(role.permission || "");
    setGardenScopeList(
      role.scope_gardens && role.scope_gardens.length > 0
        ? role.scope_gardens
        : [""],
    );
    setNamespaceScopeList(
      role.scope_namespaces && role.scope_namespaces.length > 0
        ? role.scope_namespaces
        : [""],
    );
    setSystemScopeList(
      role.scope_systems && role.scope_systems.length > 0
        ? role.scope_systems
        : [""],
    );
    setVersionScopeList(
      role.scope_versions && role.scope_versions.length > 0
        ? role.scope_versions
        : [""],
    );
    setInstanceScopeList(
      role.scope_instances && role.scope_instances.length > 0
        ? role.scope_instances
        : [""],
    );
    setCommandScopeList(
      role.scope_commands && role.scope_commands.length > 0
        ? role.scope_commands
        : [""],
    );
  }

  useEffect(() => {
    if (roleId) {
      GetRole(roleId)
        .then((role: Role) => {
          setRole(role);
        })
        .catch((error) => {
          showSnackbar({
            severity: "error",
            summary: "Error",
            detail: `Error loading the role: ${error}`,
            life: 3000,
          });
        });
    } else if (targetRole) {
      setRole(targetRole);
    } else {
      setRolePermission("");
      setGardenScopeList([""]);
      setNamespaceScopeList([""]);
      setSystemScopeList([""]);
      setVersionScopeList([""]);
      setInstanceScopeList([""]);
      setCommandScopeList([""]);
    }
  }, []);

  const handleDismissAlert = () => {
    setAlert(undefined);
  };

  const addAlert = (newAlert: AlertObj) => {
    setAlert(newAlert);
  };

  function handleDialogSubmit() {
    if (updateRoles === undefined) {
      showSnackbar({
        severity: "error",
        summary: "Error",
        detail: `Missing Roles Updater Logic`,
        life: 3000,
      });
      return;
    }
    if (roleName && rolePermission) {
      const roleObj = {
        name: roleName,
        description: roleDescription || "",
        permission: rolePermission,
        scope_gardens: gardenScopeList.filter((i) => i.length > 0),
        scope_namespaces: namespaceScopeList.filter((i) => i.length > 0),
        scope_systems: systemScopeList.filter((i) => i.length > 0),
        scope_versions: versionScopeList.filter((i) => i.length > 0),
        scope_instances: instanceScopeList.filter((i) => i.length > 0),
        scope_commands: commandScopeList.filter((i) => i.length > 0),
      } as Role;
      if (roleId && isEdit === true) {
        //Editing existing role
        roleObj.id = roleId;
        EditRole(roleObj)
          .then((updatedRole: Role) => {
            updateRoles(updatedRole);

            showSnackbar({
              severity: "info",
              summary: "Role Updated",
              detail: `Role updated: ${roleObj.name}`,
              life: 3000,
            });
            onClose();
          })
          .catch((error) => {
            showSnackbar({
              severity: "error",
              summary: "Error",
              detail: `Error editing the role: ${error}`,
              life: 3000,
            });
          });
      } else {
        // Create new role
        CreateRole(roleObj)
          .then((createdRole: Role) => {
            updateRoles(createdRole);

            showSnackbar({
              severity: "info",
              summary: "Role Created",
              detail: `New role created: ${roleObj.name}`,
              life: 3000,
            });
            onClose();
          })
          .catch((error) => {
            showSnackbar({
              severity: "error",
              summary: "Error",
              detail: `Error creating the role: ${error}`,
              life: 3000,
            });
          });
      }
    } else {
      const reqs = [];
      if (!roleName) {
        reqs.push("Name");
      }
      if (!rolePermission) {
        reqs.push("Permission");
      }
      addAlert({
        severity: "error",
        detail: `Missing required field(s): ${reqs.join(", ")}`,
      });
    }
  }

  return (
    <Dialog
      data-testid="role-dialog"
      open={dialogVisible}
      onClose={onClose}
      fullWidth={true}
      maxWidth="md"
    >
      <DialogTitle>
        <Grid container>
          <Grid size="grow">
            {!disabled
              ? isEdit === true
                ? "Edit Role"
                : "Create Role"
              : "View Role"}
          </Grid>
          <Grid>
            <AccessButton sx={{ mr: 2 }} onClick={onClose}>
              <FontAwesomeIcon icon="xmark" />
            </AccessButton>
          </Grid>
        </Grid>
      </DialogTitle>
      <DialogContent dividers>
        {alert && (
          <Alert
            sx={{ mb: 1 }}
            severity={alert.severity}
            onClose={handleDismissAlert}
          >
            {alert.detail}
          </Alert>
        )}
        <div className="flex flex-column gap-2">
          <label htmlFor="roleName" className="font-bold">
            Name
          </label>
          <TextField
            required
            id="roleName"
            type="text"
            className="mb-2"
            value={roleName}
            disabled={disabled}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setRoleName(e.target.value)
            }
          />
        </div>
        <div className="flex flex-column gap-2">
          <label htmlFor="roleDescription" className="font-bold">
            Description
          </label>
          <TextField
            id="roleDescription"
            type="text"
            className="mb-2"
            value={roleDescription}
            disabled={disabled}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setRoleDescription(e.target.value)
            }
          />
        </div>
        <div className="flex flex-column gap-2">
          <label htmlFor="rolePermission" className="font-bold">
            Permission
          </label>
          <Autocomplete
            id="rolePermission"
            options={permissions}
            value={rolePermission ?? null}
            onChange={(_event: any, newValue: string | null) => {
              setRolePermission(newValue || "");
            }}
            disabled={disabled}
            renderInput={(params) => <TextField {...params} />}
          />
        </div>
        <Divider sx={{ my: 2 }} />
        <RoleScopeCard
          scopeName="garden"
          scopeList={gardenScopeList}
          setScopeList={setGardenScopeList}
          disabled={disabled}
        />
        <RoleScopeCard
          scopeName="namespace"
          scopeList={namespaceScopeList}
          setScopeList={setNamespaceScopeList}
          disabled={disabled}
        />
        <RoleScopeCard
          scopeName="system"
          scopeList={systemScopeList}
          setScopeList={setSystemScopeList}
          disabled={disabled}
        />
        <RoleScopeCard
          scopeName="version"
          scopeList={versionScopeList}
          setScopeList={setVersionScopeList}
          disabled={disabled}
        />
        <RoleScopeCard
          scopeName="instance"
          scopeList={instanceScopeList}
          setScopeList={setInstanceScopeList}
          disabled={disabled}
        />
        <RoleScopeCard
          scopeName="command"
          scopeList={commandScopeList}
          setScopeList={setCommandScopeList}
          disabled={disabled}
        />
      </DialogContent>
      <DialogActions>
        <>
          <AccessButton onClick={onClose} label="Close">
            Close
          </AccessButton>
          {!disabled && updateRoles !== undefined && (
            <AccessButton
              data-testid={`submit-btn-dialog`}
              color="error"
              onClick={handleDialogSubmit}
              label="Submit"
            >
              Submit
            </AccessButton>
          )}
        </>
      </DialogActions>
    </Dialog>
  );
}

export default RoleCard;
