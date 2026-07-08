import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Chip } from "primereact/chip";
import { Column } from "primereact/column";
import { confirmDialog } from "primereact/confirmdialog";
import { DataTable, SortOrder } from "primereact/datatable";
import { Message } from "primereact/message";
import { Tag } from "primereact/tag";
import { RefObject, useCallback, useEffect, useState } from "react";

import AccessButton from "../components/AccessButton";
import UserChangeAccountMapping from "../components/UserChangeAccountMapping";
import UserChangePassword from "../components/UserChangePassword";
import UserChangeRoles from "../components/UserChangeRoles";
import UserCreate from "../components/UserCreate";
import { Role, User } from "../models/brewtils-types";
import { Config, TourStepProps } from "../models/models";
import { useToast } from "../providers/ToastProvider";
import { RevokeToken } from "../services/token_service";
import {
  AddTourStep,
  ClearTourSteps,
  GenerateTourProps,
} from "../services/tour_service";
import { DeleteUser, GetUsers, RescanUsers } from "../services/user_service";
import { PaginatorTemplate } from "../services/util_service";

function UserIndex({
  config,
  tourStepsRef,
}: {
  config: Config;
  tourStepsRef: RefObject<Array<TourStepProps>>;
}) {
  const showToast = useToast();
  const [users, setUsers] = useState<Array<User>>([]);
  const [loading, setLoading] = useState(false);
  const [first, setFirst] = useState<number>(0);
  const [rows, setRows] = useState<number>(10);
  const [sortField, setSortField] = useState<string | undefined>(undefined);
  const [sortOrder, setSortOrder] = useState<SortOrder>(undefined);

  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [passwordUsername, setPasswordUsername] = useState<string | undefined>(
    undefined,
  );

  const [showRolesDialog, setShowRolesDialog] = useState(false);
  const [rolesUser, setRolesUser] = useState<User | undefined>(undefined);

  const [accountMappingUser, setAccountMappingUser] = useState<
    User | undefined
  >(undefined);
  const [showAccountMappingDialog, setShowAccountMappingDialog] =
    useState(false);

  const [showCreateUserDialog, setShowCreateUserDialog] = useState(false);

  const tourUuid = "users_tour";
  const tourPrefix = "user_index";

  const rescanUserTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Rescan Users",
    content: "Refresh the list of users from configuration file.",
    layer: "LAYOUT",
    pos: 0,
  };

  const createUserTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Create User",
    content: "Create a new user account.",
    layer: "LAYOUT",
    pos: 1,
  };

  const protectedUserTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Protected User",
    content:
      "View information about a protected user. These users are required by Beer-Garden and cannot be deleted or modified.",
    layer: "COMPONENT",
    pos: 0,
  };

  const fileGeneratedUserTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "File Generated User",
    content:
      "View information about a file generated user. These users are generated from an external file and reset to defaults on Rescan/Restart.",
    layer: "COMPONENT",
    pos: 1,
  };

  const userUserTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "User",
    content: "View information about a user.",
    layer: "COMPONENT",
    pos: 2,
  };

  const maxPermissionUserTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Max Permission",
    content:
      "The maximum permission level for this user based on their assigned roles.",
    layer: "COMPONENT",
    pos: 3,
  };

  const lastAuthenticatedUserTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Last Authenticated",
    content: "The last time this user was authenticated.",
    layer: "COMPONENT",
    pos: 4,
  };

  const localRolesUserTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Local Roles",
    content:
      "The roles assigned to this user within the local garden. Tool Tip of role chip shows permission associated with that role.",
    layer: "COMPONENT",
    pos: 4,
  };

  const upstreamRolesUserTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Upstream Roles",
    content:
      "The roles assigned to this user from an upstream source. Tool Tip of role chip shows permission associated with that role.",
    layer: "COMPONENT",
    pos: 5,
  };

  const aliasGardenAccountsUserTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Alias Garden Accounts",
    content: "The accounts in other gardens that are mapped to this user.",
    layer: "COMPONENT",
    pos: 6,
  };

  const activeTokenUserTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Active Token",
    content: "Indicates whether this user has an active token.",
    layer: "COMPONENT",
    pos: 7,
  };

  const revokeTokenUserTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Revoke Token",
    content:
      "Revoke the active token for this user, forcing them to re-authenticate to get a new token.",
    layer: "COMPONENT",
    pos: 8,
  };

  const mapAccountsUserTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Map Downstream Accounts",
    content:
      "Map this user to accounts in other gardens for their alias accounts. This allows the user to switch between accounts when they have access to multiple gardens.",
    layer: "COMPONENT",
    pos: 9,
  };

  const addRemoveRolesUserTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Add/Remove Roles",
    content:
      "Add or remove roles from this user. Roles determine the permissions available to the user.",
    layer: "COMPONENT",
    pos: 10,
  };

  const changePasswordUserTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Change Password",
    content: "Change the password for this user.",
    layer: "COMPONENT",
    pos: 11,
  };

  const deleteUserTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Delete User",
    content: "Delete this user from the Garden.",
    layer: "COMPONENT",
    pos: 11,
  };

  function userNameTemplate(rowData: User) {
    if (rowData.protected) {
      return (
        <span {...GenerateTourProps(protectedUserTourStep)}>
          <FontAwesomeIcon icon="user-shield" title="Protected User" />{" "}
          {rowData.username}
        </span>
      );
    }
    if (rowData.file_generated) {
      return (
        <span {...GenerateTourProps(fileGeneratedUserTourStep)}>
          <FontAwesomeIcon icon="user-tag" title="File Generated User" />{" "}
          {rowData.username}
        </span>
      );
    }
    return (
      <span {...GenerateTourProps(userUserTourStep)}>
        <FontAwesomeIcon icon="user" title="Regular User" /> {rowData.username}
      </span>
    );
  }
  function maxPermissionTemplate(rowData: User) {
    const permissions = [] as string[];

    if (rowData.local_roles && rowData.local_roles.length > 0) {
      for (const role of rowData.local_roles) {
        if (role.permission && !permissions.includes(role.permission)) {
          permissions.push(role.permission);
        }
      }
    }

    if (permissions.length === 0) {
      return (
        <span {...GenerateTourProps(maxPermissionUserTourStep)}>None</span>
      );
    }
    if (permissions.includes("GARDEN_ADMIN")) {
      return (
        <span {...GenerateTourProps(maxPermissionUserTourStep)}>
          GARDEN_ADMIN
        </span>
      );
    }
    if (permissions.includes("PLUGIN_ADMIN")) {
      return (
        <span {...GenerateTourProps(maxPermissionUserTourStep)}>
          PLUGIN_ADMIN
        </span>
      );
    }
    if (permissions.includes("OPERATOR")) {
      return (
        <span {...GenerateTourProps(maxPermissionUserTourStep)}>OPERATOR</span>
      );
    }
    return (
      <span {...GenerateTourProps(maxPermissionUserTourStep)}>READ_ONLY</span>
    );
  }

  function lastAuthenticatedTemplate(rowData: User) {
    if (rowData?.metadata?.last_authentication) {
      const date = new Date(rowData.metadata.last_authentication);
      return (
        <span {...GenerateTourProps(lastAuthenticatedUserTourStep)}>
          {date.toUTCString()}
        </span>
      );
    }
    return (
      <span {...GenerateTourProps(lastAuthenticatedUserTourStep)}>Never</span>
    );
  }

  function localRolesTemplate(rowData: User) {
    return (
      <div {...GenerateTourProps(localRolesUserTourStep)}>
        {rowData?.local_roles?.map((role: Role) => (
          <Chip
            key={role.id}
            label={role.name}
            pt={{ root: { "aria-label": undefined } }}
          />
        ))}
      </div>
    );
  }

  function upstreamRolesTemplate(rowData: User) {
    return (
      <div {...GenerateTourProps(upstreamRolesUserTourStep)}>
        {rowData?.upstream_roles?.map((role: Role) => (
          <Chip
            key={role.id}
            label={role.name}
            pt={{ root: { "aria-label": undefined } }}
          />
        ))}
      </div>
    );
  }

  function aliasGardenAcountsTemplate(rowData: User) {
    if (
      !rowData?.user_alias_mapping ||
      rowData.user_alias_mapping.length === 0
    ) {
      return (
        <span {...GenerateTourProps(aliasGardenAccountsUserTourStep)}>
          None
        </span>
      );
    }
    return (
      <DataTable
        value={rowData.user_alias_mapping}
        size="small"
        {...GenerateTourProps(aliasGardenAccountsUserTourStep)}
      >
        <Column field="target_garden" header="Garden Name" />
        <Column field="username" header="Account Name" />
      </DataTable>
    );
  }

  function userActionsTemplate(rowData: User) {
    return (
      <div className="flex flex-row gap-2">
        <AccessButton
          onClick={() => {
            if (rowData.username) {
              if (
                rowData.metadata?.has_token === undefined ||
                rowData.metadata?.has_token === false
              ) {
                showToast({
                  severity: "warn",
                  summary: "Revoke Token",
                  detail: `No active token to revoke for ${rowData?.username}`,
                  life: 3000,
                });
              }

              RevokeToken(rowData.username)
                .then(() => {
                  loadUsers();
                  showToast({
                    severity: "info",
                    summary: "Revoke Token",
                    detail: `Successfully revoked token for ${rowData.username}`,
                    life: 3000,
                  });
                })
                .catch((error) => {
                  console.error("Error Revoking Token", error);
                  showToast({
                    severity: "error",
                    summary: "Revoke Token",
                    detail: `Error revoking token for ${rowData.username}`,
                    life: 3000,
                  });
                });
            }
          }}
          tooltip={`Revoke Token for User ${rowData.username}`}
          data-testid={`revoke-user-${rowData.id}`}
          tooltipOptions={{ position: "bottom" }}
          {...GenerateTourProps(revokeTokenUserTourStep)}
          config={config}
          permission="GARDEN_ADMIN"
          isGlobal={true}
        >
          <FontAwesomeIcon icon="arrow-right-from-bracket" />
        </AccessButton>
        <AccessButton
          onClick={() => {
            setAccountMappingUser(rowData);
            setShowAccountMappingDialog(true);
          }}
          tooltip={`Map Associated Accounts for ${rowData.username}`}
          tooltipOptions={{ position: "bottom" }}
          data-testid={`map-accounts-user-${rowData.id}`}
          {...GenerateTourProps(mapAccountsUserTourStep)}
          config={config}
          permission="GARDEN_ADMIN"
          isGlobal={true}
        >
          <FontAwesomeIcon icon="globe" />
        </AccessButton>
        {(rowData.protected === undefined || rowData.protected === false) && (
          <AccessButton
            onClick={() => {
              setRolesUser(rowData);
              setShowRolesDialog(true);
            }}
            tooltip={`Add/Remove Roles for User ${rowData.username}`}
            data-testid={`roles-user-${rowData.id}`}
            tooltipOptions={{ position: "bottom" }}
            {...GenerateTourProps(addRemoveRolesUserTourStep)}
            config={config}
            permission="GARDEN_ADMIN"
            isGlobal={true}
          >
            <FontAwesomeIcon icon="user-plus" />
          </AccessButton>
        )}
        {(rowData.protected === undefined || rowData.protected === false) && (
          <AccessButton
            onClick={() => {
              if (rowData.username) {
                setPasswordUsername(rowData.username);
                setShowPasswordDialog(true);
              }
            }}
            tooltip={`Change Password for User ${rowData.username}`}
            tooltipOptions={{ position: "bottom" }}
            data-testid={`change-password-user-${rowData.id}`}
            {...GenerateTourProps(changePasswordUserTourStep)}
            config={config}
            permission="GARDEN_ADMIN"
            isGlobal={true}
          >
            <FontAwesomeIcon icon="key" />
          </AccessButton>
        )}

        {(rowData.protected === undefined || rowData.protected === false) && (
          <AccessButton
            onClick={() => {
              const accept = () => {
                if (rowData.username) {
                  DeleteUser(rowData.username)
                    .then(() => {
                      showToast({
                        severity: "info",
                        summary: "Delete User",
                        detail: `Successfully deleted ${rowData.username}`,
                        life: 3000,
                      });
                      loadUsers();
                    })
                    .catch((error) =>
                      showToast({
                        severity: "error",
                        summary: "Error",
                        detail: `Error attempting to delete user: ${error}`,
                        life: 3000,
                      }),
                    );
                }
              };

              const reject = () => {};

              if (rowData.username) {
                confirmDialog({
                  message: `Are you sure you want to delete user ${rowData.username}?`,
                  header: "Confirmation",
                  icon: "pi pi-exclamation-triangle",
                  defaultFocus: "accept",
                  accept,
                  reject,
                });
              }
            }}
            tooltip={`Delete User ${rowData.username}`}
            tooltipOptions={{ position: "bottom" }}
            data-testid={`delete-user-${rowData.id}`}
            {...GenerateTourProps(deleteUserTourStep)}
            config={config}
            permission="GARDEN_ADMIN"
            isGlobal={true}
          >
            <FontAwesomeIcon icon="trash" />
          </AccessButton>
        )}
      </div>
    );
  }

  function activeUserTemplate(rowData: User) {
    if (rowData.metadata?.has_token) {
      return (
        <Tag
          severity="success"
          value="Active"
          {...GenerateTourProps(activeTokenUserTourStep)}
        />
      );
    }
    return (
      <Tag
        severity="danger"
        value="Inactive"
        {...GenerateTourProps(activeTokenUserTourStep)}
      />
    );
  }

  function handleRescan() {
    RescanUsers()
      .then(() => {
        loadUsers();
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
          detail: `Error rescanning users: ${error}`,
          life: 3000,
        });
      });
  }

  const loadUsers = useCallback(() => {
    setLoading(true);

    GetUsers()
      .then((users: Array<User>) => {
        setUsers(users);
        setLoading(false);
      })
      .catch((error) => {
        setLoading(false);
        showToast({
          severity: "error",
          summary: "Error",
          detail: `Error fetching users: ${error}`,
          life: 3000,
        });
      });
  }, [users]);

  useEffect(() => {
    loadUsers();
  }, []);

  useEffect(() => {
    ClearTourSteps(tourStepsRef, tourPrefix, tourUuid);
    AddTourStep(tourStepsRef, rescanUserTourStep);
    AddTourStep(tourStepsRef, createUserTourStep);

    if (users.length > 0) {
      // Always present for all users
      AddTourStep(tourStepsRef, maxPermissionUserTourStep);
      AddTourStep(tourStepsRef, lastAuthenticatedUserTourStep);
      AddTourStep(tourStepsRef, localRolesUserTourStep);
      AddTourStep(tourStepsRef, upstreamRolesUserTourStep);
      AddTourStep(tourStepsRef, aliasGardenAccountsUserTourStep);
      AddTourStep(tourStepsRef, activeTokenUserTourStep);
      AddTourStep(tourStepsRef, revokeTokenUserTourStep);
      AddTourStep(tourStepsRef, mapAccountsUserTourStep);

      // Icons need to search
      for (const user of users) {
        if (user.protected) {
          AddTourStep(tourStepsRef, protectedUserTourStep);
        } else {
          AddTourStep(tourStepsRef, addRemoveRolesUserTourStep);
          AddTourStep(tourStepsRef, changePasswordUserTourStep);
          AddTourStep(tourStepsRef, deleteUserTourStep);

          if (user.file_generated) {
            AddTourStep(tourStepsRef, fileGeneratedUserTourStep);
          } else {
            AddTourStep(tourStepsRef, userUserTourStep);
          }
        }
      }
    }
    return () => {
      ClearTourSteps(tourStepsRef, tourPrefix, tourUuid);
    };
  }, [users]);

  return (
    <div>
      <div className="flex items-end ml-2 page-header">
        <h1 className="flex-1">User Management</h1>

        <div>
          <AccessButton
            onClick={handleRescan}
            label="Rescan Users"
            data-testid="rescan-btn"
            className="mr-2"
            {...GenerateTourProps(rescanUserTourStep)}
            config={config}
            permission="GARDEN_ADMIN"
            isGlobal={true}
          />
          <AccessButton
            onClick={() => {
              setShowCreateUserDialog(true);
            }}
            label="Create User"
            data-testid="create-btn"
            className="mr-2"
            {...GenerateTourProps(createUserTourStep)}
            config={config}
            permission="GARDEN_ADMIN"
            isGlobal={true}
          />
        </div>
      </div>
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
      {showPasswordDialog && passwordUsername && (
        <UserChangePassword
          username={passwordUsername}
          isAdmin={true}
          showPasswordDialog={showPasswordDialog}
          setShowPasswordDialog={setShowPasswordDialog}
          callback={loadUsers}
        />
      )}
      {showRolesDialog && rolesUser && (
        <UserChangeRoles
          user={rolesUser}
          showRolesDialog={showRolesDialog}
          setShowRolesDialog={setShowRolesDialog}
          callback={loadUsers}
        />
      )}

      {showAccountMappingDialog && accountMappingUser && (
        <UserChangeAccountMapping
          user={accountMappingUser}
          config={config}
          showAccountMappingDialog={showAccountMappingDialog}
          setShowAccountMappingDialog={setShowAccountMappingDialog}
          callback={loadUsers}
        />
      )}

      {showCreateUserDialog && (
        <UserCreate
          showCreateUserDialog={showCreateUserDialog}
          setShowCreateUserDialog={setShowCreateUserDialog}
          callback={loadUsers}
        />
      )}

      <DataTable
        data-testid="user-datatable"
        value={users}
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
        <Column
          field="username"
          sortable
          header="Username"
          body={userNameTemplate}
        />
        <Column header="Max Permission" body={maxPermissionTemplate} />
        <Column header="Last Authenticated" body={lastAuthenticatedTemplate} />
        <Column header="Local Roles" body={localRolesTemplate} />
        <Column header="Upstream Roles" body={upstreamRolesTemplate} />
        <Column
          header="Alias Garden Accounts"
          body={aliasGardenAcountsTemplate}
        />
        <Column header="Active Token" body={activeUserTemplate} />
        <Column header="Actions" body={userActionsTemplate} />
      </DataTable>
    </div>
  );
}

export default UserIndex;
