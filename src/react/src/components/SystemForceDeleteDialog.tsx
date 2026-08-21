import {
  Alert,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  Typography,
} from "@mui/material";
import { useState } from "react";

import { SystemForceDeleteDialogProps } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import { ForceDeleteSystem } from "../services/system_service";
import { FAIcon } from "../services/util_service";
import AccessButton from "./AccessButton";

interface AlertDetail {
  severity: "error" | "info" | "success" | "warning";
  detail: string;
}

function SystemForceDeleteDialog({
  system,
  error,
  isVisible,
  onClose,
}: SystemForceDeleteDialogProps) {
  const showSnackbar = useSnackbar();
  const [alerts, setAlerts] = useState<Array<AlertDetail>>([]);

  const dismissAlert = (index: number) => {
    setAlerts((prevAlerts) =>
      prevAlerts.filter((_, idx: number) => index != idx),
    );
  };

  function forceDelete() {
    ForceDeleteSystem(system)
      .then(() => {
        showSnackbar({
          severity: "success",
          summary: "Success",
          detail: `Force deleted: ${system.name}`,
          life: 3000,
        });
      })
      .catch((error) => {
        setAlerts((prevAlerts) => [
          ...prevAlerts,
          { severity: "error", detail: error.toString() },
        ]);
      });
  }

  const localSystemText = `If you would like to Force Delete
      ${system.namespace}/${system.name}-${system.version}, please check with
      your system administrator before running this command. This will follow
      the standard shutdown process for
      ${system.namespace}/${system.name}-${system.version}. If an error
      occurs, ${system.namespace}/${system.name}-${system.version} will still
      be deleted from the database.`;

  const notLocalSystemText = `If you would like to Force Delete
      ${system.namespace}/${system.name}-${system.version}, please check with
      your system administrator before running this command.
      ${system.namespace}/${system.name}-${system.version} is managed by
      another Garden, this request will only be executed locally. This only
      deletes ${system.namespace}/${system.name}-${system.version} from the
      database and will not shutdown
      ${system.namespace}/${system.name}-${system.version} or remove RabbitMQ
      queues.`;

  return (
    <Dialog
      data-testid="system-force-delete-dialog"
      open={isVisible}
      onClose={onClose}
      aria-labelledby="system-force-delete-dialog-title"
    >
      <DialogTitle id="system-force-delete-dialog-title">
        <Grid container>
          <Grid size="grow">{`Force Deleting ${system.name}`}</Grid>
          <Grid>
            <AccessButton
              sx={{ ml: 2 }}
              aria-label="Close system force delete dialog"
              onClick={onClose}
            >
              <FAIcon icon="xmark" />
            </AccessButton>
          </Grid>
        </Grid>
      </DialogTitle>
      <DialogContent dividers>
        {alerts.map((alert: AlertDetail, index: number) => (
          <Alert severity={alert.severity} onClose={() => dismissAlert(index)}>
            {alert.detail}
          </Alert>
        ))}
        <Typography variant="body2" sx={{ mb: 2 }}>
          {system.local ? localSystemText : notLocalSystemText}
        </Typography>
        <Typography variant="body2" sx={{ mb: 2 }}>
          Please review the original error message before proceeding.
        </Typography>
        <Alert severity="error">{error}</Alert>
      </DialogContent>
      <DialogActions>
        <AccessButton onClick={forceDelete} label="Force Delete" color="error">
          Force Delete
        </AccessButton>
        <AccessButton onClick={onClose} label="Close">
          Close
        </AccessButton>
      </DialogActions>
    </Dialog>
  );
}

export default SystemForceDeleteDialog;
