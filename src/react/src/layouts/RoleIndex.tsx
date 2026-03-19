import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "primereact/button";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { Dialog } from "primereact/dialog";
import { Dropdown } from "primereact/dropdown";
import { InputText } from "primereact/inputtext";
import { Message } from "primereact/message";
import { Messages } from "primereact/messages";
import { Toast } from "primereact/toast";
import { ChangeEvent, useCallback, useEffect, useRef, useState } from "react";

import RoleScopeCard from "../components/RoleScopeCard";
import { Role } from "../models/brewtils-types";
import {
  CreateRole,
  DeleteRole,
  EditRole,
  GetRoles,
  Rescan,
} from "../services/role_service";

const permissions = [
  { label: "GARDEN_ADMIN", value: "GARDEN_ADMIN" },
  { label: "PLUGIN_ADMIN", value: "PLUGIN_ADMIN" },
  { label: "OPERATOR", value: "OPERATOR" },
  { label: "READ_ONLY", value: "READ_ONLY" },
];

function RoleIndex() {
  const toast = useRef<Toast>(null);
  const [roles, setRoles] = useState<Array<Role>>([]);
  const [loading, setLoading] = useState(false);
  const [first, setFirst] = useState<number>(0);
  const [rows, setRows] = useState<number>(10);
  const [sortField, setSortField] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState<number | null>(null);

  const [dialogVisible, setDialogVisible] = useState(false);
  const isEdit = useRef<boolean>(false);
  const roleId = useRef<string | undefined>(undefined);
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

  const loadRoles = useCallback(() => {
    setLoading(true);

    GetRoles()
      .then((roles: Array<Role>) => {
        setRoles(roles);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error fetching roles:", error);
        setLoading(false);
      });
  }, [roles]);

  useEffect(() => {
    loadRoles();
  }, []);

  function handleDialogClose() {
    //Dismiss dialog
    setDialogVisible(false);
    //Reset all values to defaults
    roleId.current = undefined;
    isEdit.current = false;
    setRolePermission("");
    setGardenScopeList([""]);
    setNamespaceScopeList([""]);
    setSystemScopeList([""]);
    setVersionScopeList([""]);
    setInstanceScopeList([""]);
    setCommandScopeList([""]);
  }

  function handleDialogSubmit() {
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
      if (roleId && roleId.current && isEdit.current) {
        //Editing existing role
        roleObj.id = roleId.current;
        EditRole(roleObj)
          .then((updatedRole: Role) => {
            setRoles((currentRoles) => {
              const newRoles = currentRoles.map((role) => {
                if (role.id == updatedRole.id) {
                  role = updatedRole;
                }
                return { ...role };
              });
              return newRoles;
            });
            setDialogVisible(false);
            toast.current?.show({
              severity: "info",
              summary: "Role Updated",
              detail: `Role updated: ${roleObj.name}`,
              life: 3000,
            });
          })
          .catch((error) => {
            console.error("Error editing the role:", error);
          });
      } else {
        // Create new role
        CreateRole(roleObj)
          .then((createdRole: Role) => {
            setRoles([...roles, createdRole]);
            roleId.current = undefined;
            setDialogVisible(false);
            toast.current?.show({
              severity: "info",
              summary: "Role Created",
              detail: `New role created: ${roleObj.name}`,
              life: 3000,
            });
          })
          .catch((error) => {
            console.error("Error creating the role:", error);
          });
      }
      setRoleName("");
      setRoleDescription("");
      setRolePermission("");
      setGardenScopeList([""]);
      setNamespaceScopeList([""]);
      setSystemScopeList([""]);
      setVersionScopeList([""]);
      setInstanceScopeList([""]);
      setCommandScopeList([""]);
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

  function RoleHeader() {
    function handleRescan() {
      Rescan()
        .then(() => {
          loadRoles();
          toast.current?.show({
            severity: "info",
            summary: "Confirmation",
            detail: "Rescan complete",
            life: 3000,
          });
        })
        .catch((error) => {
          console.error("Error deleting system:", error);
        });
    }
    function openRoleDialog() {
      setDialogVisible(true);
    }

    return (
      <div className="flex items-end ml-2 page-header">
        <h1 className="flex-1">Role Management</h1>
        <div>
          <Button onClick={handleRescan} label="Rescan Roles" />
          <Button onClick={openRoleDialog} label="Create Role" />
        </div>
      </div>
    );
  }

  function RoleTable() {
    function handleDeleteRole(role: Role) {
      if (role && role.id) {
        DeleteRole(role.id)
          .then(() => {
            setRoles((currentRoles) => {
              return currentRoles.filter((r) => r.id !== role.id);
            });
            toast.current?.show({
              severity: "info",
              summary: "Role Deleted",
              detail: `Deleted role: ${role.name}`,
              life: 3000,
            });
          })
          .catch((error) => {
            console.error("Error deleting the role:", error);
          });
      }
    }

    function handleLoadRole(role: Role, isNew = true) {
      setRoleName(role.name || "");
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
      isEdit.current = !isNew;
      roleId.current = role.id;
      setDialogVisible(true);
    }

    function roleButtonTemplate(role: Role) {
      // Show delete
      return (
        <div className="flex">
          <Button
            tooltip="Duplicate"
            onClick={() => handleLoadRole(role, true)}
          >
            <FontAwesomeIcon icon="clone" />
          </Button>
          {!role.file_generated && !role.protected && (
            <Button tooltip="Edit" onClick={() => handleLoadRole(role, false)}>
              <FontAwesomeIcon icon="pencil" />
            </Button>
          )}
          {!role.file_generated && !role.protected && (
            <Button tooltip="Delete" onClick={() => handleDeleteRole(role)}>
              <FontAwesomeIcon icon="trash-can" />
            </Button>
          )}
        </div>
      );
    }

    return (
      <div>
        <Message
          severity="error"
          text="Warning - Beergarden authorization is currently disabled. Changes made here
          will be persisted, but permissions will not be enforced. Contact your
          administator to enable this feature."
        />
        <DataTable
          value={roles}
          loading={loading}
          paginator
          rows={rows}
          first={first}
          sortField={sortField}
          sortOrder={sortOrder}
          rowsPerPageOptions={[10, 25, 50]}
          onPage={(e: any) => {
            setFirst(e.first);
            setRows(e.rows);
          }}
          onSort={(e: any) => {
            setSortField(e.sortField);
            setSortOrder(e.sortOrder);
            setFirst(0);
          }}
          dataKey="id"
        >
          <Column field="name" sortable header="Role" />
          <Column field="permission" sortable header="Permission" />
          <Column field="description" sortable header="Description" />
          <Column field="scope_gardens" sortable header="Garden Scope" />
          <Column field="scope_namespaces" sortable header="Namespace Scope" />
          <Column field="scope_systems" sortable header="System Scope" />
          <Column field="scope_versions" sortable header="Version Scope" />
          <Column field="scope_instances" sortable header="Instance Scope" />
          <Column field="scope_commands" sortable header="Command Scope" />
          <Column header="" body={roleButtonTemplate} />
        </DataTable>
      </div>
    );
  }

  return (
    <div>
      <Toast ref={toast} />
      <Dialog
        appendTo={"self"}
        header={isEdit.current ? "Edit Role" : "Create Role"}
        footer={
          <>
            <Button onClick={handleDialogClose}>Close</Button>
            <Button severity="danger" onClick={handleDialogSubmit}>
              Submit
            </Button>
          </>
        }
        visible={dialogVisible}
        style={{ width: "50vw" }}
        onHide={() => {
          handleDialogClose();
        }}
      >
        <Messages ref={msgs} />
        <div className="flex flex-column gap-2">
          <label htmlFor="roleName">Name</label>
          <InputText
            required
            id="roleName"
            type="text"
            value={roleName}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setRoleName(e.target.value)
            }
          />
        </div>
        <div className="flex flex-column gap-2">
          <label htmlFor="roleDescription">Description</label>
          <InputText
            id="roleDescription"
            type="text"
            value={roleDescription}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setRoleDescription(e.target.value)
            }
          />
        </div>
        <div className="flex flex-column gap-2">
          <label htmlFor="rolePermission">Permission</label>
          <Dropdown
            required
            id="rolePermission"
            options={permissions}
            value={rolePermission}
            optionLabel="label"
            placeholder="Select One"
            onChange={(e) => {
              // e.originalEvent?.stopPropagation();
              setRolePermission(e.value);
            }}
          />
        </div>
        <RoleScopeCard
          scopeName="garden"
          scopeList={gardenScopeList}
          setScopeList={setGardenScopeList}
        />
        <RoleScopeCard
          scopeName="namespace"
          scopeList={namespaceScopeList}
          setScopeList={setNamespaceScopeList}
        />
        <RoleScopeCard
          scopeName="system"
          scopeList={systemScopeList}
          setScopeList={setSystemScopeList}
        />
        <RoleScopeCard
          scopeName="version"
          scopeList={versionScopeList}
          setScopeList={setVersionScopeList}
        />
        <RoleScopeCard
          scopeName="instance"
          scopeList={instanceScopeList}
          setScopeList={setInstanceScopeList}
        />
        <RoleScopeCard
          scopeName="command"
          scopeList={commandScopeList}
          setScopeList={setCommandScopeList}
        />
      </Dialog>
      <RoleHeader />
      <RoleTable />
    </div>
  );
}

export default RoleIndex;
