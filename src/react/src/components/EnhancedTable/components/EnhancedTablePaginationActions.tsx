import {
  faAngleLeft,
  faAngleRight,
  faAnglesLeft,
  faAnglesRight,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import Box from "@mui/material/Box";
import IconButton from "@mui/material/IconButton";
import { useTheme } from "@mui/material/styles";

export interface EnhancedTablePaginationActionsProps {
  count: number;
  page: number;
  rowsPerPage: number;
  onPageChange: (
    event: React.MouseEvent<HTMLButtonElement>,
    newPage: number,
  ) => void;
}

export function EnhancedTablePaginationActions(
  props: EnhancedTablePaginationActionsProps,
) {
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
    <Box sx={{ display: "flex", flexWrap: "wrap", m: 2.5 }}>
      <IconButton
        onClick={handleFirstPageButtonClick}
        disabled={page === 0}
        aria-label="first page"
        sx={{ color: "action.selected" }}
      >
        {theme.direction === "rtl" ? (
          <FontAwesomeIcon icon={faAnglesRight} />
        ) : (
          <FontAwesomeIcon icon={faAnglesLeft} />
        )}
      </IconButton>
      <IconButton
        onClick={handleBackButtonClick}
        disabled={page === 0}
        aria-label="previous page"
        sx={{ color: "action.hover" }}
      >
        {theme.direction === "rtl" ? (
          <FontAwesomeIcon icon={faAngleRight} />
        ) : (
          <FontAwesomeIcon icon={faAngleLeft} />
        )}
      </IconButton>
      <IconButton
        onClick={handleNextButtonClick}
        disabled={page >= Math.ceil(count / rowsPerPage) - 1}
        aria-label="next page"
        sx={{ color: "action.hover" }}
      >
        {theme.direction === "rtl" ? (
          <FontAwesomeIcon icon={faAngleLeft} />
        ) : (
          <FontAwesomeIcon icon={faAngleRight} />
        )}
      </IconButton>
      <IconButton
        onClick={handleLastPageButtonClick}
        disabled={page >= Math.ceil(count / rowsPerPage) - 1}
        aria-label="last page"
        sx={{ color: "action.selected" }}
      >
        {theme.direction === "rtl" ? (
          <FontAwesomeIcon icon={faAnglesLeft} />
        ) : (
          <FontAwesomeIcon icon={faAnglesRight} />
        )}
      </IconButton>
    </Box>
  );
}
