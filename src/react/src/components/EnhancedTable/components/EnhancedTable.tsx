import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import Paper from "@mui/material/Paper";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TablePagination from "@mui/material/TablePagination";
import TableRow from "@mui/material/TableRow";
import TableSortLabel from "@mui/material/TableSortLabel";
import { visuallyHidden } from "@mui/utils";
import dayjs from "dayjs";
import { useEffect, useRef, useState } from "react";

import { ColumnField, FilterColumn } from "../models/EnhancedTableModels";
import { EnhancedTableColumnHeaderFilter } from "./EnhancedTableColumnHeaderFilter";
import { EnhancedTablePaginationActions } from "./EnhancedTablePaginationActions";

const EnhancedTable = ({
  data,
  dataLength,
  totalDataLength,
  columns,
  remoteFilter,
  defaultOrderBy,
  defaultOrder,
  header,
  footer,
  reloadTable,
  isLoading,
  displayAll,
  ...props
}: {
  data: any[];
  dataLength?: number;
  totalDataLength?: number;
  columns: ColumnField[];
  remoteFilter?: (
    columnFilters?: FilterColumn[],
    orderBy?: string,
    order?: "asc" | "desc",
    page?: number,
    rowsPerPage?: number,
  ) => void;
  defaultOrderBy?: string;
  defaultOrder?: "asc" | "desc";
  header?: React.ReactElement;
  footer?: React.ReactElement;
  reloadTable?: number;
  isLoading?: boolean;
  displayAll?: boolean;
}) => {
  const [displayData, setDisplayData] = useState<any[] | undefined>(undefined);
  const [displayFiltered, setDisplayFiltered] = useState<number | undefined>(
    undefined,
  );

  const [order, setOrder] = useState<"asc" | "desc">(defaultOrder ?? "asc");
  const [orderBy, setOrderBy] = useState<string | undefined>(defaultOrderBy);

  const columnFiltersRef = useRef<FilterColumn[]>([]);
  const [filters, setFilters] = useState<FilterColumn[]>([]);

  const updateFilters = (newFilters: FilterColumn[]) => {
    columnFiltersRef.current = newFilters;
    setFilters(newFilters);
  };

  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(5);

  const [pageRecords, setPageRecords] = useState(false);

  const onRequestSort = (
    event: React.MouseEvent<unknown>,
    property: string,
  ) => {
    const isAsc = orderBy === property && order === "asc";
    setOrder(isAsc ? "desc" : "asc");
    setOrderBy(property);
  };

  const formatDate = (value: string) => {
    const date = new Date(value);
    return date.toLocaleDateString() + " " + date.toLocaleTimeString();
  };

  const createSortHandler =
    (property?: string) => (event: React.MouseEvent<unknown>) => {
      if (property) {
        onRequestSort(event, property);
      }
    };

  const findValue = (path: string, obj: any) => {
    return path
      .replace(/\[(\d+)\]/g, ".$1") // convert [0] to .0
      .split(".")
      .filter(Boolean)
      .reduce((acc, key) => (acc == null ? undefined : acc[key]), obj);
  };

  const columnData = (column: ColumnField, row: any) => {
    if (column.template) {
      return column.template(row);
    }
    if (column.field) {
      const columnValue = findValue(column.field, row);

      if (columnValue !== undefined && columnValue !== null) {
        if (column.isDate) {
          return formatDate(columnValue);
        }
        return columnValue;
      }
    }
    return undefined;
  };

  const filterSortData = (data: any[]) => {
    const filteredData = [
      ...data.filter((record) => {
        if (
          columnFiltersRef.current === undefined ||
          columnFiltersRef.current.length === 0
        ) {
          return true;
        }

        return columnFiltersRef.current.every((filter: FilterColumn) => {
          // No Modifier
          if (filter.modifier === undefined) {
            return true;
          }

          // Is Number and Is Date Empty
          if (filter.value === undefined) {
            return true;
          }

          // Is String Empty
          if (typeof filter.value === "string" && filter.value.length === 0) {
            return true;
          }

          // Is Array Empty
          if (
            typeof filter.value === "object" &&
            Array.isArray(filter.value) &&
            filter.value.length === 0
          ) {
            return true;
          }

          // Grab Compare Value
          let compare = findValue(filter.column, record);

          if (compare === undefined) {
            return false;
          }

          if (filter.isNumeric) {
            if (typeof compare === "string") {
              compare = Number(compare);
            }
          } else if (filter.isDate) {
            if (typeof compare === "string") {
              compare = dayjs(new Date(compare));
            }
          }

          if (filter.modifier === "eq") {
            return filter.value === compare;
          } else if (filter.modifier === "neq") {
            return filter.value !== compare;
          } else if (filter.modifier === "startswith") {
            if (
              typeof compare === "string" &&
              typeof filter.value === "string"
            ) {
              return compare.startsWith(filter.value);
            }
          } else if (filter.modifier === "endswith") {
            if (
              typeof compare === "string" &&
              typeof filter.value === "string"
            ) {
              return compare.endsWith(filter.value);
            }
          } else if (filter.modifier === "contains") {
            if (
              typeof compare === "string" &&
              typeof filter.value === "string"
            ) {
              return compare.includes(filter.value);
            }
          } else if (filter.modifier === "not__contains") {
            if (
              typeof compare === "string" &&
              typeof filter.value === "string"
            ) {
              return !compare.includes(filter.value);
            }
          } else if (filter.modifier === "gt") {
            return compare > filter.value;
          } else if (filter.modifier === "gte") {
            return compare >= filter.value;
          } else if (filter.modifier === "lt") {
            return compare < filter.value;
          } else if (filter.modifier === "lte") {
            return compare <= filter.value;
          } else if (filter.modifier === "in") {
            if (
              typeof compare === "string" &&
              typeof filter.value === "object" &&
              Array.isArray(filter.value)
            ) {
              return filter.value.some((field) => field === compare);
            }
          } else if (filter.modifier === "nin") {
            if (
              typeof compare === "string" &&
              typeof filter.value === "object" &&
              Array.isArray(filter.value)
            ) {
              return !filter.value.some((field) => field === compare);
            }
          } else if (filter.modifier === "exists") {
            if (filter.value === "true") {
              // Value Present
              if (compare === undefined) {
                return false;
              }

              if (
                typeof compare === "string" &&
                (compare === "" || compare.trim().length === 0)
              ) {
                return false;
              }

              return true;
            } else {
              // Value is empty
              if (compare === undefined) {
                return true;
              }
              if (
                typeof compare === "string" &&
                (compare === "" || compare.trim().length === 0)
              ) {
                return true;
              }

              return false;
            }
          }

          // Default response if field is populated
          return false;
        });
      }),
    ];

    setDisplayFiltered(filteredData.length);
    const orderByField = columns.find(
      (column) => column.field === orderBy,
    )?.field;
    const sortedData = [...filteredData].sort((a, b) => {
      if (orderByField) {
        const field_a = findValue(orderByField, a);
        const field_b = findValue(orderByField, b);
        if (
          columns.some((column) => column.field === orderBy && column.isNumeric)
        ) {
          return order === "asc"
            ? Number(field_a) - Number(field_b)
            : Number(field_b) - Number(field_a);
        }
        if (
          columns.some((column) => column.field === orderBy && column.isDate)
        ) {
          return order === "asc"
            ? new Date(field_a).getTime() - new Date(field_b).getTime()
            : new Date(field_b).getTime() - new Date(field_a).getTime();
        }
        if (
          columns.some((column) => column.field === orderBy && column.isString)
        ) {
          return order === "asc"
            ? (field_a as string).localeCompare(field_b as string)
            : (field_b as string).localeCompare(field_a as string);
        }
        return order === "asc" ? field_a - field_b : field_b - field_a;
      }
      return 0;
    });

    if (displayAll === true) {
      return sortedData;
    }

    const startIndex = page * rowsPerPage;
    return sortedData.slice(startIndex, startIndex + rowsPerPage);
  };

  const handleChangePage = (
    event: React.MouseEvent<HTMLButtonElement> | null,
    newPage: number,
  ) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Data Updated Externally
  useEffect(() => {
    if (remoteFilter) {
      // Accept remote updates
      setDisplayData(data);
      setPageRecords(dataLength !== undefined && dataLength > 5);
    } else {
      // Local Filter
      setPageRecords(data.length > 5);
      setDisplayData(filterSortData(data));
    }
  }, [data]);

  // Table Filtering Changes or external reload requests
  useEffect(() => {
    if (remoteFilter) {
      remoteFilter(filters, orderBy, order, page, rowsPerPage);
    } else {
      setDisplayData(filterSortData(data));
    }
  }, [reloadTable, order, orderBy, page, rowsPerPage]);

  function defaultLabelDisplayedRows({
    from,
    to,
    count,
  }: {
    from: number;
    to: number;
    count: number;
  }) {
    return `Showing ${from} to ${to} of ${count !== -1 ? count : `more than ${to}`} entries ${totalDataLength ? (dataLength === totalDataLength ? "" : `(Filtered from ${totalDataLength} entries)`) : data.length === displayFiltered ? "" : `(Filtered from ${data.length} entries)`}`;
  }

  const filterTriggerReload = () => {
    setPage(0);
    if (remoteFilter) {
      remoteFilter(filters, orderBy, order, 0, rowsPerPage);
    } else {
      setDisplayData(filterSortData(data));
    }
  };

  return (
    <Box sx={{ position: "relative", width: "100%" }}>
      <TableContainer
        component={Paper}
        sx={{ position: "relative", opacity: isLoading ? 0.5 : 1 }}
      >
        {header}
        <Table {...props}>
          <TableHead>
            <TableRow>
            {columns.map((column) => (
              <TableCell
                key={column.id}
                sortDirection={orderBy === column.field ? order : false}
              >
                <TableSortLabel
                  active={orderBy === column.field}
                  direction={orderBy === column.field ? order : "asc"}
                  onClick={createSortHandler(column.field)}
                >
                  {column.label}
                  {orderBy === column.field ? (
                    <Box component="span" sx={visuallyHidden}>
                      {order === "desc"
                        ? "sorted descending"
                        : "sorted ascending"}
                    </Box>
                  ) : null}
                </TableSortLabel>
                {column.sortable && (
                  <>
                    <EnhancedTableColumnHeaderFilter
                      column={column}
                      columns={columns}
                      columnFilters={filters}
                      columnFiltersRef={columnFiltersRef}
                      updateColumnFilters={updateFilters}
                      order={order}
                      setOrder={setOrder}
                      orderBy={orderBy}
                      setOrderBy={setOrderBy}
                      triggerReload={filterTriggerReload}
                    />
                  </>
                )}
              </TableCell>
            ))}
            </TableRow>
          </TableHead>

          <TableBody>
            {displayData &&
              displayData.map((row) => (
                <TableRow key={row.id ?? undefined}>
                  {columns.map((column) => (
                    <TableCell>{columnData(column, row)}</TableCell>
                  ))}
                </TableRow>
              ))}
          </TableBody>
        </Table>
        {(displayAll === undefined || displayAll === false) && (
          <TablePagination
            rowsPerPageOptions={pageRecords ? [5, 10, 25] : []}
            colSpan={3}
            count={dataLength ?? data.length}
            rowsPerPage={rowsPerPage}
            page={page}
            slotProps={{
              select: {
                inputProps: {
                  "aria-label": "rows per page",
                },
                native: true,
              },
            }}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
            ActionsComponent={
              pageRecords ? EnhancedTablePaginationActions : () => <></>
            }
            labelDisplayedRows={defaultLabelDisplayedRows}
          />
        )}
        {footer}
      </TableContainer>
      {isLoading && (
        <Box
          sx={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            zIndex: 10, // Higher than the table
          }}
        >
          <CircularProgress />
        </Box>
      )}
    </Box>
  );
};

export default EnhancedTable;
