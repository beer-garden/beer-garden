import { Alert, Box, Chip, Grid, Typography } from "@mui/material";
import { RefObject, useCallback, useEffect, useState } from "react";

import AccessButton from "../components/AccessButton";
import ConfirmDialog from "../components/ConfirmDialog";
import EnhancedTable from "../components/EnhancedTable/components/EnhancedTable";
import RoleCard from "../components/RoleCard";
import UserChangeAccountMapping from "../components/UserChangeAccountMapping";
import UserChangePassword from "../components/UserChangePassword";
import UserChangeRoles from "../components/UserChangeRoles";
import UserCreate from "../components/UserCreate";
import { Role, User } from "../models/brewtils-types";
import { Config, TourStepProps } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import { RevokeToken } from "../services/token_service";
import {
  AddTourStep,
  ClearTourSteps,
  GenerateTourProps,
} from "../services/tour_service";
import { DeleteUser, GetUsers, RescanUsers } from "../services/user_service";
import { FAIcon } from "../services/util_service";

function UserIndex({
  config,
  tourStepsRef,
}: {
  config: Config;
  tourStepsRef: RefObject<Array<TourStepProps>>;
}) {
  const showSnackbar = useSnackbar();
  const [users, setUsers] = useState<Array<User>>([]);
  const [loading, setLoading] = useState(false);

  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [passwordUsername, setPasswordUsername] = useState<string | undefined>(
    undefined,
  );

  const [deleteUsername, setDeleteUsername] = useState<string | undefined>(
    undefined,
  );

  const [showRolesDialog, setShowRolesDialog] = useState(false);
  const [rolesUser, setRolesUser] = useState<User | undefined>(undefined);

  const [showViewRolesDialog, setShowViewRolesDialog] = useState(false);
  const [showRole, setShowRole] = useState<Role | undefined>(undefined);

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
          <FAIcon icon="user-shield" title="Protected User" sx={{ mr: 1 }} />
          {rowData.username}
        </span>
      );
    }
    if (rowData.file_generated) {
      return (
        <span {...GenerateTourProps(fileGeneratedUserTourStep)}>
          <FAIcon icon="user-tag" title="File Generated User" sx={{ mr: 1 }} />
          {rowData.username}
        </span>
      );
    }
    return (
      <span {...GenerateTourProps(userUserTourStep)}>
        <FAIcon icon="user" title="Regular User" sx={{ mr: 1 }} />
        {rowData.username}
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

  function localRolesTemplate(rowData: User) {
    return (
      <div {...GenerateTourProps(localRolesUserTourStep)}>
        {rowData?.local_roles?.map((role: Role) => (
          <AccessButton
            id={role.id}
            label={role.name}
            onClick={() => {
              setShowRole(role);
              setShowViewRolesDialog(true);
            }}
            rounded
            color="info"
            tooltip={`View Local Role: ${role.name}`}
          >
            {role.name}
          </AccessButton>
        ))}
      </div>
    );
  }

  function upstreamRolesTemplate(rowData: User) {
    return (
      <div {...GenerateTourProps(upstreamRolesUserTourStep)}>
        {rowData?.upstream_roles?.map((role: Role) => (
          <AccessButton
            id={role.id}
            label={role.name}
            onClick={() => {
              setShowRole(role);
              setShowViewRolesDialog(true);
            }}
            rounded
            color="secondary"
            tooltip={`View Upstream Role: ${role.name}`}
          >
            {role.name}
          </AccessButton>
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
      <EnhancedTable
        data={rowData.user_alias_mapping}
        columns={[
          {
            id: "target_garden",
            field: "target_garden",
            label: "Garden Name",
            isString: true,
          },
          {
            id: "username",
            field: "username",
            label: "Account Name",
            isString: true,
          },
        ]}
        {...GenerateTourProps(aliasGardenAccountsUserTourStep)}
      />
    );
  }

  function userActionsTemplate(rowData: User) {
    const buttonSx = { mr: 1 };
    return (
      <Box sx={{ display: "flex" }}>
        <AccessButton
          sx={buttonSx}
          onClick={() => {
            if (rowData.username) {
              if (
                rowData.metadata?.has_token === undefined ||
                rowData.metadata?.has_token === false
              ) {
                showSnackbar({
                  severity: "warning",
                  summary: "Revoke Token",
                  detail: `No active token to revoke for ${rowData?.username}`,
                  life: 3000,
                });
              }

              RevokeToken(rowData.username)
                .then(() => {
                  loadUsers();
                  showSnackbar({
                    severity: "info",
                    summary: "Revoke Token",
                    detail: `Successfully revoked token for ${rowData.username}`,
                    life: 3000,
                  });
                })
                .catch((error) => {
                  console.error("Error Revoking Token", error);
                  showSnackbar({
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
          {...GenerateTourProps(revokeTokenUserTourStep)}
          config={config}
          permission="GARDEN_ADMIN"
          isGlobal={true}
        >
          <FAIcon icon="arrow-right-from-bracket" />
        </AccessButton>
        <AccessButton
          sx={buttonSx}
          onClick={() => {
            setAccountMappingUser(rowData);
            setShowAccountMappingDialog(true);
          }}
          tooltip={`Map Associated Accounts for ${rowData.username}`}
          data-testid={`map-accounts-user-${rowData.id}`}
          {...GenerateTourProps(mapAccountsUserTourStep)}
          config={config}
          permission="GARDEN_ADMIN"
          isGlobal={true}
        >
          <FAIcon icon="globe" />
        </AccessButton>
        {(rowData.protected === undefined || rowData.protected === false) && (
          <AccessButton
            sx={buttonSx}
            onClick={() => {
              setRolesUser(rowData);
              setShowRolesDialog(true);
            }}
            tooltip={`Add/Remove Roles for User ${rowData.username}`}
            data-testid={`roles-user-${rowData.id}`}
            {...GenerateTourProps(addRemoveRolesUserTourStep)}
            config={config}
            permission="GARDEN_ADMIN"
            isGlobal={true}
          >
            <FAIcon icon="user-plus" />
          </AccessButton>
        )}
        {(rowData.protected === undefined || rowData.protected === false) && (
          <AccessButton
            sx={buttonSx}
            onClick={() => {
              if (rowData.username) {
                setPasswordUsername(rowData.username);
                setShowPasswordDialog(true);
              }
            }}
            tooltip={`Change Password for User ${rowData.username}`}
            data-testid={`change-password-user-${rowData.id}`}
            {...GenerateTourProps(changePasswordUserTourStep)}
            config={config}
            permission="GARDEN_ADMIN"
            isGlobal={true}
          >
            <FAIcon icon="key" />
          </AccessButton>
        )}

        {(rowData.protected === undefined || rowData.protected === false) && (
          <AccessButton
            sx={buttonSx}
            onClick={() => {
              setDeleteUsername(rowData.username);
            }}
            tooltip={`Delete User ${rowData.username}`}
            data-testid={`delete-user-${rowData.id}`}
            {...GenerateTourProps(deleteUserTourStep)}
            config={config}
            permission="GARDEN_ADMIN"
            isGlobal={true}
          >
            <FAIcon icon="trash" />
          </AccessButton>
        )}
      </Box>
    );
  }

  function activeUserTemplate(rowData: User) {
    if (rowData.metadata?.has_token) {
      return (
        <Chip
          color="success"
          label="Active"
          {...GenerateTourProps(activeTokenUserTourStep)}
        />
      );
    }
    return (
      <Chip
        color="error"
        label="Inactive"
        {...GenerateTourProps(activeTokenUserTourStep)}
      />
    );
  }

  function handleRescan() {
    RescanUsers()
      .then(() => {
        loadUsers();
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
        showSnackbar({
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
    <>
      <Grid container sx={{ m: 1 }}>
        <Grid size="grow">
          <Typography variant="h2" component="h1">
            User Management
          </Typography>
        </Grid>
        <Grid sx={{ display: "flex", alignItems: "center" }}>
          <AccessButton
            onClick={handleRescan}
            label="Rescan Users"
            data-testid="rescan-btn"
            sx={{ mr: 2 }}
            {...GenerateTourProps(rescanUserTourStep)}
            config={config}
            permission="GARDEN_ADMIN"
            isGlobal={true}
          >
            Rescan Users
          </AccessButton>
          <AccessButton
            onClick={() => {
              setShowCreateUserDialog(true);
            }}
            label="Create User"
            data-testid="create-btn"
            sx={{ mr: 2 }}
            {...GenerateTourProps(createUserTourStep)}
            config={config}
            permission="GARDEN_ADMIN"
            isGlobal={true}
          >
            Create User
          </AccessButton>
        </Grid>
      </Grid>
      {config?.auth_enabled == false && (
        <Alert severity="error" sx={{ m: 2 }}>
          Warning - Beergarden authorization is currently disabled. Changes made
          here will be persisted, but permissions will not be enforced. Contact
          your administator to enable this feature.
        </Alert>
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

      {showViewRolesDialog && showRole && (
        <RoleCard
          targetRole={showRole}
          disabled={true}
          onClose={() => {
            setShowViewRolesDialog(false);
          }}
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

      <EnhancedTable
        data-testid="user-datatable"
        data={users}
        isLoading={loading}
        columns={[
          {
            id: "username",
            field: "username",
            label: "Username",
            isString: true,
            sortable: true,
            filterable: true,
            template: userNameTemplate,
          },
          {
            id: "max_permission",
            label: "Max Permission",
            isString: true,
            template: maxPermissionTemplate,
          },
          {
            id: "last_authentication",
            field: "metadata.last_authentication",
            label: "Last Authentication",
            isDate: true,
            sortable: true,
            filterable: true,
          },
          {
            id: "local_roles",
            field: "local_roles.name",
            label: "Local Roles",
            template: localRolesTemplate,
          },
          {
            id: "upstream_roles",
            field: "upstream_roles.name",
            label: "Upstream Roles",
            template: upstreamRolesTemplate,
          },
          {
            id: "alias_garden_accounts",
            field: "user_alias_mapping",
            label: "Alias Garden Accounts",
            template: aliasGardenAcountsTemplate,
          },
          {
            id: "active_token",
            field: "metadata.has_token",
            label: "Active Token",
            template: activeUserTemplate,
            isBoolean: true,
            sortable: true,
            filterable: true,
          },
          {
            id: "actions",
            label: "Actions",
            template: userActionsTemplate,
          },
        ]}
        defaultOrderBy="username"
        defaultOrder="desc"
      />
      {deleteUsername && (
        <ConfirmDialog
          open={true}
          setOpen={() => setDeleteUsername(undefined)}
          accept={() => {
            if (deleteUsername) {
              DeleteUser(deleteUsername)
                .then(() => {
                  showSnackbar({
                    severity: "info",
                    summary: "Delete User",
                    detail: `Successfully deleted ${deleteUsername}`,
                    life: 3000,
                  });
                  loadUsers();
                })
                .catch((error) =>
                  showSnackbar({
                    severity: "error",
                    summary: "Error",
                    detail: `Error attempting to delete user: ${error}`,
                    life: 3000,
                  }),
                );
            }
          }}
          reject={() => {}}
          message={`Are you sure you want to delete user ${deleteUsername}?`}
          header="Confirmation"
        />
      )}
    </>
  );
}

export default UserIndex;
