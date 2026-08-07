import {
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  TextField,
  Typography,
} from "@mui/material";
import { useEffect, useRef, useState } from "react";

import { AliasUserMap, Garden, User } from "../models/brewtils-types";
import { Config } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import { GetRootGarden } from "../services/garden_service";
import { UpdateUserAliasMapping } from "../services/user_service";
import { FAIcon } from "../services/util_service";
import AccessButton from "./AccessButton";
import EnhancedTable from "./EnhancedTable/components/EnhancedTable";

function UserChangeAccountMapping({
  user,
  config,
  showAccountMappingDialog,
  setShowAccountMappingDialog,
  callback,
}: {
  user: User;
  config: Config;
  showAccountMappingDialog: boolean;
  setShowAccountMappingDialog: (show: boolean) => void;
  callback?: () => void;
}) {
  const showSnackbar = useSnackbar();
  const [gardenAccounts, setGardenAccounts] = useState<Array<any>>([]);
  const gardenAccountsRef = useRef<Array<any>>([]);

  function mapGardensToAccounts(
    gardens: Array<Garden>,
    defaultUsername?: string,
    parent?: string,
    depth?: number,
  ) {
    const accounts = [] as Array<any>;

    if (gardens.length === 0) {
      return accounts;
    }

    for (const garden of gardens) {
      if (garden.name) {
        const gardenDefaultUsername =
          garden.id &&
          user.user_alias_mapping &&
          user.user_alias_mapping.some(
            (alias) => alias.target_garden === garden.name,
          )
            ? (user.user_alias_mapping.filter(
                (alias) => alias.target_garden === garden.name,
              )[0]?.username ?? defaultUsername)
            : defaultUsername;

        accounts.push({
          garden: garden.name,
          username:
            garden.id &&
            user.user_alias_mapping &&
            user.user_alias_mapping.some(
              (alias) => alias.target_garden === garden.name,
            )
              ? user.user_alias_mapping.filter(
                  (alias) => alias.target_garden === garden.name,
                )[0]?.username
              : undefined,
          defaultUsername: gardenDefaultUsername,
          depth: depth ?? 0,
          parent: parent,
        });
        if (garden.children) {
          for (const account of mapGardensToAccounts(
            garden.children,

            gardenDefaultUsername,
            garden.name,
            (depth ?? 1) + 1,
          )) {
            accounts.push(account);
          }
        }
      }
    }
    return accounts;
  }

  function handleAccountMappingDialogClose() {
    setShowAccountMappingDialog(false);
  }

  function extractAliasMappingFromAccounts(
    accounts: Array<any>,
  ): Array<AliasUserMap> {
    const aliasMapping = [] as Array<AliasUserMap>;

    for (const account of accounts) {
      if (account.username && account.garden) {
        aliasMapping.push({
          target_garden: account.garden,
          username: account.username,
        });
      }
    }

    return aliasMapping;
  }

  function updateAccounts() {
    const newAliasMapping = extractAliasMappingFromAccounts(
      gardenAccountsRef.current,
    );
    if (user.username) {
      UpdateUserAliasMapping(user.username, newAliasMapping)
        .then(() => {
          if (callback) {
            callback();
          }
          handleAccountMappingDialogClose();
        })
        .catch((error) => {
          console.error("Error updating user account mapping:", error);
          showSnackbar({
            severity: "error",
            summary: "Error",
            detail: `Failed to update account mapping for user ${user.username}`,
            life: 3000,
          });
        });
    }
  }

  const onEditorValueChange = (updatedNode: any, value: any) => {
    const newNodes = JSON.parse(JSON.stringify(gardenAccountsRef.current));
    for (const node of newNodes) {
      if (node.garden === updatedNode.garden) {
        node.username = value;
      }
    }

    if (
      value !== null &&
      value !== undefined &&
      value !== "" &&
      value.length > 0
    ) {
      for (const childNode of newNodes || []) {
        if (childNode.parent === updatedNode.garden) {
          childNode.defaultUsername = value;
        }
      }
    }

    gardenAccountsRef.current = newNodes;
    setGardenAccounts(gardenAccountsRef.current);
  };

  const accountEditorTemplate = (node: any) => {
    return (
      <TextField
        placeholder={node.defaultUsername}
        value={node.username}
        onChange={(e) => onEditorValueChange(node, e.target.value)}
        slotProps={{
          input: {
            "aria-label": `Edit User Account ${node.garden}`,
          },
        }}
      />
    );
  };

  useEffect(() => {
    GetRootGarden(config, {})
      .then((garden) => {
        const accountsTree = [] as Array<any>;
        if (garden && garden.children) {
          mapGardensToAccounts(garden.children, user?.username).forEach(
            (account) => {
              accountsTree.push(account);
            },
          );
        }
        for (const alias of user.user_alias_mapping || []) {
          if (
            alias.target_garden &&
            !accountsTree.some(
              (account) => account.garden === alias.target_garden,
            )
          ) {
            accountsTree.push({
              garden: alias.target_garden,
              username: alias.username,
              defaultUsername: user.username,
            });
          }
        }
        gardenAccountsRef.current = accountsTree;
        setGardenAccounts(gardenAccountsRef.current);
      })
      .catch((error) => {
        console.error("Error fetching root garden accounts:", error);
        showSnackbar({
          severity: "error",
          summary: "Error",
          detail: `Error fetching root garden accounts: ${error}`,
          life: 3000,
        });
      });
  }, []);

  return (
    <Dialog
      data-testid="change-account-mapping-dialog"
      open={showAccountMappingDialog}
      onClose={() => {
        handleAccountMappingDialogClose();
      }}
    >
      <DialogTitle>
        <Grid container>
          <Grid size="grow">{`Update Account Mapping for ${user.username}`}</Grid>
          <Grid>
            <AccessButton
              sx={{ ml: 2 }}
              onClick={handleAccountMappingDialogClose}
            >
              <FAIcon icon="xmark" />
            </AccessButton>
          </Grid>
        </Grid>
      </DialogTitle>

      <DialogContent>
        <EnhancedTable
          data={gardenAccounts}
          displayAll
          columns={[
            {
              id: "garden_name",
              label: "Garden",
              field: "garden",
              isString: true,
              template: (row) => (
                <Typography sx={{ ml: row.depth ? row.depth * 2 : 0 }}>
                  {row.garden}
                </Typography>
              ),
            },
            {
              id: "username",
              label: "Alias Account",
              field: "username",
              isString: true,
              template: accountEditorTemplate,
            },
          ]}
        />
      </DialogContent>

      <DialogActions>
        <AccessButton onClick={handleAccountMappingDialogClose} label="Close">
          Close
        </AccessButton>
        <AccessButton
          data-testid={`submit-btn-dialog`}
          color="error"
          onClick={updateAccounts}
          label="Submit"
        >
          Submit
        </AccessButton>
      </DialogActions>
    </Dialog>
  );
}

export default UserChangeAccountMapping;
