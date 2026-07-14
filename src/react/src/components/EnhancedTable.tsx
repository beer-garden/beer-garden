import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Divider from "@mui/material/Divider";
import FormHelperText from "@mui/material/FormHelperText";
import IconButton from "@mui/material/IconButton";
import InputBase from "@mui/material/InputBase";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import Paper from "@mui/material/Paper";
import Popover from "@mui/material/Popover";
import Select, { SelectChangeEvent } from "@mui/material/Select";
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
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { DateTimePicker } from "@mui/x-date-pickers/DateTimePicker";
import { PickerValue } from "@mui/x-date-pickers/internals";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import dayjs, { Dayjs } from "dayjs";
import { ChangeEvent, RefObject, useEffect, useRef, useState } from "react";
import { v4 as uuidv4 } from "uuid";

import NumberField from "../components/NumberField";
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
  isArray?: boolean;

  options?: string[];
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

export interface FilterColumn {
  id: string;
  column: string;
  value: string | string[] | Dayjs | number | undefined;
  modifier?: string;
  isString?: boolean;
  isDate?: boolean;
  isNumeric?: boolean;
  isArray?: boolean;
  options?: string[];
}

const StringFilters = [
  {
    value: "eq",
    label: "Equals",
  },
  {
    value: "startswith",
    label: "Starts With",
  },
  {
    value: "endswith",
    label: "Ends With",
  },
  {
    value: "ne",
    label: "Not Equals",
  },
  {
    value: "contains",
    label: "Contains",
  },
  {
    value: "not__contains",
    label: "Not Contains",
  },
];

const DateFilters = [
  {
    value: "eq",
    label: "Is",
  },
  {
    value: "ne",
    label: "Is Not",
  },
  {
    value: "gt",
    label: "Is After",
  },
  {
    value: "gte",
    label: "Is After or Equal",
  },
  {
    value: "lt",
    label: "Is Before",
  },
  {
    value: "lte",
    label: "Is Before or Equal",
  },
];

const NumericFilters = [
  {
    value: "eq",
    label: "=",
  },
  {
    value: "ne",
    label: "!=",
  },
  {
    value: "gt",
    label: ">",
  },
  {
    value: "gte",
    label: ">=",
  },
  {
    value: "lt",
    label: "<",
  },
  {
    value: "lte",
    label: "<=",
  },
];

const ArrayFilters = [
  {
    value: "in",
    label: "In",
  },
  {
    value: "nin",
    label: "Not In",
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

const FilterOptions = ({
  id,
  columns,
  columnFiltersRef,
  columnFilters,
  updateColumnFilters,
}: {
  id: string;
  columns: ColumnField[];
  columnFiltersRef: RefObject<FilterColumn[]>;
  columnFilters: FilterColumn[];
  updateColumnFilters: (filters: FilterColumn[]) => void;
}) => {
  const [filterColumn, setFilterColumn] = useState<string>(
    columnFiltersRef.current.filter((filter) => filter.id === id)[0]?.column,
  );
  const [filterModifier, setFilterModifier] = useState<string | undefined>(
    columnFiltersRef.current.filter((filter) => filter.id === id)[0]?.modifier,
  );
  const [filterValue, setFilterValue] = useState<
    string | string[] | number | Dayjs | undefined
  >(columnFiltersRef.current.filter((filter) => filter.id === id)[0]?.value);

  const [isDate, setIsDate] = useState(
    columnFiltersRef.current.filter((filter) => filter.id === id)[0]?.isDate ===
      true,
  );
  const [isString, setIsString] = useState(
    columnFiltersRef.current.filter((filter) => filter.id === id)[0]
      ?.isString === true,
  );
  const [isNumeric, setIsNumeric] = useState(
    columnFiltersRef.current.filter((filter) => filter.id === id)[0]
      ?.isNumeric === true,
  );
  const [isArray, setIsArray] = useState(
    columnFiltersRef.current.filter((filter) => filter.id === id)[0]
      ?.isArray === true,
  );

  const [options, setOptions] = useState(
    columnFiltersRef.current.filter((filter) => filter.id === id)[0]?.options,
  );

  useEffect(() => {
    const filter = columnFiltersRef.current.filter(
      (filter) => filter.id === id,
    )[0];
    setFilterColumn(filter?.column);
    setFilterModifier(filter?.modifier);
    setFilterValue(filter?.value);
    setIsDate(filter?.isDate === true);
    setIsString(filter?.isString === true);
    setIsNumeric(filter?.isNumeric === true);
    setIsArray(filter?.isArray === true);
    setOptions(filter?.options);
  }, [columnFilters]);

  const updateColumn = (id: string, column: string) => {
    updateColumnFilters([
      ...columnFilters.map((filter) => {
        if (filter.id === id) {
          const tableColumnIsDate = columns.some(
            (tableColumn) =>
              tableColumn.id === column && tableColumn.isDate === true,
          );
          const tableColumnIsNumeric = columns.some(
            (tableColumn) =>
              tableColumn.id === column && tableColumn.isNumeric === true,
          );
          const tableColumnIsArray = columns.some(
            (tableColumn) =>
              tableColumn.id === column && tableColumn.isArray === true,
          );

          const tableColumnOptions = columns.some(
            (tableColumn) => tableColumn.id === column && tableColumn.options,
          )
            ? columns.filter((tableColumn) => tableColumn.id === column)[0]
                .options
            : [];

          const tableColumnIsString =
            columns.some(
              (tableColumn) =>
                tableColumn.id === column && tableColumn.isString === true,
            ) ||
            (tableColumnIsDate === false &&
              tableColumnIsNumeric === false &&
              tableColumnIsArray === false);

          if (
            filter.isDate !== tableColumnIsDate ||
            filter.isNumeric !== tableColumnIsNumeric ||
            filter.isString !== tableColumnIsString ||
            filter.isArray !== tableColumnIsArray
          ) {
            return {
              ...filter,
              column: column,
              isDate: tableColumnIsDate,
              isNumeric: tableColumnIsNumeric,
              isString: tableColumnIsString,
              isArray: tableColumnIsArray,
              options: tableColumnOptions,
              value: tableColumnIsArray ? [] : undefined,
            } as FilterColumn;
          }
          return {
            ...filter,
            column: column,
            isDate: tableColumnIsDate,
            isNumeric: tableColumnIsNumeric,
            isString: tableColumnIsString,
            isArray: tableColumnIsArray,
            options: tableColumnOptions,
          } as FilterColumn;
        }
        return filter;
      }),
    ]);
  };

  const removeFilter = (id: string) => {
    updateColumnFilters([
      ...columnFilters.filter((filter) => filter.id !== id),
    ]);
  };

  const updateModifier = (id: string, modifier: string) => {
    updateColumnFilters([
      ...columnFilters.map((filter) => {
        if (filter.id === id) {
          return { ...filter, modifier: modifier } as FilterColumn;
        }
        return filter;
      }),
    ]);
  };

  const updateValue = (
    id: string,
    value: string | Dayjs | number | string[] | undefined,
  ) => {
    updateColumnFilters([
      ...columnFilters.map((filter) => {
        if (filter.id === id) {
          return { ...filter, value: value } as FilterColumn;
        }
        return filter;
      }),
    ]);
  };

  return (
    <>
      {id && (
        <div className="flex mb-2 ml-2">
          <div className="flex-1">
            <IconButton onClick={() => removeFilter(id)}>
              <FontAwesomeIcon icon="x" className="mr-2" />
            </IconButton>
          </div>
          <div className="flex-2">
            <TextField
              className="mr-2"
              id={`filter-column-${id}`}
              select
              label="Column"
              value={filterColumn}
              onChange={(event: ChangeEvent<HTMLInputElement>) => {
                updateColumn(id, event.target.value);
              }}
            >
              {columns
                .filter((tableColumns) => tableColumns.filterable === true)
                .map((tableColumns) => (
                  <MenuItem key={tableColumns.label} value={tableColumns.id}>
                    {tableColumns.label}
                  </MenuItem>
                ))}
            </TextField>
          </div>

          <div className="flex-3">
            {(isString || (!isDate && !isNumeric && !isArray)) && (
              <TextField
                className="mr-2"
                id={`filter-modifier-${id}`}
                select
                label="Operator"
                value={filterModifier}
                onChange={(event: ChangeEvent<HTMLInputElement>) => {
                  updateModifier(id, event.target.value);
                }}
              >
                {StringFilters.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </TextField>
            )}

            {isDate && (
              <TextField
                className="mr-2"
                id={`filter-modifier-${id}`}
                select
                label="Operator"
                value={filterModifier}
                onChange={(event: ChangeEvent<HTMLInputElement>) => {
                  updateModifier(id, event.target.value);
                }}
              >
                {DateFilters.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </TextField>
            )}

            {isNumeric && (
              <TextField
                className="mr-2"
                id={`filter-modifier-${id}`}
                select
                label="Operator"
                value={filterModifier}
                onChange={(event: ChangeEvent<HTMLInputElement>) => {
                  updateModifier(id, event.target.value);
                }}
              >
                {NumericFilters.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </TextField>
            )}

            {isArray && (
              <TextField
                className="mr-2"
                id={`filter-modifier-${id}`}
                select
                label="Operator"
                value={filterModifier}
                onChange={(event: ChangeEvent<HTMLInputElement>) => {
                  updateModifier(id, event.target.value);
                }}
              >
                {ArrayFilters.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </TextField>
            )}
          </div>
          <div className="flex-4">
            {(isString || (!isDate && !isNumeric && !isArray)) && (
              <TextField
                className="mr-2"
                id={`filter-value-${id}`}
                label="Value"
                value={filterValue}
                variant="outlined"
                onChange={(event: ChangeEvent<HTMLInputElement>) => {
                  updateValue(id, event.target.value);
                }}
              />
            )}

            {isDate && (
              <LocalizationProvider dateAdapter={AdapterDayjs}>
                <DateTimePicker
                  label="Value"
                  value={filterValue as Dayjs}
                  onChange={(newValue: PickerValue) => {
                    if (newValue && newValue.isValid()) {
                      updateValue(id, newValue);
                    } else {
                      updateValue(id, undefined);
                    }
                  }}
                />
              </LocalizationProvider>
            )}

            {isNumeric && (
              <NumberField
                label="Value"
                value={filterValue as number}
                onValueChange={(value: number | null) => {
                  if (value === null) {
                    updateValue(id, undefined);
                  } else {
                    updateValue(id, value);
                  }
                }}
              />
            )}

            {isArray && (
              <>
                <Select
                  id={`filter-value-${id}`}
                  aria-describedby={`filter-value-helper-text-${id}`}
                  multiple
                  label="Value"
                  value={filterValue as string[]}
                  onChange={(event: SelectChangeEvent<typeof options>) => {
                    const {
                      target: { value },
                    } = event;
                    updateValue(
                      id,
                      typeof value === "string" ? value.split(",") : value,
                    );
                  }}
                >
                  {options &&
                    options.map((option) => (
                      <MenuItem key={option} value={option}>
                        {option}
                      </MenuItem>
                    ))}
                </Select>
                <FormHelperText id={`filter-value-helper-text-${id}`}>
                  Value
                </FormHelperText>
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
};

const FilterSelect = ({
  columns,
  columnFilters,
  columnFiltersRef,
  updateColumnFilters,
  anchor,
  setShowFilter,
}: {
  columns: ColumnField[];
  columnFilters: FilterColumn[];
  columnFiltersRef: RefObject<FilterColumn[]>;
  updateColumnFilters: (filters: FilterColumn[]) => void;
  anchor: HTMLButtonElement | undefined;
  setShowFilter(filter: boolean): void;
}) => {
  // Return Popover

  const addFilter = () => {
    updateColumnFilters([...columnFilters, { id: uuidv4() } as FilterColumn]);
  };

  const clearFilters = () => {
    updateColumnFilters([]);
  };

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
          <FilterOptions
            id={filter.id}
            columns={columns}
            columnFilters={columnFilters}
            columnFiltersRef={columnFiltersRef}
            updateColumnFilters={updateColumnFilters}
          />
        ))}

      <Divider />
      <div className="flex mt-2 mb-2">
        <div className="flex-1 ml-2">
          <Button variant="outlined" onClick={addFilter}>
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

const ColumnHeaderFilter = ({
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
  orderBy: string;
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
        <FilterSelect
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
    columnFilters?: FilterColumn[],
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

  const updateFilters = (newFilters: FilterColumn[]) => {
    columnFiltersRef.current = newFilters;
    setFilters(newFilters);
  };

  const [activeFilter, setActiveFilter] = useState<string | undefined>(
    undefined,
  );

  const getFilterValue = (id: string) => {
    for (const filter of columnFiltersRef.current) {
      if (filter.id === id) {
        return filter.value;
      }
    }

    return undefined;
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
              typeof filter.value === "object" &&
              Array.isArray(filter.value)
            ) {
              return filter.value.some((field) => field === compare);
            }
          } else if (filter.modifier === "nin") {
            if (
              typeof filter.value === "object" &&
              Array.isArray(filter.value)
            ) {
              return !filter.value.some((field) => field === compare);
            }
          }

          // Default response if field is populated
          return false;
        });
      }),
    ];
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
                      columnFiltersRef={columnFiltersRef}
                      updateColumnFilters={updateFilters}
                      order={order}
                      setOrder={setOrder}
                      orderBy={orderBy}
                      setOrderBy={setOrderBy}
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
