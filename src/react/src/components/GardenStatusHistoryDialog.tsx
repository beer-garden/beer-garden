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

import { Connection, Garden, StatusHistory } from "../models/brewtils-types";
import { GardenDialogProps } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import { GetGarden } from "../services/garden_service";
import { GetSeverity } from "../services/util_service";
import { FAIcon } from "../services/util_service";
import AccessButton from "./AccessButton";
import EnhancedTable from "./EnhancedTable/components/EnhancedTable";

function GardenStatusHistoryDialog({
  gardenName,
  connection_type,
  api_type,
  isVisible,
  onClose,
}: GardenDialogProps) {
  const [currentGarden, setCurrentGarden] = useState<Garden>();
  const [statusHistory, setStatusHistory] = useState<StatusHistory[]>();
  const showSnackbar = useSnackbar();
  const connection_type_key =
    connection_type == "RECEIVING"
      ? "receiving_connections"
      : "publishing_connections";

  useEffect(() => {
    if (isVisible) {
      GetGarden(gardenName, true)
        .then((data: Garden) => {
          setCurrentGarden(data);
          setStatusHistory(
            data[connection_type_key]
              .find((x: Connection) => x.api == api_type)
              .status_info?.history.sort(
                (a: StatusHistory, b: StatusHistory) =>
                  b.heartbeat - a.heartbeat,
              ),
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

  const statusTemplate = (statusHistory: StatusHistory) => {
    return (
      <Chip
        color={GetSeverity(statusHistory?.status)}
        label={statusHistory.status}
      />
    );
  };

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
        <Box sx={{ mb: 1 }}>
          <Stack direction="row" spacing={1}>
            <Typography component="label">Last Change Event:</Typography>
            <span>
              {currentGarden &&
                new Date(
                  currentGarden[connection_type_key].find(
                    (x: Connection) => x.api == api_type,
                  ).status_info.heartbeat,
                ).toLocaleString()}
            </span>
          </Stack>
          <Stack direction="row" spacing={1}>
            <Typography component="label">Current Status:</Typography>
            <Chip
              label={
                currentGarden &&
                currentGarden[connection_type_key].find(
                  (x: Connection) => x.api == api_type,
                ).status
              }
              color={GetSeverity(
                currentGarden &&
                  currentGarden[connection_type_key].find(
                    (x: Connection) => x.api == api_type,
                  ).status,
              )}
              id={`instance_status_${gardenName}`}
            />
          </Stack>
        </Box>
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
              template: statusTemplate,
            },
            {
              id: "heartbeat",
              field: "heartbeat",
              label: "Timestamp",
              isString: true,
              template: (row) => (
                <span>{new Date(row.heartbeat).toLocaleString()}</span>
              ),
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

export default GardenStatusHistoryDialog;
