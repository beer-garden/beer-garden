import {
  Box,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";

import { ColumnField } from "../components/EnhancedTable//models/EnhancedTableModels";
import EnhancedTable from "../components/EnhancedTable/components/EnhancedTable";
import { Request } from "../models/brewtils-types";
import { FAIcon, GetSeverity } from "../services/util_service";
import AccessButton from "./AccessButton";

interface TimelineRecord {
  garden: string;
  created_at?: number;
  received_at?: number;
  in_progress_at?: number;
  canceled_at?: number;
  success_at?: number;
  error_at?: number;
  invalid_at?: number;
}

function RequestTimeline({ request }: { request: Request }) {
  const [timeline, setTimeline] = useState<TimelineRecord[]>([]);
  const [displayColumns, setDisplayColumns] = useState<ColumnField[]>([]);

  const [showTimeline, setShowTimeline] = useState(false);

  const parseRequest = (parseRequest: Request) => {
    let newTimeline = [] as TimelineRecord[];

    if (parseRequest.metadata !== undefined) {
      for (const key of Object.keys(parseRequest.metadata)) {
        for (const [status, target] of [
          ["CREATED", "created_at"],
          ["RECEIVED", "received_at"],
          ["IN_PROGRESS", "in_progress_at"],
          ["CANCELED", "canceled_at"],
          ["SUCCESS", "success_at"],
          ["ERROR", "error_at"],
          ["INVALID", "invalid_at"],
        ]) {
          if (key.startsWith(`${status}_`)) {
            const garden = key.replace(`${status}_`, "");
            if (newTimeline.some((value) => value.garden === garden)) {
              newTimeline = newTimeline.map((value) => {
                if (
                  value.garden === garden &&
                  parseRequest.metadata !== undefined &&
                  parseRequest.metadata[key] !== undefined
                ) {
                  if (typeof parseRequest.metadata[key] === "number") {
                    return { ...value, [target]: parseRequest.metadata[key] };
                  }
                }
                return value;
              });
            } else {
              newTimeline.push({
                garden: garden,
                [target]: parseRequest.metadata[key],
              });
            }
          }
        }
      }
    }
    parseColumns(newTimeline);
    setTimeline(newTimeline);
  };

  const parseColumns = (newTimeline: TimelineRecord[]) => {
    const columns = [
      {
        id: "garden",
        field: "garden",
        label: "Garden",
        isString: true,
        sortable: true,
        filterable: false,
      },
    ] as ColumnField[];

    if (newTimeline.some((value) => value.created_at !== undefined)) {
      columns.push({
        id: "created_at",
        field: "created_at",
        label: "Created At",
        isDate: true,
        sortable: true,
        filterable: false,
      });
    }

    if (newTimeline.some((value) => value.received_at !== undefined)) {
      columns.push({
        id: "received_at",
        field: "received_at",
        label: "Received At",
        isDate: true,
        sortable: true,
        filterable: false,
      });
    }

    if (newTimeline.some((value) => value.in_progress_at !== undefined)) {
      columns.push({
        id: "in_progress_at",
        field: "in_progress_at",
        label: "In Progress At",
        isDate: true,
        sortable: true,
        filterable: false,
      });
    }

    if (newTimeline.some((value) => value.success_at !== undefined)) {
      columns.push({
        id: "success_at",
        field: "success_at",
        label: "Success At",
        isDate: true,
        sortable: true,
        filterable: false,
      });
    }

    if (newTimeline.some((value) => value.canceled_at !== undefined)) {
      columns.push({
        id: "canceled_at",
        field: "canceled_at",
        label: "Canceled At",
        isDate: true,
        sortable: true,
        filterable: false,
      });
    }
    if (newTimeline.some((value) => value.error_at !== undefined)) {
      columns.push({
        id: "error_at",
        field: "error_at",
        label: "Error At",
        isDate: true,
        sortable: true,
        filterable: false,
      });
    }
    if (newTimeline.some((value) => value.invalid_at !== undefined)) {
      columns.push({
        id: "invalid_at",
        field: "invalid_at",
        label: "Invalid At",
        isDate: true,
        sortable: true,
        filterable: false,
      });
    }

    setDisplayColumns(columns);
  };

  useEffect(() => {
    // Set timeline records
    if (request) {
      parseRequest(request);
    }
  }, [request]);

  const formatDate = (value: string) => {
    const date = new Date(value);
    return date.toLocaleDateString() + " " + date.toLocaleTimeString();
  };

  return (
    <>
      <AccessButton
        onClick={() => setShowTimeline(true)}
        aria-label={`Show Request Status Timeline for ${request.id}`}
        icon
      >
        <FAIcon icon="clock-rotate-left" />
      </AccessButton>
      <Dialog
        open={showTimeline}
        scroll="paper"
        onClose={() => {
          setShowTimeline(false);
        }}
        sx={{
          "& .MuiPaper-root": {
            minWidth: "50%",
          },
        }}
      >
        <DialogTitle>
          <Grid container>
            <Grid size="grow">Request Status Timeline: {request.id}</Grid>
            <Grid>
              <AccessButton
                sx={{ mr: 2 }}
                aria-label="Close request timeline dialog"
                onClick={() => {
                  setShowTimeline(false);
                }}
              >
                <FAIcon icon="xmark" />
              </AccessButton>
            </Grid>
          </Grid>
        </DialogTitle>
        <DialogContent>
          <Box>
            <Typography sx={{ mb: 2 }}>
              Last Request Event Seen: {formatDate(request.updated_at)}
            </Typography>
            <Typography sx={{ mb: 2 }}>
              Current Status:
              <Chip
                label={request?.status}
                color={GetSeverity(request?.status)}
                id={`request_timeline_status_${request?.id}`}
                sx={{ ml: 1 }}
              />
            </Typography>

            <EnhancedTable
              data={timeline}
              columns={displayColumns}
              displayAll={true}
              defaultOrder="asc"
              defaultOrderBy="created_at"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <AccessButton
            onClick={() => {
              setShowTimeline(false);
            }}
            tooltip="Close Request Timeline Dialog"
            label="Close Timeline"
          >
            Close
          </AccessButton>
        </DialogActions>
      </Dialog>
    </>
  );
}
export default RequestTimeline;
