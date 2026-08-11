import {
  Alert,
  Box,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  Stack,
  TextField,
} from "@mui/material";
import { useRef, useState } from "react";

import { Instance } from "../models/brewtils-types";
import { InstanceDialogProps } from "../models/models";
import { GetInstanceLogs } from "../services/instance_service";
import { FAIcon } from "../services/util_service";
import AccessButton from "./AccessButton";

interface AlertDetail {
  severity: "error" | "info" | "success" | "warning";
  detail: string;
}

function InstanceShowLogsDialog({
  instance,
  system,
  isVisible,
  onClose,
}: InstanceDialogProps) {
  const [alerts, setAlerts] = useState<Array<AlertDetail>>([
    {
      severity: "info",
      detail:
        "Plugin must be listening to the Admin Queue and logging to File for logs to be returned. This will only return information from the log file being actively written to.",
    },
  ]);

  const tailLineStart = useRef<number>(20);
  const tailStart = useRef<number>(-20);
  const tailLine = useRef<number>(20);
  const waitTimeout = useRef<number>(30);
  const stopTailing = useRef<boolean>(false);
  const [displayLogs, setDisplayLogs] = useState<string | undefined>(undefined);
  const [loadingLogs, setLoadingLogs] = useState<boolean>(false);
  const downloadHref = useRef<string>(undefined);

  const filename =
    system.name + "[" + system.version + "]-" + instance.name + ".log";

  const updateTailLineStart = (event: any) => {
    if (event.target.value > 0) {
      tailLineStart.current = event.target.value * -1;
    } else {
      tailLineStart.current = event.target.value;
    }
  };

  function successTailLogs(response: [any, any]) {
    const data = response[0];
    const headers = response[1];

    setLoadingLogs(false);

    const requestId = headers.get("request_id");
    downloadHref.current = "api/v1/requests/output/" + requestId;

    let response_logs = null;

    if (typeof data === "string") {
      // Legacy support for log only responses
      response_logs = data;

      if (response_logs !== null && response_logs.length > 0) {
        tailStart.current =
          tailStart.current + (data.match(/\n/g) ?? "").length + 1;
      }
    } else {
      // New log response structure
      response_logs = data.logs;

      if (response_logs !== null && response_logs.length > 0) {
        tailStart.current = data.end_line + 1;
      }
    }

    setDisplayLogs((prevDisplayLogs) => {
      if (prevDisplayLogs !== undefined) {
        return prevDisplayLogs.concat(response_logs);
      } else {
        return "".concat(response_logs);
      }
    });

    // Sleep so you don't spam the server
    if (
      (response_logs !== null && response_logs.length == 0) ||
      response_logs.match(/\n/g).length < tailLine.current
    ) {
      setTimeout(() => {
        getLogsTailLoop();
      }, 10000); // Sleep Ten seconds
    } else {
      setTimeout(() => {
        getLogsTailLoop();
      }, 1000); // Sleep One Second
    }
  }

  function addErrorAlert() {
    setLoadingLogs(false);
    setAlerts((prevAlerts) => [
      ...prevAlerts,
      {
        severity: "error",
        detail:
          "Something went wrong on the backend: Error attempting to retrieve logs - unable to determine log filename. Please verify that the plugin is writing to a log file.",
      },
    ]);
  }

  function getLogsTail(instance: Instance) {
    setLoadingLogs(true);
    setDisplayLogs(undefined);

    if (tailLineStart.current > 0) {
      tailStart.current = tailLineStart.current * -1;
    } else {
      tailStart.current = tailLineStart.current;
    }

    stopTailing.current = false;

    GetInstanceLogs(
      instance,
      waitTimeout.current,
      tailStart.current,
      null,
    ).then(successTailLogs, addErrorAlert);
  }

  function stopLogsTail() {
    stopTailing.current = true;
  }

  function getLogsTailLoop() {
    if (stopTailing.current) {
      return;
    }
    GetInstanceLogs(
      instance,
      waitTimeout.current,
      tailStart.current,
      tailLine.current + tailStart.current,
    ).then((response) => successTailLogs(response), addErrorAlert);
  }

  const dismissAlert = (index: number) => {
    setAlerts((prevAlerts) =>
      prevAlerts.filter((_, idx: number) => index != idx),
    );
  };

  return (
    <Dialog
      data-testid="instance-show-logs-dialog"
      open={isVisible}
      onClose={onClose}
    >
      <DialogTitle>
        <Grid container>
          <Grid size="grow">{`Log File: ${system.name}[${system.version}]-${instance.name}`}</Grid>
          <Grid>
            <AccessButton sx={{ ml: 2 }} onClick={onClose}>
              <FAIcon icon="xmark" />
            </AccessButton>
          </Grid>
        </Grid>
      </DialogTitle>
      <DialogContent>
        {alerts.map((alert: AlertDetail, index: number) => (
          <Alert severity={alert.severity} onClose={() => dismissAlert(index)}>
            {alert.detail}
          </Alert>
        ))}
        <div>
          <Stack direction="row" spacing={1}>
            <AccessButton
              name="start"
              value="Get Tail Logs"
              tooltip="Get Tail logs"
              onClick={() => getLogsTail(instance)}
              label="Get Tail Logs"
            >
              Get Tail Logs
            </AccessButton>
            <AccessButton
              name="stop"
              value="Stop Tail Logs"
              tooltip="Stop Tail Logs"
              onClick={() => stopLogsTail()}
              label="Stop Tail Logs"
            >
              Stop Tail Logs
            </AccessButton>
            <label htmlFor="tail_line_start">Tail Lines</label>
            <TextField
              type="number"
              id="tail_line_start"
              slotProps={{
                htmlInput: { min: 0 },
              }}
              defaultValue={20}
              name="tail_line_start"
              onChange={updateTailLineStart}
            />
          </Stack>
          <div>
            <a
              href={`api/v1/instances/${instance.id}/logs/?logs_only=true`}
              download={filename}
            >
              <AccessButton
                tooltip="Download Full Logs File"
                label="Get Full Logs"
              >
                Get Full Logs
              </AccessButton>
            </a>
          </div>
          {loadingLogs && (
            <Box id="loading" sx={{ textAlign: "center" }}>
              <h1>
                <Box component="span" sx={{ mr: 1 }}>
                  Loading...
                </Box>
                <CircularProgress />
              </h1>
            </Box>
          )}
          {displayLogs !== undefined && (
            <Box>
              <br />
              <Stack spacing={2}>
                <Box
                  component="a"
                  sx={{ display: "flex", justifyContent: "flex-end" }}
                  href={downloadHref.current}
                  download={filename}
                  aria-label="Download Current Logs Displayed"
                >
                  Download
                  <FAIcon icon="download" sx={{ ml: 1 }} />
                </Box>
                <Box component="pre" id="rawOutput">
                  {displayLogs}
                </Box>
              </Stack>
            </Box>
          )}
        </div>
      </DialogContent>
      <DialogActions>
        <AccessButton
          onClick={onClose}
          tooltip="Close Instance Show Logs Dialog"
          label="Close Logs"
        >
          Close Logs
        </AccessButton>
      </DialogActions>
    </Dialog>
  );
}

export default InstanceShowLogsDialog;
