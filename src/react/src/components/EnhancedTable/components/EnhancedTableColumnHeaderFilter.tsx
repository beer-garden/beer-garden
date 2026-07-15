import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import IconButton from "@mui/material/IconButton";
import Tooltip from "@mui/material/Tooltip";
import { RefObject, useRef, useState } from "react";

import { ColumnField, FilterColumn } from "../models/EnhancedTableModels";
import { EnhancedTableFilterSelect } from "./EnhancedTableFilterSelect";

export const EnhancedTableColumnHeaderFilter = ({
  column,
  columns,
  columnFilters,
  columnFiltersRef,
  updateColumnFilters,
  triggerReload,
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
  triggerReload: () => void;
}) => {
  const [filterMenuAnchor, setFilterMenuAnchor] = useState<
    HTMLElement | undefined
  >(undefined);
  const filterMenuOpen = Boolean(filterMenuAnchor);
  const handleFilterMenuOpen = (event: React.MouseEvent<HTMLButtonElement>) => {
    setFilterMenuAnchor(event.currentTarget);
    setShowFilter(true);
  };
  const handleFilterMenuClose = (show: boolean) => {
    if (show === false) {
      setFilterMenuAnchor(undefined);
    }
    setShowFilter(show);
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
          <FontAwesomeIcon icon="filter" />
        </IconButton>
      </Tooltip>
      {showFilter && (
        <EnhancedTableFilterSelect
          columns={columns}
          columnFilters={columnFilters}
          columnFiltersRef={columnFiltersRef}
          updateColumnFilters={updateColumnFilters}
          anchor={filterAnchorRef.current}
          setShowFilter={handleFilterMenuClose}
          addColumn={column.id}
          triggerReload={triggerReload}
        />
      )}
    </>
  );
};
