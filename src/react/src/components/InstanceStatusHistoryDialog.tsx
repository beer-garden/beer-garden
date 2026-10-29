import {
  Box,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  Stack,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";

import { Instance } from "../models/brewtils-types";
import { InstanceDialogProps } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import { GetInstance } from "../services/instance_service";
import { GetSeverity } from "../services/util_service";
import { FAIcon } from "../services/util_service";
import AccessButton from "./AccessButton";
import EnhancedTable from "./EnhancedTable/components/EnhancedTable";

function InstanceStatusHistoryDialog({
  instance,
  system,
  isVisible,
  onClose,
}: InstanceDialogProps) {
  const [currentInstance, setCurrentInstance] = useState<Instance>([]);
  const showSnackbar = useSnackbar();

  useEffect(() => {
    if (isVisible) {
      GetInstance(instance.id)
        .then((data: Instance) => {
          setCurrentInstance(data);
        })
        .catch((error) => {
          console.error("Error fetching status history:", error);
          showSnackbar({
            severity: "error",
            summary: "Error",
            detail: `Error fetching status history: ${error}`,
            life: 3000,
          });
        });
    }
  }, [isVisible]);

  return (
    <Dialog
      data-testid="instance-status-history-dialog"
      open={isVisible}
      onClose={onClose}
      aria-labelledby="instance-status-history-dialog-title"
    >
      <DialogTitle id="instance-status-history-dialog-title">
        <Grid container>
          <Grid size="grow">{`Status History: ${system.name}[${system.version}]-${instance.name}`}</Grid>
          <Grid>
            <AccessButton
              sx={{ ml: 2 }}
              aria-label="Close status history dialog"
              onClick={onClose}
            >
              <FAIcon icon="xmark" />
            </AccessButton>
          </Grid>
        </Grid>
      </DialogTitle>
      <DialogContent>
        <Stack direction="row" spacing={1}>
          <Typography component="label">Last Change Event:</Typography>
          <span>
            {new Date(
              currentInstance.status_info?.heartbeat,
            ).toLocaleString() ||
              new Date(instance.status_info?.heartbeat).toLocaleString()}
          </span>
        </Stack>
        <Stack direction="row" spacing={1}>
          <Typography component="label">Current Status:</Typography>
          <Chip
            label={currentInstance.status || instance.status}
            color={GetSeverity(currentInstance.status || instance.status)}
            id={`instance_status_${instance?.id}`}
          />
        </Stack>
        <EnhancedTable
          data={currentInstance.status_info?.history}
          displayAll={true}
          aria-label="Instance Status History Table"
          header={
            <Box sx={{ m: 2 }}>
              <Typography variant="body1" sx={{ fontWeight: "bold" }}>
                Status History
              </Typography>
            </Box>
          }
          columns={[
            {
              id: "status",
              field: "status",
              label: "Status",
            },
            {
              id: "heartbeat",
              field: "heartbeat",
              label: "Timestamp",
              isString: true,
              template: (row) => new Date(row.heartbeat).toLocaleString(),
            },
          ]}
        />
      </DialogContent>
      <DialogActions>
        <AccessButton onClick={onClose} label="Close">
          Close
        </AccessButton>
      </DialogActions>
    </Dialog>
  );
}

export default InstanceStatusHistoryDialog;
