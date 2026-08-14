import { Skeleton } from "@mui/material";
import { useTreeItemModel } from "@mui/x-tree-view/hooks";
import { TreeViewItemId } from "@mui/x-tree-view/models";
import { RichTreeView, RichTreeViewProps } from "@mui/x-tree-view/RichTreeView";
import {
  TreeItemCheckbox,
  TreeItemContent,
  TreeItemIconContainer,
  TreeItemRoot,
} from "@mui/x-tree-view/TreeItem";
import { TreeItemDragAndDropOverlay } from "@mui/x-tree-view/TreeItemDragAndDropOverlay";
import { TreeItemIcon } from "@mui/x-tree-view/TreeItemIcon";
import { TreeItemProvider } from "@mui/x-tree-view/TreeItemProvider";
import {
  useTreeItem,
  UseTreeItemParameters,
} from "@mui/x-tree-view/useTreeItem";
import { forwardRef, ReactElement, useState } from "react";

export type ExtendedTreeItemProps = {
  data?: any;
  id?: string;
  label?: string;
  children?: ExtendedTreeItemProps[];
};

interface CustomTreeItemProps
  extends
    Omit<UseTreeItemParameters, "rootRef">,
    Omit<React.HTMLAttributes<HTMLLIElement>, "onFocus"> {}

function TreeMenu<T extends ExtendedTreeItemProps, M extends boolean = false>({
  itemTemplate,
  changeSelected,
  disableToggle,
  expandAll,
  isLoading,
  ...richTreeProps
}: {
  itemTemplate?: (node: ExtendedTreeItemProps) => ReactElement;
  changeSelected: (id: string) => void;
  disableToggle?: boolean;
  expandAll?: boolean;
  isLoading?: boolean;
} & RichTreeViewProps<T, M>) {
  const getAllItemsWithChildrenItemIds = () => {
    const itemIds: TreeViewItemId[] = [];
    const registerItemId = (item: ExtendedTreeItemProps) => {
      if (item.children?.length) {
        if (item.id) {
          itemIds.push(item.id);
        }
        item.children.forEach(registerItemId);
      }
    };

    richTreeProps.items.forEach(registerItemId);

    return itemIds;
  };

  const [expandedItems, setExpandedItems] = useState<string[]>(
    expandAll ? getAllItemsWithChildrenItemIds() : [],
  );

  const handleExpandedItemsChange = (
    event: React.SyntheticEvent | null,
    itemIds: string[],
  ) => {
    setExpandedItems(itemIds);
  };

  const handleItemSelectionToggle = (
    _event: React.SyntheticEvent | null,
    itemId: string,
    isSelected: boolean,
  ) => {
    if (isSelected) {
      changeSelected(itemId);
    }
  };

  const CustomTreeItem = forwardRef(function CustomTreeItem(
    props: CustomTreeItemProps,
    ref: React.Ref<HTMLLIElement>,
  ) {
    const { id, itemId, label, disabled, children, ...other } = props;

    const {
      getContextProviderProps,
      getRootProps,
      getContentProps,
      getIconContainerProps,
      getCheckboxProps,
      getDragAndDropOverlayProps,
      status,
    } = useTreeItem({ id, itemId, children, label, disabled, rootRef: ref });

    const hasChildren = Array.isArray(children) && children.length > 0;

    const item = useTreeItemModel<ExtendedTreeItemProps>(itemId)!;
    return (
      <TreeItemProvider {...getContextProviderProps()}>
        <TreeItemRoot
          {...getRootProps(other)}
          tabIndex={0}
          role={hasChildren ? "group" : "treeitem"}
          aria-checked={undefined}
          {...(disableToggle !== true ? {} : { "aria-expanded": undefined })}
        >
          <TreeItemContent {...getContentProps()}>
            {disableToggle !== true && (
              <TreeItemIconContainer {...getIconContainerProps()}>
                <TreeItemIcon status={status} />
              </TreeItemIconContainer>
            )}
            <TreeItemCheckbox {...getCheckboxProps()} />
            {itemTemplate && itemTemplate(item)}
            {itemTemplate === undefined && item.label}
            <TreeItemDragAndDropOverlay {...getDragAndDropOverlayProps()} />
          </TreeItemContent>
          {(status.expanded || disableToggle === true) && children}
        </TreeItemRoot>
      </TreeItemProvider>
    );
  });

  return (
    <>
      {isLoading === true && (
        <Skeleton
          variant="rectangular"
          width={210}
          height={"100%"}
          sx={richTreeProps?.sx}
        />
      )}
      {(isLoading === undefined || isLoading === false) && (
        <RichTreeView
          slots={{ item: CustomTreeItem }}
          onItemSelectionToggle={handleItemSelectionToggle}
          expandedItems={expandedItems}
          onExpandedItemsChange={handleExpandedItemsChange}
          {...richTreeProps}
        />
      )}
    </>
  );
}

export default TreeMenu;
