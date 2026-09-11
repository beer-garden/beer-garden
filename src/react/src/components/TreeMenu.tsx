import { MenuItem, MenuList, MenuListProps, Skeleton } from "@mui/material";
import { ReactElement, useEffect, useState } from "react";

export type TreeMenuItemProps = {
  data?: any;
  id?: string;
  label?: string;
  depth?: number;
  children?: TreeMenuItemProps[];
};

function TreeMenu({
  itemTemplate,
  changeSelected,
  isLoading,
  treeItems,
  selectedItem,
  ...menuProps
}: {
  itemTemplate?: (node: TreeMenuItemProps) => ReactElement;
  changeSelected: (id: string) => void;
  isLoading?: boolean;
  treeItems?: TreeMenuItemProps[] | any[];
  selectedItem?: string;
} & MenuListProps) {
  const [options, setOptions] = useState<any[] | undefined>([]);
  const [selected, setSelected] = useState<string | undefined>(selectedItem);

  useEffect(() => {
    if (selected) {
      changeSelected(selected);
    }
  }, [selected]);

  useEffect(() => {
    if (selectedItem) {
      setSelected(selectedItem);
    }
  }, [selectedItem]);

  useEffect(() => {
    if (isLoading !== true) {
      // Parse Tree Items

      const parseItems = (
        item: TreeMenuItemProps,
        parsedOptions: TreeMenuItemProps[],
        depth: number,
      ) => {
        const { children, ...node } = item;

        parsedOptions.push({ ...node, depth: depth });

        if (children) {
          for (const child of children) {
            parseItems(child, parsedOptions, depth + 1);
          }
        }
        return parsedOptions;
      };

      const parsedOptions = [] as TreeMenuItemProps[];

      if (treeItems) {
        for (const item of treeItems) {
          parseItems(item, parsedOptions, 0);
        }
      }
      setOptions(parsedOptions);
      if (selected === undefined && parsedOptions.length > 0) {
        setSelected(parsedOptions[0].id);
      }
    }
  }, [isLoading, treeItems]);

  const onSelected = (item: TreeMenuItemProps) => {
    setSelected(item.id);
  };

  return (
    <>
      {isLoading === true && (
        <Skeleton
          variant="rectangular"
          width={210}
          height={"100%"}
          sx={menuProps?.sx}
        />
      )}
      {(isLoading === undefined || isLoading === false) && (
        <MenuList {...menuProps}>
          {options?.map((option: TreeMenuItemProps) => (
            <MenuItem
              key={option.id}
              selected={selected === option.id}
              onClick={() => onSelected(option)}
              sx={{
                ml: option.depth ? option.depth * 2 : 0,
                "&:hover, &:focus, &.Mui-focusVisible, &.Mui-selected.Mui-focusVisible, &.Mui-selected:hover":
                  {
                    backgroundColor: (theme) => theme.palette.action.hover,
                  },
                "&.Mui-selected": {
                  backgroundColor: (theme) => theme.palette.action.selected,
                },
              }}
            >
              {itemTemplate ? itemTemplate(option) : option.label}
            </MenuItem>
          ))}
        </MenuList>
      )}
    </>
  );
}

export default TreeMenu;
