import { useTreeItemModel } from "@mui/x-tree-view/hooks";
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
  ...richTreeProps
}: {
  itemTemplate: (node: ExtendedTreeItemProps) => ReactElement;
  changeSelected: (id: string) => void;
} & RichTreeViewProps<T, M>) {
  const handleItemSelectionToggle = (
    _event: React.SyntheticEvent | null,
    itemId: string,
    isSelected: boolean,
  ) => {
    if (isSelected) {
      changeSelected(itemId);
    }
  };

  const [expandedItems, setExpandedItems] = useState<string[]>([]);

  const handleExpandedItemsChange = (
    event: React.SyntheticEvent | null,
    itemIds: string[],
  ) => {
    setExpandedItems(itemIds);
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

    const item = useTreeItemModel<ExtendedTreeItemProps>(itemId)!;

    return (
      <TreeItemProvider {...getContextProviderProps()}>
        <TreeItemRoot {...getRootProps(other)}>
          <TreeItemContent {...getContentProps()}>
            <TreeItemIconContainer {...getIconContainerProps()}>
              <TreeItemIcon status={status} />
            </TreeItemIconContainer>
            <TreeItemCheckbox {...getCheckboxProps()} />
            {itemTemplate && itemTemplate(item)}
            {itemTemplate === undefined && item.label}
            <TreeItemDragAndDropOverlay {...getDragAndDropOverlayProps()} />
          </TreeItemContent>
          {children}
        </TreeItemRoot>
      </TreeItemProvider>
    );
  });

  return (
    <RichTreeView
      slots={{ item: CustomTreeItem }}
      onItemSelectionToggle={handleItemSelectionToggle}
      {...richTreeProps}
    />
  );
}

export default TreeMenu;
