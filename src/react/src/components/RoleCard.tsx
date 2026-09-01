import { Dialog } from "primereact/dialog";
import { Divider } from "primereact/divider";
import { Dropdown } from "primereact/dropdown";
import { InputText } from "primereact/inputtext";
import { Messages } from "primereact/messages";
import { ChangeEvent, useEffect, useRef, useState } from "react";

import AccessButton from "../components/AccessButton";
import RoleScopeCard from "../components/RoleScopeCard";
import { Role } from "../models/brewtils-types";
import { useToast } from "../providers/ToastProvider";
import { CreateRole, EditRole, GetRole } from "../services/role_service";

function RoleCard({
  roleId,
  targetRole,
  isEdit,
  disabled = false,
  updateRoles,
  onClose,
}: {
  roleId?: string;
  targetRole?: Role;
  isEdit?: boolean;
  disabled?: boolean;
  updateRoles?: (role: Role) => void;
  onClose: () => void;
}) {
  const showToast = useToast();

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
  const msgs = useRef<Messages>(null);

  const permissions = [
    { label: "GARDEN_ADMIN", value: "GARDEN_ADMIN" },
    { label: "PLUGIN_ADMIN", value: "PLUGIN_ADMIN" },
    { label: "OPERATOR", value: "OPERATOR" },
    { label: "READ_ONLY", value: "READ_ONLY" },
  ];

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
          showToast({
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

  function handleDialogSubmit() {
    if (updateRoles === undefined) {
      showToast({
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

            showToast({
              severity: "info",
              summary: "Role Updated",
              detail: `Role updated: ${roleObj.name}`,
              life: 3000,
            });
            onClose();
          })
          .catch((error) => {
            showToast({
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

            showToast({
              severity: "info",
              summary: "Role Created",
              detail: `New role created: ${roleObj.name}`,
              life: 3000,
            });
            onClose();
          })
          .catch((error) => {
            showToast({
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
      msgs.current?.show({
        severity: "error",
        detail: `Missing required field(s): ${reqs.join(", ")}`,
        sticky: true,
      });
    }
  }

  return (
    <Dialog
      data-testid="role-dialog"
      appendTo={"self"}
      header={
        !disabled
          ? isEdit === true
            ? "Edit Role"
            : "Create Role"
          : "View Role"
      }
      footer={
        <>
          <AccessButton onClick={onClose} label="Close" />
          {!disabled && updateRoles !== undefined && (
            <AccessButton
              data-testid={`submit-btn-dialog`}
              severity="danger"
              onClick={handleDialogSubmit}
              label="Submit"
            />
          )}
        </>
      }
      style={{ width: "50vw" }}
      visible
      onHide={() => {
        onClose();
      }}
    >
      <Messages ref={msgs} />
      <div className="flex flex-column gap-2">
        <label htmlFor="roleName" className="font-bold">
          Name
        </label>
        <InputText
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
        <InputText
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
        <Dropdown
          required
          id="rolePermission"
          className="mb-2"
          options={permissions}
          value={rolePermission}
          optionLabel="label"
          placeholder="Select One"
          disabled={disabled}
          onChange={(e) => {
            setRolePermission(e.value);
          }}
        />
      </div>
      <Divider />
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
    </Dialog>
  );
}

export default RoleCard;
