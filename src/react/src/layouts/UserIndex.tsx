import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "primereact/button";
import { Chip } from "primereact/chip";
import { Column } from "primereact/column";
import { ConfirmDialog, confirmDialog } from "primereact/confirmdialog";
import { DataTable, SortOrder } from "primereact/datatable";
import { Message } from "primereact/message";
import { Tag } from "primereact/tag";
import { Toast } from "primereact/toast";
import { useCallback, useEffect, useRef, useState } from "react";

import UserChangeAccountMapping from "../components/UserChangeAccountMapping";
import UserChangePassword from "../components/UserChangePassword";
import UserChangeRoles from "../components/UserChangeRoles";
import UserCreate from "../components/UserCreate";
import { Role, User } from "../models/brewtils-types";
import { Config } from "../models/models";
import { RevokeToken } from "../services/token_service";
import { DeleteUser, GetUsers, RescanUsers } from "../services/user_service";

function UserIndex({ config }: { config: Config }) {
  const toast = useRef<Toast>(null);
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

  function userNameTemplate(rowData: User) {
    if (rowData.protected) {
      return (
        <span>
          <FontAwesomeIcon icon="user-shield" title="Protected User" />{" "}
          {rowData.username}
        </span>
      );
    }
    if (rowData.file_generated) {
      return (
        <span>
          <FontAwesomeIcon icon="user-tag" title="File Generated User" />{" "}
          {rowData.username}
        </span>
      );
    }
    return (
      <span>
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
      return <span>None</span>;
    }
    if (permissions.includes("GARDEN_ADMIN")) {
      return <span>GARDEN_ADMIN</span>;
    }
    if (permissions.includes("PLUGIN_ADMIN")) {
      return <span>PLUGIN_ADMIN</span>;
    }
    if (permissions.includes("OPERATOR")) {
      return <span>OPERATOR</span>;
    }
    return <span>READ_ONLY</span>;
  }

  function lastAuthenticatedTemplate(rowData: User) {
    if (rowData?.metadata?.last_authentication) {
      const date = new Date(rowData.metadata.last_authentication * 1000);
      return <span>{date.toUTCString()}</span>;
    }
    return <span>Never</span>;
  }

  function localRolesTemplate(rowData: User) {
    return (
      <div>
        {rowData?.local_roles?.map((role: Role) => (
          <Chip key={role.id} label={role.name} title={role.permission} />
        ))}
      </div>
    );
  }

  function upstreamRolesTemplate(rowData: User) {
    return (
      <div>
        {rowData?.upstream_roles?.map((role: Role) => (
          <Chip key={role.id} label={role.name} title={role.permission} />
        ))}
      </div>
    );
  }

  function aliasGardenAcountsTemplate(rowData: User) {
    if (
      !rowData?.user_alias_mapping ||
      rowData.user_alias_mapping.length === 0
    ) {
      return <span>None</span>;
    }
    return (
      <DataTable value={rowData.user_alias_mapping} size="small">
        <Column field="target_garden" header="Garden Name" />
        <Column field="username" header="Account Name" />
      </DataTable>
    );
  }

  function userActionsTemplate(rowData: User) {
    return (
      <div className="flex flex-row gap-2">
        <Button
          onClick={() => {
            if (rowData.username) {
              RevokeToken(rowData.username)
                .then(() => loadUsers())
                .catch((error) => console.error("Error Revoking Token", error));
            }
          }}
          tooltip={`Revoke Token for User ${rowData.username}`}
          data-testid={`revoke-user-${rowData.id}`}
          tooltipOptions={{ position: "bottom" }}
        >
          <FontAwesomeIcon icon="arrow-right-from-bracket" />
        </Button>
        <Button
          onClick={() => {
            setAccountMappingUser(rowData);
            setShowAccountMappingDialog(true);
          }}
          tooltip={`Map Associated Accounts for ${rowData.username}`}
          tooltipOptions={{ position: "bottom" }}
          data-testid={`map-accounts-user-${rowData.id}`}
        >
          <FontAwesomeIcon icon="globe" />
        </Button>
        {(rowData.protected === undefined || rowData.protected === false) && (
          <Button
            onClick={() => {
              setRolesUser(rowData);
              setShowRolesDialog(true);
            }}
            tooltip={`Add/Remove Roles for User ${rowData.username}`}
            data-testid={`roles-user-${rowData.id}`}
            tooltipOptions={{ position: "bottom" }}
          >
            <FontAwesomeIcon icon="user-plus" />
          </Button>
        )}
        {(rowData.protected === undefined || rowData.protected === false) && (
          <Button
            onClick={() => {
              if (rowData.username) {
                setPasswordUsername(rowData.username);
                setShowPasswordDialog(true);
              }
            }}
            tooltip={`Change Password for User ${rowData.username}`}
            tooltipOptions={{ position: "bottom" }}
            data-testid={`change-password-user-${rowData.id}`}
          >
            <FontAwesomeIcon icon="key" />
          </Button>
        )}

        {(rowData.protected === undefined || rowData.protected === false) && (
          <Button
            onClick={() => {
              const accept = () => {
                if (rowData.username) {
                  DeleteUser(rowData.username)
                    .then(() => {
                      toast.current?.show({
                        severity: "info",
                        summary: "Delete User",
                        detail: `Delete ${rowData.username} complete`,
                        life: 3000,
                      });
                      loadUsers();
                    })
                    .catch((error) =>
                      console.error("Error attempting to delete user", error),
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
          >
            <FontAwesomeIcon icon="trash" />
          </Button>
        )}
      </div>
    );
  }

  function activeUserTemplate(rowData: User) {
    if (rowData.metadata?.has_token) {
      return <Tag severity="success" value="Active" />;
    }
    return <Tag severity="danger" value="Inactive" />;
  }

  function handleRescan() {
    RescanUsers()
      .then(() => {
        loadUsers();
        toast.current?.show({
          severity: "info",
          summary: "Confirmation",
          detail: "Rescan complete",
          life: 3000,
        });
      })
      .catch((error) => {
        console.log("Error rescanning users", error);
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
        console.error("Error fetching users:", error);
        setLoading(false);
      });
  }, [users]);

  useEffect(() => {
    loadUsers();
  }, []);

  return (
    <div>
      <Toast ref={toast} />
      <ConfirmDialog />
      <div className="flex items-end ml-2 page-header">
        <h1 className="flex-1">User Management</h1>
        <div>
          <Button
            onClick={handleRescan}
            label="Rescan Users"
            data-testid="rescan-btn"
            className="mr-2"
          />
          <Button
            onClick={() => {
              setShowCreateUserDialog(true);
            }}
            label="Create User"
            data-testid="create-btn"
            className="mr-2"
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
        />
      )}
      {showPasswordDialog && passwordUsername && (
        <UserChangePassword
          username={passwordUsername}
          isAdmin={true}
          showPasswordDialog={showPasswordDialog}
          setShowPasswordDialog={setShowPasswordDialog}
          toast={toast}
          callback={loadUsers}
        />
      )}
      {showRolesDialog && rolesUser && (
        <UserChangeRoles
          user={rolesUser}
          showRolesDialog={showRolesDialog}
          setShowRolesDialog={setShowRolesDialog}
          toast={toast}
          callback={loadUsers}
        />
      )}

      {showAccountMappingDialog && accountMappingUser && (
        <UserChangeAccountMapping
          user={accountMappingUser}
          config={config}
          showAccountMappingDialog={showAccountMappingDialog}
          setShowAccountMappingDialog={setShowAccountMappingDialog}
          toast={toast}
          callback={loadUsers}
        />
      )}

      {showCreateUserDialog && (
        <UserCreate
          showCreateUserDialog={showCreateUserDialog}
          setShowCreateUserDialog={setShowCreateUserDialog}
          toast={toast}
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
