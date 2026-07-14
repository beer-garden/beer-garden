import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import Divider from "@mui/material/Divider";
import IconButton from "@mui/material/IconButton";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import Tooltip from "@mui/material/Tooltip";
import { RefObject, useEffect, useRef, useState } from "react";

import { ColumnField, FilterColumn } from "../models/EnhancedTableModels";
import { EnhancedTableFilterSelect } from "./EnhancedTableFilterSelect";

export const EnhancedTableColumnHeaderFilter = ({
  column,
  columns,
  columnFilters,
  columnFiltersRef,
  updateColumnFilters,
  order,
  setOrder,
  orderBy,
  setOrderBy,
}: {
  column: ColumnField;
  columns: ColumnField[];
  columnFilters: FilterColumn[];
  columnFiltersRef: RefObject<FilterColumn[]>;
  updateColumnFilters: (filters: FilterColumn[]) => void;
  order: "asc" | "desc";
  setOrder: (value: "asc" | "desc") => void;
  orderBy: string | undefined;
  setOrderBy: (value: string) => void;
}) => {
  const [filterMenuAnchor, setFilterMenuAnchor] = useState<
    HTMLElement | undefined
  >(undefined);
  const filterMenuOpen = Boolean(filterMenuAnchor);
  const handleFilterMenuOpen = (event: React.MouseEvent<HTMLButtonElement>) => {
    setFilterMenuAnchor(event.currentTarget);
  };
  const handleFilterMenuClose = () => {
    setFilterMenuAnchor(undefined);
  };

  const filterAnchorRef = useRef<HTMLButtonElement>(undefined);

  const [showFilter, setShowFilter] = useState(false);

  return (
    <>
      <Tooltip title={`Filter ${column.field}`} ref={filterAnchorRef}>
        <IconButton
          onClick={handleFilterMenuOpen}
          size="small"
          sx={{ ml: 2 }}
          aria-controls={
            filterMenuOpen ? `filter-menu-${column.field}` : undefined
          }
          aria-haspopup="true"
          aria-expanded={filterMenuOpen}
        >
          <FontAwesomeIcon icon="ellipsis-vertical" />
        </IconButton>
      </Tooltip>
      {showFilter && (
        <EnhancedTableFilterSelect
          columns={columns}
          columnFilters={columnFilters}
          columnFiltersRef={columnFiltersRef}
          updateColumnFilters={updateColumnFilters}
          anchor={filterAnchorRef.current}
          setShowFilter={setShowFilter}
        />
      )}
      <Menu
        id="filter_menu"
        anchorEl={filterAnchorRef.current}
        open={filterMenuOpen}
        onClose={handleFilterMenuClose}
      >
        {column.sortable && (
          <MenuItem
            onClick={() => {
              setOrder("asc");
              setOrderBy(column.id);
            }}
          >
            <div className="flex">
              {orderBy === column.id && order === "asc" && (
                <FontAwesomeIcon className="mr-2" icon="arrow-up" />
              )}
              Sort by ASC
            </div>
          </MenuItem>
        )}
        <MenuItem
          onClick={() => {
            setOrder("desc");
            setOrderBy(column.id);
          }}
        >
          <div className="flex">
            {orderBy === column.id && order === "desc" && (
              <FontAwesomeIcon className="mr-2" icon="arrow-down" />
            )}
            Sort by DESC
          </div>
        </MenuItem>
        <Divider />
        <MenuItem
          onClick={() => {
            setShowFilter(true);
            handleFilterMenuClose();
          }}
        >
          <div className="flex">
            <FontAwesomeIcon className="mr-2" icon="filter" />
            Filter
          </div>
        </MenuItem>
      </Menu>
    </>
  );
};
