import { Dayjs } from "dayjs";

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
  isBoolean?: boolean;

  // Evaluated to determine if is Array
  options?: string[];
}

export interface FilterColumn {
  id: string;
  column: string;
  value: string | string[] | Dayjs | number | undefined;
  modifier?: string;
  isString?: boolean;
  isDate?: boolean;
  isNumeric?: boolean;
  isBoolean?: boolean;

  options?: string[];

  highlighted?: boolean;
}
