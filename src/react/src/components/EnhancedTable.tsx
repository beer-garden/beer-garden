import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Divider from "@mui/material/Divider";
import IconButton from "@mui/material/IconButton";
import InputBase from "@mui/material/InputBase";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import Paper from "@mui/material/Paper";
import Popover from "@mui/material/Popover";
import { useTheme } from "@mui/material/styles";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableFooter from "@mui/material/TableFooter";
import TableHead from "@mui/material/TableHead";
import TablePagination from "@mui/material/TablePagination";
import TableRow from "@mui/material/TableRow";
import TableSortLabel from "@mui/material/TableSortLabel";
import TextField from "@mui/material/TextField";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import { visuallyHidden } from "@mui/utils";
import { useEffect, useRef, useState } from "react";

import AccessButton from "./AccessButton";

export interface ColumnField {
  id: string;
  label: string;

  field?: string;
  template?: (row: any) => React.ReactElement;

  sortable?: boolean;

  filterable?: boolean;

  isNumeric?: boolean;
  isString?: boolean;
  isDate?: boolean;
}

interface TablePaginationActionsProps {
  count: number;
  page: number;
  rowsPerPage: number;
  onPageChange: (
    event: React.MouseEvent<HTMLButtonElement>,
    newPage: number,
  ) => void;
}

const StringFilters = [
  {
    value: "eq",
    label: "=",
  },
  {
    value: "neq",
    label: "!=",
  },
];

function TablePaginationActions(props: TablePaginationActionsProps) {
  const theme = useTheme();
  const { count, page, rowsPerPage, onPageChange } = props;

  const handleFirstPageButtonClick = (
    event: React.MouseEvent<HTMLButtonElement>,
  ) => {
    onPageChange(event, 0);
  };

  const handleBackButtonClick = (
    event: React.MouseEvent<HTMLButtonElement>,
  ) => {
    onPageChange(event, page - 1);
  };

  const handleNextButtonClick = (
    event: React.MouseEvent<HTMLButtonElement>,
  ) => {
    onPageChange(event, page + 1);
  };

  const handleLastPageButtonClick = (
    event: React.MouseEvent<HTMLButtonElement>,
  ) => {
    onPageChange(event, Math.max(0, Math.ceil(count / rowsPerPage) - 1));
  };

  return (
    <Box sx={{ flexShrink: 0, ml: 2.5 }}>
      <IconButton
        onClick={handleFirstPageButtonClick}
        disabled={page === 0}
        aria-label="first page"
      >
        {theme.direction === "rtl" ? (
          <FontAwesomeIcon icon="angles-right" />
        ) : (
          <FontAwesomeIcon icon="angles-left" />
        )}
      </IconButton>
      <IconButton
        onClick={handleBackButtonClick}
        disabled={page === 0}
        aria-label="previous page"
      >
        {theme.direction === "rtl" ? (
          <FontAwesomeIcon icon="angle-right" />
        ) : (
          <FontAwesomeIcon icon="angle-left" />
        )}
      </IconButton>
      <IconButton
        onClick={handleNextButtonClick}
        disabled={page >= Math.ceil(count / rowsPerPage) - 1}
        aria-label="next page"
      >
        {theme.direction === "rtl" ? (
          <FontAwesomeIcon icon="angle-left" />
        ) : (
          <FontAwesomeIcon icon="angle-right" />
        )}
      </IconButton>
      <IconButton
        onClick={handleLastPageButtonClick}
        disabled={page >= Math.ceil(count / rowsPerPage) - 1}
        aria-label="last page"
      >
        {theme.direction === "rtl" ? (
          <FontAwesomeIcon icon="angles-left" />
        ) : (
          <FontAwesomeIcon icon="angles-right" />
        )}
      </IconButton>
    </Box>
  );
}

interface FilterColumn {
  id: string;
  value: string | Date | number | undefined;
  modifier?: string;
}

const FilterSelect = ({
  columns,
  columnFilters,
  anchor,
  setShowFilter,
}: {
  columns: ColumnField[];
  columnFilters: FilterColumn[];
  anchor: HTMLButtonElement | undefined;
  setShowFilter(filter: boolean): void;
}) => {
  // Return Popover

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
      <div className="flex mb-2 ml-2">
        <FontAwesomeIcon icon="x" className="mr-2" />
        <TextField
          className="mr-2"
          id="outlined-select-column"
          select
          label="Select"
          defaultValue={columns[0].id}
          helperText="Column"
        >
          {columns.map((filterColumn) => (
            <MenuItem key={filterColumn.id} value={filterColumn.id}>
              {filterColumn.id}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          className="mr-2"
          id="outlined-select-currency"
          select
          label="Select"
          defaultValue="EQ"
          helperText="Operator"
        >
          {StringFilters.map((option) => (
            <MenuItem key={option.value} value={option.value}>
              {option.label}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          className="mr-2"
          id="filter-value"
          label="Value"
          defaultValue=""
          helperText="Filter Value"
          variant="filled"
        />
      </div>
      <Divider />
      <div className="flex mt-2 mb-2">
        <div className="flex-1 ml-2">
          <Button variant="outlined">
            <FontAwesomeIcon icon="plus" />
            Add Filter
          </Button>
        </div>
        <div className="flex-2 mr-2">
          <Button variant="outlined">
            <FontAwesomeIcon icon="trash" /> Remove All
          </Button>
        </div>
      </div>
    </Popover>
  );
};

const ColumnHeaderFilter = ({
  column,
  getFilterValue,
  updateFilter,
  columns,
  columnFilters,
}: {
  column: ColumnField;
  getFilterValue(id: string): void;
  updateFilter(id: string, value: string, modifier: string): void;
  columns: ColumnField[];
  columnFilters: FilterColumn[];
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
        <FilterSelect
          columns={columns}
          columnFilters={columnFilters}
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
        {/* <MenuItem>
              {column.isString && (
                <TextField
                  id={`${column.id}-filter`}
                  value={ getFilterValue(column.id)}
                  onChange={(e) => updateFilter(column.id, e.target.value, "eq")}
                  variant="standard"
                  placeholder={`Search...`}
                />
              )}
            </MenuItem> */}
        <MenuItem
          onClick={() => {
            handleFilterMenuClose();
          }}
        >
          <div className="flex">
            <FontAwesomeIcon className="mr-2" icon="arrow-up" />
            Sort by ASC
          </div>
        </MenuItem>
        <MenuItem
          onClick={() => {
            handleFilterMenuClose();
          }}
        >
          <div className="flex">
            <FontAwesomeIcon className="mr-2" icon="arrow-down" />
            Sort by DESC
          </div>
        </MenuItem>
        <MenuItem
          onClick={() => {
            handleFilterMenuClose();
          }}
        >
          <div className="flex">
            <FontAwesomeIcon className="mr-2" icon="rotate-left" />
            Unsort
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

const EnhancedTable = ({
  data,
  dataLength,
  columns,
  remoteFilter,
  defaultOrderBy,
  header,
  footer,
  reloadTable,
}: {
  data: any[];
  dataLength?: number;
  columns: ColumnField[];
  remoteFilter?: (
    columnFilters?: any[],
    orderBy?: string,
    order?: "asc" | "desc",
    page?: number,
    rowsPerPage?: number,
  ) => void;
  defaultOrderBy?: string;
  header?: React.ReactElement;
  footer?: React.ReactElement;
  reloadTable?: number;
}) => {
  const [displayData, setDisplayData] = useState<any[] | undefined>(undefined);

  const [order, setOrder] = useState<"asc" | "desc">("asc");
  const [orderBy, setOrderBy] = useState<string | undefined>(defaultOrderBy);

  const columnFiltersRef = useRef<FilterColumn[]>([]);
  const [filters, setFilters] = useState<FilterColumn[]>([]);

  const [activeFilter, setActiveFilter] = useState<string | undefined>(
    undefined,
  );

  const updateFilter = (
    id: string,
    value: string | Date | number | undefined,
    modifier?: string,
  ) => {
    if (columnFiltersRef?.current.some((filter) => filter.id === id)) {
      columnFiltersRef.current = columnFiltersRef?.current.map((filter) => {
        if (filter.id === id && filter.modifier === modifier) {
          filter.value = value;
        }
        return filter;
      });
    } else {
      columnFiltersRef?.current.push({
        id: id,
        value: value,
        modifier: modifier,
      });
    }
    setFilters(columnFiltersRef.current);
  };

  const getFilterValue = (id: string) => {
    for (const filter of columnFiltersRef.current) {
      if (filter.id === id) {
        return filter.value;
      }
    }

    return undefined;
  };

  const clearFilters = () => {
    columnFiltersRef.current = [];
    for (const column of columns) {
      if (column.filterable) {
        columnFiltersRef.current.push({
          id: column.id,
          value: undefined,
          modifier: "eq",
        });
      }
    }
    setFilters(columnFiltersRef.current);
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
    const filteredData = [...data];
    const sortedData = filteredData.sort((a, b) => {
      if (orderBy) {
        const field_a = Object.hasOwn(a, orderBy) ? a?.[orderBy] : undefined;
        const field_b = Object.hasOwn(b, orderBy) ? b?.[orderBy] : undefined;
        return order === "asc" ? field_a - field_b : field_b - field_a;
      }
      return 0;
    });

    const startIndex = page * rowsPerPage;
    return sortedData.slice(startIndex, startIndex + rowsPerPage);
  };

  const handleChangePage = (
    event: React.MouseEvent<HTMLButtonElement> | null,
    newPage: number,
  ) => {
    setPage(newPage);
  };

  // const Filter = ({ column }: { column: ColumnField }) => {

  //   return (
  //     <>

  //     <Tooltip title={`Filter ${column.field}`}>
  //         <IconButton
  //           onClick={handleFilterMenuOpen}
  //           size="small"
  //           sx={{ ml: 2 }}
  //           aria-controls={open ? 'account-menu' : undefined}
  //           aria-haspopup="true"
  //           aria-expanded={open}
  //         >
  //           <FontAwesomeIcon icon="filter"/>
  //         </IconButton>
  //       </Tooltip>
  //       </>
  //   );

  //   return (
  //     <Button onClick={(event) => {
  //       setAnchorEl(event.currentTarget);
  //       setActiveFilter(column.id)
  //     }}>
  //       <FontAwesomeIcon icon="filter"/>
  //     </Button>
  //   )

  //   // const columnFilterValue = getFilterValue(column.id);

  //   // if (column.isString){
  //   //   return (
  //   //     <div className="flex space-x-2">
  //   //     <TextField
  //   //       id={`${column.id}-filter`}
  //   //       value={ getFilterValue(column.id)}
  //   //       onChange={(e) => updateFilter(column.id, e.target.value, "eq")}
  //   //       variant="standard"
  //   //       placeholder={`Search...`}
  //   //     />

  //   //     {/* {StringFilters.map((option) => (
  //   //         <MenuItem key={option.value} value={option.value}>
  //   //           {option.label}
  //   //         </MenuItem>
  //   //       ))} */}
  //   //     </div>
  //   //   )
  //   // }

  // };

  const handleChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Initial Load
  useEffect(() => {
    clearFilters();
  }, []);

  // Data Updated Externally
  useEffect(() => {
    if (remoteFilter) {
      // Accept remote updates
      setDisplayData(data);
    } else {
      // Local Filter
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
  }, [reloadTable, filters, order, orderBy, page, rowsPerPage]);

  return (
    <>
      <TableContainer component={Paper}>
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
                    <ColumnHeaderFilter
                      column={column}
                      columns={columns}
                      columnFilters={filters}
                      getFilterValue={getFilterValue}
                      updateFilter={updateFilter}
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
          </TableBody>
          <TableFooter>
            <TableRow>
              <TablePagination
                rowsPerPageOptions={[5, 10, 25, { label: "All", value: -1 }]}
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
                ActionsComponent={TablePaginationActions}
              />
            </TableRow>
          </TableFooter>
        </Table>

        {footer}
      </TableContainer>
    </>
  );
};

export default EnhancedTable;
