import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "primereact/button";
import { Column } from "primereact/column";
import { Dialog } from "primereact/dialog";
import { InputText } from "primereact/inputtext";
import { Toast } from "primereact/toast";
import { TreeTable } from "primereact/treetable";
import { RefObject, useEffect, useRef, useState } from "react";

import { AliasUserMap, Garden, User } from "../models/brewtils-types";
import { Config } from "../models/models";
import { GetRootGarden } from "../services/garden_service";
import { UpdateUserAliasMapping } from "../services/user_service";

function UserChangeAccountMapping({
  user,
  config,
  showAccountMappingDialog,
  setShowAccountMappingDialog,
  toast,
}: {
  user: User;
  config: Config;
  showAccountMappingDialog: boolean;
  setShowAccountMappingDialog: (show: boolean) => void;
  toast: RefObject<Toast | null>;
}) {
  const [gardenAccounts, setGardenAccounts] = useState<Array<any>>([]);
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
    const newAliasMapping = extractAliasMappingFromAccounts(gardenAccounts);
    if (user.username) {
      UpdateUserAliasMapping(user.username, newAliasMapping)
        .then(() => {
          handleAccountMappingDialogClose();
        })
        .catch((error) => {
          console.error("Error updating user account mapping:", error);
          toast.current?.show({
            severity: "error",
            summary: "Error",
            detail: `Failed to update account mapping for user ${user.username}`,
            life: 3000,
          });
        });
    }
  }

  const onEditorValueChange = (options: any, value: any) => {
    const newNodes = JSON.parse(JSON.stringify(gardenAccounts));
    const editedNode = findNodeByKey(newNodes, options.node.key);

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

    setGardenAccounts(newNodes);
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

  const accountEditor = (options: any) => {
    return (
      <InputText
        type="text"
        placeholder={options.rowData.defaultUsername}
        value={options.rowData[options.field]}
        onChange={(e) => onEditorValueChange(options, e.target.value)}
        onKeyDown={(e) => e.stopPropagation()}
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

        setGardenAccounts(accountsTree);
      })
      .catch((error) => {
        console.error("Error fetching root garden accounts:", error);
      });
  }, []);

  function accountNameTemplate(rowData: any) {
    const username = rowData.data.username;
    const defaultUsername = rowData.data.defaultUsername;

    if (username) {
      return (
        <div className="flex">
          <FontAwesomeIcon
            icon="user-gear"
            title="Account Mapping"
            className="mr-1"
          />
          {username}
          <FontAwesomeIcon icon="pencil" title="Edit" className="ml-1" />
        </div>
      );
    } else if (!username) {
      return (
        <div className="flex">
          <FontAwesomeIcon
            icon="user-slash"
            title="No Account Mapping"
            className="mr-1"
          />
          {defaultUsername}
          <FontAwesomeIcon icon="pencil" title="Edit" className="ml-1" />
        </div>
      );
    }
  }

  return (
    <Dialog
      data-testid="change-account-mapping-dialog"
      header={`Update Account Mapping for ${user.username}`}
      footer={
        <>
          <Button onClick={handleAccountMappingDialogClose}>Close</Button>
          <Button
            data-testid={`submit-btn-dialog`}
            severity="danger"
            onClick={updateAccounts}
          >
            Submit
          </Button>
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
          header="Account Name (Editable)"
          body={accountNameTemplate}
          editor={accountEditor}
        ></Column>
      </TreeTable>
    </Dialog>
  );
}

export default UserChangeAccountMapping;
