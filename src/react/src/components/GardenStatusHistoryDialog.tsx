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

import { Garden, StatusHistory } from "../models/brewtils-types";
import { GardenDialogProps } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import { GetGarden } from "../services/garden_service";
import { GetSeverity } from "../services/util_service";
import { FAIcon } from "../services/util_service";
import AccessButton from "./AccessButton";
import EnhancedTable from "./EnhancedTable/components/EnhancedTable";

function StatusHistoryDialog({
  gardenName,
  connection_type,
  api_type,
  isVisible,
  onClose,
}: GardenDialogProps) {
  const [currentGarden, setCurrentGarden] = useState<Garden>();
  const [statusHistory, setStatusHistory] = useState<StatusHistory>();
  const showSnackbar = useSnackbar();
  const connection_type_key =
    connection_type == "RECEIVING"
      ? "receiving_connections"
      : "publishing_connections";

  useEffect(() => {
    if (isVisible) {
      GetGarden(gardenName)
        .then((data: Garden) => {
          setCurrentGarden(data);
          setStatusHistory(
            data["publishing_connections"]
              .find((x) => x.api == api_type)
              .status_info.history.sort((a, b) => b.heartbeat - a.heartbeat),
          );
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
      data-testid="status-history-dialog"
      open={isVisible}
      onClose={onClose}
      aria-labelledby="status-history-dialog-title"
    >
      <DialogTitle id="status-history-dialog-title">
        <Grid container>
          <Grid size="grow">{`Status History: ${gardenName} ${connection_type}`}</Grid>
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
            {currentGarden &&
              new Date(
                currentGarden[connection_type_key].find(
                  (x) => x.api == api_type,
                ).status_info.heartbeat,
              ).toLocaleString()}
          </span>
        </Stack>
        <Stack direction="row" spacing={1}>
          <Typography component="label">Current Status:</Typography>
          <Chip
            label={
              currentGarden["receiving_connections"].find(
                (x) => x.api == api_type,
              ).status
            }
            color={GetSeverity(
              currentGarden["receiving_connections"].find(
                (x) => x.api == api_type,
              ).status,
            )}
            id={`instance_status_${gardenName}`}
          />
        </Stack>
        <EnhancedTable
          data={statusHistory}
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

export default StatusHistoryDialog;
