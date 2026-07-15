import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import Button from "@mui/material/Button";
import Divider from "@mui/material/Divider";
import Popover from "@mui/material/Popover";
import Typography from "@mui/material/Typography";
import { RefObject, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";

import { ColumnField, FilterColumn } from "../models/EnhancedTableModels";
import { EnhancedTableFilterOptions } from "./EnhancedTableFilterOptions";

export const EnhancedTableFilterSelect = ({
  columns,
  columnFilters,
  columnFiltersRef,
  updateColumnFilters,
  anchor,
  setShowFilter,
  addColumn,
  triggerReload,
}: {
  columns: ColumnField[];
  columnFilters: FilterColumn[];
  columnFiltersRef: RefObject<FilterColumn[]>;
  updateColumnFilters: (filters: FilterColumn[]) => void;
  anchor: HTMLButtonElement | undefined;
  setShowFilter(filter: boolean): void;
  addColumn: string;
  triggerReload: () => void;
}) => {
  // Return Popover

  const addFilter = (defaultColumn?: string) => {
    updateColumnFilters([
      ...columnFilters,
      { id: uuidv4(), column: defaultColumn } as FilterColumn,
    ]);
  };

  const clearFilters = () => {
    const runReload = columnFilters.some(
      (filter) =>
        filter.value !== undefined &&
        (typeof filter.value !== "string" || filter.value !== ""),
    );
    updateColumnFilters([]);
    if (runReload) {
      triggerReload();
    }
  };

  useEffect(() => {
    if (columnFilters.length === 0) {
      addFilter(addColumn);
    }
  }, []);

  return (
    <Popover
      id={`filter-options`}
      open={true}
      anchorEl={anchor}
      onClose={() => setShowFilter(false)}
      anchorOrigin={{
        vertical: "bottom",
        horizontal: "left",
      }}
    >
      <Typography sx={{ p: 2 }}>Filter Table</Typography>
      {columnFilters &&
        columnFilters.map((filter) => (
          <EnhancedTableFilterOptions
            id={filter.id}
            columns={columns}
            columnFilters={columnFilters}
            columnFiltersRef={columnFiltersRef}
            updateColumnFilters={updateColumnFilters}
            triggerReload={triggerReload}
          />
        ))}

      <Divider />
      <div className="flex mt-2 mb-2">
        <div className="flex-1 ml-2">
          <Button variant="outlined" onClick={() => addFilter()}>
            <FontAwesomeIcon icon="plus" />
            Add Filter
          </Button>
        </div>
        <div className="flex-2 mr-2">
          <Button variant="outlined" onClick={clearFilters}>
            <FontAwesomeIcon icon="trash" /> Remove All
          </Button>
        </div>
      </div>
    </Popover>
  );
};
