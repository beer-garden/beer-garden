import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Grid } from "@mui/material";
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
  setShowFilter: (filter: boolean) => void;
  addColumn: string;
  triggerReload: () => void;
}) => {
  const addFilter = (defaultColumn?: string) => {
    updateColumnFilters([
      ...columnFiltersRef.current,
      {
        id: uuidv4(),
        column: defaultColumn,
        highlighted: true,
      } as FilterColumn,
    ]);
  };

  const clearFilters = () => {
    const runReload = columnFiltersRef.current.some(
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
    if (
      columnFiltersRef.current.length === 0 ||
      !columnFiltersRef.current.some((filter) => filter.column === addColumn)
    ) {
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
      <Typography sx={{ p: 2 }}>Filter</Typography>

      <Grid container sx={{}}>
        <Grid size="grow" sx={{ ml: 2 }}>
          <Button variant="outlined" onClick={() => addFilter()}>
            <FontAwesomeIcon icon="plus" />
            Add Filter
          </Button>
        </Grid>
        <Grid sx={{ mr: 2 }}>
          <Button variant="outlined" onClick={clearFilters}>
            <FontAwesomeIcon icon="trash" /> Remove All
          </Button>
        </Grid>
      </Grid>
      <Divider sx={{ mb: 2, mt: 2 }} />
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
    </Popover>
  );
};
