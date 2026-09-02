import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Box, Grid } from "@mui/material";
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
  triggerReload,
  addColumn,
}: {
  columns: ColumnField[];
  columnFilters: FilterColumn[];
  columnFiltersRef: RefObject<FilterColumn[]>;
  updateColumnFilters: (filters: FilterColumn[]) => void;
  anchor: HTMLButtonElement | undefined;
  setShowFilter: (filter: boolean) => void;
  triggerReload: () => void;
  addColumn?: string;
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
            <Box component="span" sx={{ ml: 1 }}>
              Add Filter
            </Box>
          </Button>
        </Grid>
        <Grid sx={{ mr: 2 }}>
          <Button variant="outlined" onClick={clearFilters}>
            <FontAwesomeIcon icon="trash" />
            <Box component="span" sx={{ ml: 1 }}>
              Remove All
            </Box>
          </Button>
        </Grid>
      </Grid>
      <Divider sx={{ my: 2 }} />
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
