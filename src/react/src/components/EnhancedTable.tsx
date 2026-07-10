import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import Box from "@mui/material/Box";
import IconButton from "@mui/material/IconButton";
import Paper from "@mui/material/Paper";
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
import { visuallyHidden } from "@mui/utils";
import { useEffect, useState } from "react";

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

  const [columnFilters, setColumnFilters] = useState<any[] | undefined>(
    undefined,
  );

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

  const handleChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  useEffect(() => {
    if (remoteFilter) {
      // Accept remote updates
      setDisplayData(data);
    } else {
      // Local Filter
      setDisplayData(filterSortData(data));
    }
  }, [data, columnFilters, order, orderBy, page, rowsPerPage]);

  useEffect(() => {
    if (remoteFilter) {
      remoteFilter(columnFilters, orderBy, order, page, rowsPerPage);
    }
  }, [reloadTable]);

  return (
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
                  <FontAwesomeIcon icon="filter" />
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
  );
};

export default EnhancedTable;
