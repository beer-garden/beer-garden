import Alert, { AlertColor } from "@mui/material/Alert";
import Snackbar from "@mui/material/Snackbar";
import React, {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useState,
} from "react";
import { AlertHeading } from "react-bootstrap";

export interface SnackbarArgs {
  severity: AlertColor; // "success" | "info" | "warning" | "error"
  summary: string;
  detail: string;
  life: number;
}

interface SnackbarContextType {
  showSnackbar: (args: SnackbarArgs) => void;
}

// Create the context
const SnackbarContext = createContext<SnackbarContextType | undefined>(
  undefined,
);

// Create the Provider Component
export const SnackbarProvider = ({ children }: { children: ReactNode }) => {
  const [open, setOpen] = useState(false);
  const [summary, setSummary] = useState("");
  const [detail, setDetail] = useState("");
  const [life, setLife] = useState(3000);
  const [severity, setSeverity] = useState<AlertColor>("success");

  const showSnackbar = useCallback((args: SnackbarArgs) => {
    setSummary(args.summary);
    setDetail(args.detail);
    setSeverity(args.severity);
    setLife(args.life);
    setOpen(true);
  }, []);

  const handleClose = (
    _event?: React.SyntheticEvent | Event,
    reason?: string,
  ) => {
    if (reason === "clickaway") return;
    setOpen(false);
  };

  return (
    <SnackbarContext.Provider value={{ showSnackbar }}>
      {children}
      <Snackbar
        open={open}
        autoHideDuration={life}
        onClose={handleClose}
        anchorOrigin={{ vertical: "top", horizontal: "right" }}
      >
        <Alert
          onClose={handleClose}
          severity={severity}
          variant="filled"
          sx={{ width: "100%" }}
        >
          <AlertHeading>{summary}</AlertHeading>
          {detail}
        </Alert>
      </Snackbar>
    </SnackbarContext.Provider>
  );
};

// Create a custom hook for consuming the context
export const useSnackbar = () => {
  const context = useContext(SnackbarContext);
  if (!context) {
    throw new Error("useSnackbar must be used within a SnackbarProvider");
  }
  return context.showSnackbar;
};
