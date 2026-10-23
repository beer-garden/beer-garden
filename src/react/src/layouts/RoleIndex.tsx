import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Column } from "primereact/column";
import { DataTable, SortOrder } from "primereact/datatable";
import { Message } from "primereact/message";
import { RefObject, useCallback, useEffect, useRef, useState } from "react";

import AccessButton from "../components/AccessButton";
import RoleCard from "../components/RoleCard";
import { Role } from "../models/brewtils-types";
import { Config, TourStepProps } from "../models/models";
import { useToast } from "../providers/ToastProvider";
import { checkPermission } from "../services/permission_service";
import { DeleteRole, GetRoles, Rescan } from "../services/role_service";
import {
  AddTourStep,
  ClearTourSteps,
  GenerateTourProps,
} from "../services/tour_service";
import { PaginatorTemplate } from "../services/util_service";

function RoleIndex({
  config,
  tourStepsRef,
}: {
  config: Config;
  tourStepsRef: RefObject<Array<TourStepProps>>;
}) {
  const showToast = useToast();
  const [roles, setRoles] = useState<Array<Role>>([]);
  const [loading, setLoading] = useState(false);
  const [first, setFirst] = useState<number>(0);
  const [rows, setRows] = useState<number>(10);
  const [sortField, setSortField] = useState<string | undefined>(undefined);
  const [sortOrder, setSortOrder] = useState<SortOrder>(undefined);

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
        showToast({
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

  function RoleHeader() {
    function handleRescan() {
      Rescan()
        .then(() => {
          loadRoles();
          showToast({
            severity: "info",
            summary: "Confirmation",
            detail: "Rescan complete",
            life: 3000,
          });
        })
        .catch((error) => {
          showToast({
            severity: "error",
            summary: "Error",
            detail: `Error rescanning roles: ${error}`,
            life: 3000,
          });
        });
    }
    function openRoleDialog() {
      setDialogVisible(true);
    }

    return (
      <div className="flex items-end ml-2 page-header">
        <h1 className="flex-1">Role Management</h1>

        <div>
          <AccessButton
            onClick={handleRescan}
            label="Rescan Roles"
            data-testid="rescan-btn"
            {...GenerateTourProps(rescanRolesTourStep)}
            config={config}
            permission="GARDEN_ADMIN"
            isGlobal={true}
          />
          <AccessButton
            onClick={openRoleDialog}
            label="Create Role"
            data-testid="create-btn"
            {...GenerateTourProps(createRoleTourStep)}
            config={config}
            permission="GARDEN_ADMIN"
            isGlobal={true}
          />
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
            showToast({
              severity: "info",
              summary: "Role Deleted",
              detail: `Deleted role: ${role.name}`,
              life: 3000,
            });
          })
          .catch((error) => {
            showToast({
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

    function roleButtonTemplate(role: Role) {
      // Show delete
      if (!checkPermission(config, "GARDEN_ADMIN", { global: true })) {
        return <></>;
      }
      return (
        <div className="flex">
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
        </div>
      );
    }

    return (
      <div>
        {config?.auth_enabled == false && (
          <Message
            className="mx-2 mb-2"
            severity="error"
            text="Warning - Beergarden authorization is currently disabled. Changes made here
            will be persisted, but permissions will not be enforced. Contact your
            administator to enable this feature."
            pt={{
              icon: {
                role: "img",
                "aria-label": "Close Alert Message",
                style: { color: "var(--danger-color)" },
              },
            }}
            style={{
              backgroundColor: "var(--danger-background-color)",
              color: "var(--danger-color)",
            }}
          />
        )}
        <DataTable
          data-testid="role-datatable"
          value={roles}
          loading={loading}
          paginator
          rows={rows}
          first={first}
          sortField={sortField}
          sortOrder={sortOrder}
          rowsPerPageOptions={[10, 25, 50]}
          paginatorTemplate={PaginatorTemplate}
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
          <Column field="name" sortable header="Role" body={roleNameTemplate} />
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
          updateRoles={updateRoles}
          onClose={() => {
            setDialogVisible(false);
            loadRoles();
          }}
        />
      )}
      <RoleHeader />
      <RoleTable />
    </div>
  );
}

export default RoleIndex;
