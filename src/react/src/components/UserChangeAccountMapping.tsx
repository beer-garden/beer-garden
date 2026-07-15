import { Column } from "primereact/column";
import { Dialog } from "primereact/dialog";
import { InputText } from "primereact/inputtext";
import { TreeTable } from "primereact/treetable";
import { useEffect, useRef, useState } from "react";

import { AliasUserMap, Garden, User } from "../models/brewtils-types";
import { Config } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import { GetRootGarden } from "../services/garden_service";
import { UpdateUserAliasMapping } from "../services/user_service";
import AccessButton from "./AccessButton";

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
  const seenGardens = useRef<Set<string>>(new Set());

  function mapGardensToAccounts(
    gardens: Array<Garden>,
    defaultUsername?: string,
  ): Array<any> {
    const accounts = [] as Array<any>;

    if (gardens.length === 0) {
      return accounts;
    }

    for (const garden of gardens) {
      if (garden.name) {
        seenGardens.current.add(garden.name);
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
          key: garden.name,
          data: {
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
          },

          expanded: true,
          children:
            garden?.children && garden.children.length > 0
              ? mapGardensToAccounts(garden.children, gardenDefaultUsername)
              : [],
        });
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
      if (account.data.username && account.data.garden) {
        aliasMapping.push({
          target_garden: account.data.garden,
          username: account.data.username,
        });
      }
      if (account.children && account.children.length > 0) {
        const childAliasMapping = extractAliasMappingFromAccounts(
          account.children,
        );
        aliasMapping.push(...childAliasMapping);
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

  const onEditorValueChange = (node: any, value: any) => {
    const newNodes = JSON.parse(JSON.stringify(gardenAccountsRef.current));
    const editedNode = findNodeByKey(newNodes, node.key);

    editedNode.data.username = value;

    if (
      value !== null &&
      value !== undefined &&
      value !== "" &&
      value.length > 0
    ) {
      for (const childNodes of editedNode.children || []) {
        if (childNodes.data.defaultUsername !== value) {
          childNodes.data.defaultUsername = value;
        }
      }
    }

    gardenAccountsRef.current = newNodes;
    setGardenAccounts(gardenAccountsRef.current);
  };

  const findNodeByKey = (nodes: Array<any>, key: string): any => {
    for (const node of nodes) {
      if (node.key === key) {
        return node;
      }
      if (node.children && node.children.length > 0) {
        const foundNode = findNodeByKey(node.children, key);
        if (foundNode) {
          return foundNode;
        }
      }
    }

    return undefined;
  };

  const accountEditorTemplate = (node: any) => {
    return (
      <InputText
        type="text"
        placeholder={node.data.defaultUsername}
        value={node.data.username}
        onChange={(e) => onEditorValueChange(node, e.target.value)}
        onKeyDown={(e) => e.stopPropagation()}
        data-testid={`edit-user-account-${node.data.garden}`}
      />
    );
  };

  useEffect(() => {
    seenGardens.current.clear();
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
            !seenGardens.current.has(alias.target_garden)
          ) {
            accountsTree.push({
              key: alias.target_garden,
              data: {
                garden: alias.target_garden,
                username: alias.username,
                defaultUsername: user.username,
              },
              expanded: true,
              children: [],
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
      header={`Update Account Mapping for ${user.username}`}
      footer={
        <>
          <AccessButton
            onClick={handleAccountMappingDialogClose}
            label="Close"
          />
          <AccessButton
            data-testid={`submit-btn-dialog`}
            severity="danger"
            onClick={updateAccounts}
            label="Submit"
          />
        </>
      }
      visible={showAccountMappingDialog}
      onHide={() => {
        handleAccountMappingDialogClose();
      }}
    >
      <TreeTable value={gardenAccounts}>
        <Column field="garden" header="Garden" expander></Column>
        <Column
          field="username"
          header="Account Name"
          body={accountEditorTemplate}
        ></Column>
      </TreeTable>
    </Dialog>
  );
}

export default UserChangeAccountMapping;
