import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import FormHelperText from "@mui/material/FormHelperText";
import IconButton from "@mui/material/IconButton";
import MenuItem from "@mui/material/MenuItem";
import Select, { SelectChangeEvent } from "@mui/material/Select";
import TextField from "@mui/material/TextField";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { DateTimePicker } from "@mui/x-date-pickers/DateTimePicker";
import { PickerValue } from "@mui/x-date-pickers/internals";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { Dayjs } from "dayjs";
import { ChangeEvent, RefObject, useEffect, useState } from "react";

import { ColumnField, FilterColumn } from "../models/EnhancedTableModels";
import NumberField from "./NumberField";

const StringFilters = [
  {
    value: "contains",
    label: "Contains",
  },
  {
    value: "not__contains",
    label: "Not Contains",
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
    value: "eq",
    label: "Equals",
  },
  {
    value: "ne",
    label: "Not Equals",
  },
];

const DateFilters = [
  {
    value: "lt",
    label: "Is Before",
  },
  {
    value: "lte",
    label: "Is Before or Equal",
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
    value: "eq",
    label: "Is",
  },
  {
    value: "ne",
    label: "Is Not",
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

export const EnhancedTableFilterOptions = ({
  id,
  columns,
  columnFiltersRef,
  columnFilters,
  updateColumnFilters,
  triggerReload,
}: {
  id: string;
  columns: ColumnField[];
  columnFiltersRef: RefObject<FilterColumn[]>;
  columnFilters: FilterColumn[];
  updateColumnFilters: (filters: FilterColumn[]) => void;
  triggerReload: () => void;
}) => {
  const [filterColumn, setFilterColumn] = useState<string | undefined>(() => {
    const filters = columnFiltersRef.current.filter(
      (filter) => filter.id === id,
    );

    if (filters.length === 1) {
      return columnFiltersRef.current.filter((filter) => filter.id === id)[0]
        ?.column;
    }
    return undefined;
  });

  const defaultModifier = (filter?: FilterColumn) => {
    if (filter === undefined) {
      const filters = columnFiltersRef.current.filter(
        (filter) => filter.id === id,
      );
      if (filters.length === 1) {
        filter = filters[0];
      }
    }
    if (filter) {
      if (filter.modifier) {
        return filter.modifier;
      }
      if (filter.isDate) {
        return DateFilters[0].value;
      }
      if (filter.isNumeric) {
        return NumericFilters[0].value;
      }
      if (filter.options !== undefined) {
        return ArrayFilters[0].value;
      }
    }

    return StringFilters[0].value;
  };
  const [filterModifier, setFilterModifier] = useState<string | undefined>(
    defaultModifier(),
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
      ?.options !== undefined,
  );

  const [options, setOptions] = useState(
    columnFiltersRef.current.filter((filter) => filter.id === id)[0]?.options,
  );

  useEffect(() => {
    const filter = columnFiltersRef.current.filter(
      (filter) => filter.id === id,
    )[0];
    setFilterColumn(filter?.column);
    setFilterModifier(defaultModifier(filter));
    if (filter?.value !== filterValue) {
      triggerReload();
    }
    setFilterValue(filter?.value);

    const isArray = filter?.options !== undefined;
    setIsDate(!isArray && filter?.isDate === true);
    setIsString(!isArray && filter?.isString === true);
    setIsNumeric(!isArray && filter?.isNumeric === true);
    setIsArray(isArray);
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
              tableColumn.id === column && tableColumn.options !== undefined,
          );

          const tableColumnOptions = columns.some(
            (tableColumn) => tableColumn.id === column && tableColumn.options,
          )
            ? columns.filter((tableColumn) => tableColumn.id === column)[0]
                .options
            : [];

          const tableColumnIsString =
            tableColumnIsArray === false &&
            (columns.some(
              (tableColumn) =>
                tableColumn.id === column && tableColumn.isString === true,
            ) ||
              (tableColumnIsDate === false &&
                tableColumnIsNumeric === false &&
                tableColumnIsArray === false));

          if (
            filter.isDate !== tableColumnIsDate ||
            filter.isNumeric !== tableColumnIsNumeric ||
            filter.isString !== tableColumnIsString ||
            (filter.options !== undefined) !== tableColumnIsArray
          ) {
            // check is modifier is set and in the correct array of options

            // Check if modifier is set and in the correct array of options
            const currentModifier = filter.modifier;
            let validModifier = true;
            let updatedModifier = undefined;
            if (tableColumnIsDate) {
              validModifier = false;
              updatedModifier = DateFilters[0].value;
            } else if (tableColumnIsNumeric) {
              validModifier = false;
              updatedModifier = NumericFilters[0].value;
            } else if (tableColumnIsArray) {
              validModifier = false;
              updatedModifier = ArrayFilters[0].value;
            } else if (tableColumnIsString) {
              validModifier = false;
              updatedModifier = StringFilters[0].value;
            }

            return {
              ...filter,
              column: column,
              isDate: tableColumnIsDate,
              isNumeric: tableColumnIsNumeric,
              isString: tableColumnIsString,
              isArray: tableColumnIsArray,
              options: tableColumnOptions,
              value: tableColumnIsArray ? [] : undefined,
              modifier: validModifier ? currentModifier : updatedModifier,
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
    const runReload = columnFilters.some(
      (filter) =>
        filter.id === id &&
        filter.value !== undefined &&
        (typeof filter.value !== "string" || filter.value !== ""),
    );
    updateColumnFilters([
      ...columnFilters.filter((filter) => filter.id !== id),
    ]);
    if (runReload) {
      triggerReload();
    }
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
            {filterColumn === undefined && (
              <TextField
                className="mr-2"
                id={`filter-modifier-${id}`}
                select
                label="Operator"
                disabled
              ></TextField>
            )}
            {filterColumn &&
              (isString || (!isDate && !isNumeric && !isArray)) && (
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

            {filterColumn && isDate && (
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

            {filterColumn && isNumeric && (
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

            {filterColumn && isArray && (
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
            {(filterColumn === undefined || filterModifier === undefined) && (
              <TextField
                className="mr-2"
                id={`filter-value-${id}`}
                label="Value"
                variant="outlined"
                disabled
              />
            )}

            {filterColumn &&
              filterModifier &&
              (isString || (!isDate && !isNumeric && !isArray)) && (
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

            {filterColumn && filterModifier && isDate && (
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

            {filterColumn && filterModifier && isNumeric && (
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

            {filterColumn && filterModifier && isArray && (
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
