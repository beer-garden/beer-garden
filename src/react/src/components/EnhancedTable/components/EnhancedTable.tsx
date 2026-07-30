import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import Paper from "@mui/material/Paper";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableFooter from "@mui/material/TableFooter";
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
  groupBy,
  flattenBy,
  header,
  footer,
  reloadTable,
  isLoading,
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
  groupBy?: string;
  flattenBy?: string;
  header?: React.ReactElement;
  footer?: React.ReactElement;
  reloadTable?: number;
  isLoading?: boolean;
}) => {
  const [displayData, setDisplayData] = useState<any[] | undefined>(undefined);
  const [displayGroupData, setDisplayGroupData] = useState<
    { group: string; data: any[] }[] | undefined
  >(undefined);

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
    (property: string) => (event: React.MouseEvent<unknown>) => {
      onRequestSort(event, property);
    };

  const columnData = (column: ColumnField, row: any) => {
    if (column.template) {
      return column.template(row);
    }
    if (column.field) {
      if (Object.hasOwn(row, column.field)) {
        if (column.isDate) {
          return formatDate(row?.[column.field]);
        }
        return row?.[column.field];
      }
    }
    return undefined;
  };

  const filterSortData = (data: any[]) => {
    if (data.length > 0){
      console.log("Run Filter")
    }
    const flatData = flattenByData([...data]);
    const filteredData = flatData.filter((record) => {
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
        let compare = Object.hasOwn(record, filter.column)
          ? record?.[filter.column]
          : undefined;

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
          if (typeof compare === "string" && typeof filter.value === "string") {
            return compare.startsWith(filter.value);
          }
        } else if (filter.modifier === "endswith") {
          if (typeof compare === "string" && typeof filter.value === "string") {
            return compare.endsWith(filter.value);
          }
        } else if (filter.modifier === "contains") {
          if (typeof compare === "string" && typeof filter.value === "string") {
            return compare.includes(filter.value);
          }
        } else if (filter.modifier === "not__contains") {
          if (typeof compare === "string" && typeof filter.value === "string") {
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
    });

    const startIndex = page * rowsPerPage;

    if (groupBy) {
      const groupedData = groupByData(filteredData);
      setDisplayFiltered(groupedData.length);
      // Sort Data, then groups

      const sortedGroupData = groupedData.map((group) => {
        return {
          group: group.group,
          data: group.data.sort((a, b) => {
            if (orderBy) {
              const field_a = Object.hasOwn(a, orderBy)
                ? a?.[orderBy]
                : undefined;
              const field_b = Object.hasOwn(b, orderBy)
                ? b?.[orderBy]
                : undefined;
              return order === "asc" ? field_a - field_b : field_b - field_a;
            }
            return 0;
          }),
        };
      });

      const sortedGroups = sortedGroupData.sort((a, b) => {
        if (orderBy) {
          const field_a = Object.hasOwn(a.data[0], orderBy)
            ? a.data[0]?.[orderBy]
            : undefined;
          const field_b = Object.hasOwn(b.data[0], orderBy)
            ? a.data[0]?.[orderBy]
            : undefined;
          return order === "asc" ? field_a - field_b : field_b - field_a;
        }
        return 0;
      });

      return sortedGroups.slice(startIndex, startIndex + rowsPerPage);
    }

    setDisplayFiltered(filteredData.length);
    const sortedData = filteredData.sort((a, b) => {
      if (orderBy) {
        const field_a = Object.hasOwn(a, orderBy) ? a?.[orderBy] : undefined;
        const field_b = Object.hasOwn(b, orderBy) ? b?.[orderBy] : undefined;
        return order === "asc" ? field_a - field_b : field_b - field_a;
      }
      return 0;
    });

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

  const flattenByData = (data: any[]) => {
    if (flattenBy) {
      const flattenRecords = [] as any[];
      for (const record of data){
        if (Object.hasOwn(record, flattenBy) && Array.isArray(record?.[flattenBy])){
          for (const flatten of record?.[flattenBy]){
            flattenRecords.push({...record, [flattenBy]:flatten});
          }
        } else {
          flattenRecords.push(record);
        }
      }
      return flattenRecords;
    }
    return data;
  };

  const groupByData = (data: any[]) => {
    const groupedData = [] as { group: string; data: any[] }[];
    if (groupBy) {    
      for (const record of data){
        if (Object.hasOwn(record, groupBy) ){
          if (groupedData.some((group) => group.group === record?.[groupBy])){
            groupedData.map((group) => {
              if (group.group === record?.[groupBy]){
                group.data.push(record);
              }
              return group;
            })
          } else {
            groupedData.push({group: record?.[groupBy], data: [record]});
          }
        }
      }
    }
    return groupedData;
  };
  // Data Updated Externally
  useEffect(() => {
    if (remoteFilter) {
      // Accept remote updates
      if (groupBy) {
        const filteredGroupedData =  groupByData(flattenByData(data));
        setDisplayGroupData(filteredGroupedData);
      } else {
        setDisplayData(flattenByData(data));
      }
    } else {
      // Local Filter
      if (groupBy) {
        const filteredGroupedData =  filterSortData(data);
        setDisplayGroupData(filteredGroupedData);
      } else {
        setDisplayData(filterSortData(data));
      }
    }
  }, [data]);

  // Table Filtering Changes or external reload requests
  useEffect(() => {
    if (remoteFilter) {
      remoteFilter(filters, orderBy, order, page, rowsPerPage);
    } else {
      if (groupBy) {
        const filteredGroupedData =  filterSortData(data);
        setDisplayGroupData(filteredGroupedData);
      } else {
        setDisplayData(filterSortData(data));
      }
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
      if (groupBy) {
        const filteredGroupedData =  filterSortData(data);
        setDisplayGroupData(filteredGroupedData);
      } else {
        setDisplayData(filterSortData(data));
      }
    }
  };

  return (
    <Box sx={{ position: "relative", width: "100%" }}>
      <TableContainer
        component={Paper}
        sx={{ position: "relative", opacity: isLoading ? 0.5 : 1 }}
      >
        {header}
        <Table>
          <TableHead>
            {columns.map((column) => (
              <TableCell
                key={column.id}
                align={column.isNumeric ? "right" : "left"}
                sortDirection={orderBy === column.id ? order : false}
              >
                <TableSortLabel
                  active={orderBy === column.id}
                  direction={orderBy === column.id ? order : "asc"}
                  onClick={createSortHandler(column.id)}
                >
                  {column.label}
                  {orderBy === column.id ? (
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

            {displayGroupData &&
              displayGroupData.map((group) => {
                if (group.data.length === 1) {
                  return (
                    <TableRow key={group.data[0].id ?? undefined}>
                      {columns.map((column) => (
                        <TableCell>
                          {columnData(column, group.data[0])}
                        </TableCell>
                      ))}
                    </TableRow>
                  );
                }
                if (group.data.length > 1) {
                  return group.data.map((groupData, index) => (
                    <TableRow key={group.data[0].id ?? undefined}>
                      {columns.map((column) => {
                        if (column.field === groupBy) {
                          if (index === 0) {
                            return (<TableCell rowSpan={group.data.length}>
                              {columnData(column, groupData)}
                            </TableCell>);
                          } else {
                            return;
                          }
                        } else {
                          return (
                            <TableCell>{columnData(column, groupData)}</TableCell>
                          );
                        }
                      })}
                    </TableRow>
                  ));
                }
              })}
          </TableBody>
          <TableFooter>
            <TableRow>
              <TablePagination
                rowsPerPageOptions={[5, 10, 25]}
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
                ActionsComponent={EnhancedTablePaginationActions}
                labelDisplayedRows={defaultLabelDisplayedRows}
              />
            </TableRow>
          </TableFooter>
        </Table>

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
