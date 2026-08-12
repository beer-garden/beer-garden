import {
  Alert,
  Box,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";

import { Request } from "../models/brewtils-types";
import { InstanceDialogProps } from "../models/models";
import { useConfirmDialog } from "../providers/ConfirmDialogProvider";
import { useSnackbar } from "../providers/SnackbarProvider";
import { DeleteRequests, GetRequestList } from "../services/request_service";
import { FAIcon } from "../services/util_service";
import AccessButton from "./AccessButton";
import EnhancedTable from "./EnhancedTable/components/EnhancedTable";

interface AlertDetail {
  severity: "error" | "info" | "success" | "warning";
  detail: string;
}

function InstanceCancelDeleteRequestsDialog({
  instance,
  system,
  isVisible,
  onClose,
}: InstanceDialogProps) {
  const [allCount, setAllCount] = useState<number>(0);
  const [successCount, setSuccessCount] = useState<number>(0);
  const [canceledCount, setCanceledCount] = useState<number>(0);
  const [errorCount, setErrorCount] = useState<number>(0);
  const [createdCount, setCreatedCount] = useState<number>(0);
  const [receivedCount, setReceivedCount] = useState<number>(0);
  const [inProgressCount, setInProgressCount] = useState<number>(0);

  const [alerts, setAlerts] = useState<Array<AlertDetail>>([]);
  const showSnackbar = useSnackbar();
  const showConfirmDialog = useConfirmDialog();

  const [countsDataModels, setCountDataModels] = useState<Array<any>>([
    { label: "SUCCESS", count: successCount },
    { label: "CANCELED", count: canceledCount },
    { label: "ERROR", count: errorCount },
    { label: "IN PROGRESS", count: inProgressCount },
    { label: "RECEIVED", count: receivedCount },
    { label: "CREATED", count: createdCount },
    {
      label: "Non-Completed (CREATED/RECEIVED/IN PROGRESS)",
      count: inProgressCount + receivedCount + createdCount,
    },
    { label: "ALL", count: allCount },
  ]);

  useEffect(() => {
    if (isVisible) {
      loadRequests();
    }
  }, [isVisible]);

  useEffect(() => {
    const updateValues = () => {
      setCountDataModels([
        { label: "SUCCESS", count: successCount },
        { label: "CANCELED", count: canceledCount },
        { label: "ERROR", count: errorCount },
        { label: "IN PROGRESS", count: inProgressCount },
        { label: "RECEIVED", count: receivedCount },
        { label: "CREATED", count: createdCount },
        {
          label: "Non-Completed (CREATED/RECEIVED/IN PROGRESS)",
          count: inProgressCount + receivedCount + createdCount,
        },
        { label: "ALL", count: allCount },
      ]);
    };
    if (
      !countsDataModels.some(
        (value) => value.label === "SUCCESS" && value.count === successCount,
      ) ||
      !countsDataModels.some(
        (value) => value.label === "CANCELED" && value.count === canceledCount,
      ) ||
      !countsDataModels.some(
        (value) => value.label === "ERROR" && value.count === errorCount,
      ) ||
      !countsDataModels.some(
        (value) =>
          value.label === "IN PROGRESS" && value.count === inProgressCount,
      ) ||
      !countsDataModels.some(
        (value) => value.label === "RECEIVED" && value.count === receivedCount,
      ) ||
      !countsDataModels.some(
        (value) => value.label === "CREATED" && value.count === createdCount,
      ) ||
      !countsDataModels.some(
        (value) =>
          value.label === "Non-Completed (CREATED/RECEIVED/IN PROGRESS)" &&
          value.count === inProgressCount + receivedCount + createdCount,
      ) ||
      !countsDataModels.some(
        (value) => value.label === "ALL" && value.count === allCount,
      )
    ) {
      updateValues();
    }
  }, [
    allCount,
    successCount,
    canceledCount,
    errorCount,
    createdCount,
    receivedCount,
    inProgressCount,
  ]);

  function buildFilter(status: string) {
    return {
      include_children: true,
      length: 1,
      columns: [
        {
          data: "namespace__exact",
          name: "",
          searchable: true,
          orderable: true,
          search: {
            value: system.namespace,
            regex: false,
          },
        },
        {
          data: "system__exact",
          name: "",
          searchable: true,
          orderable: true,
          search: {
            value: system.name,
            regex: false,
          },
        },
        {
          data: "system_version__exact",
          name: "",
          searchable: true,
          orderable: true,
          search: {
            value: system.version,
            regex: false,
          },
        },
        {
          data: "instance_name__exact",
          name: "",
          searchable: true,
          orderable: true,
          search: {
            value: instance.name,
            regex: false,
          },
        },
        {
          data: "status",
          name: "",
          searchable: true,
          orderable: true,
          search: {
            value: status == "ALL" ? "" : status,
            regex: false,
          },
        },
      ],
    };
  }

  function loadRequests() {
    setAllCount(0);
    GetRequestList(buildFilter("SUCCESS")).then(
      (data: [Array<Request>, Headers]) => {
        const headers = data[1];
        const count = parseInt(headers.get("recordsFiltered") ?? "0");
        setSuccessCount(count);
        setAllCount((prevCount) => prevCount + count);
      },
      (response) => {
        let msg =
          "Uh oh! It looks like there was a problem counting the SUCCESS Requests.\n";
        if (response.data !== undefined && response.data !== null) {
          msg += response.data;
        }
        setAlerts((prevAlerts) => [
          ...prevAlerts,
          { severity: "error", detail: msg },
        ]);
      },
    );

    GetRequestList(buildFilter("CANCELED")).then(
      (data: [Array<Request>, Headers]) => {
        const headers = data[1];
        const count = parseInt(headers.get("recordsFiltered") ?? "0");
        setCanceledCount(count);
        setAllCount((prevCount) => prevCount + count);
      },
      (response) => {
        let msg =
          "Uh oh! It looks like there was a problem counting the CANCELED Requests.\n";
        if (response.data !== undefined && response.data !== null) {
          msg += response.data;
        }
        setAlerts((prevAlerts) => [
          ...prevAlerts,
          { severity: "error", detail: msg },
        ]);
      },
    );

    GetRequestList(buildFilter("ERROR")).then(
      (data: [Array<Request>, Headers]) => {
        const headers = data[1];
        const count = parseInt(headers.get("recordsFiltered") ?? "0");
        setErrorCount(count);
        setAllCount((prevCount) => prevCount + count);
      },
      (response) => {
        let msg =
          "Uh oh! It looks like there was a problem counting the ERROR Requests.\n";
        if (response.data !== undefined && response.data !== null) {
          msg += response.data;
        }
        setAlerts((prevAlerts) => [
          ...prevAlerts,
          { severity: "error", detail: msg },
        ]);
      },
    );

    GetRequestList(buildFilter("CREATED")).then(
      (data: [Array<Request>, Headers]) => {
        const headers = data[1];
        const count = parseInt(headers.get("recordsFiltered") ?? "0");
        setCreatedCount(count);
        setAllCount((prevCount) => prevCount + count);
      },
      (response) => {
        let msg =
          "Uh oh! It looks like there was a problem counting the CREATED Requests.\n";
        if (response.data !== undefined && response.data !== null) {
          msg += response.data;
        }
        setAlerts((prevAlerts) => [
          ...prevAlerts,
          { severity: "error", detail: msg },
        ]);
      },
    );

    GetRequestList(buildFilter("RECEIVED")).then(
      (data: [Array<Request>, Headers]) => {
        const headers = data[1];
        const count = parseInt(headers.get("recordsFiltered") ?? "0");
        setReceivedCount(count);
        setAllCount((prevCount) => prevCount + count);
      },
      (response) => {
        let msg =
          "Uh oh! It looks like there was a problem counting the RECEIVED Requests.\n";
        if (response.data !== undefined && response.data !== null) {
          msg += response.data;
        }
        setAlerts((prevAlerts) => [
          ...prevAlerts,
          { severity: "error", detail: msg },
        ]);
      },
    );

    GetRequestList(buildFilter("IN_PROGRESS")).then(
      (data: [Array<Request>, Headers]) => {
        const headers = data[1];
        const count = parseInt(headers.get("recordsFiltered") ?? "0");
        setInProgressCount(count);
        setAllCount((prevCount) => prevCount + count);
      },
      (response) => {
        let msg =
          "Uh oh! It looks like there was a problem counting the IN PROGRESS Requests.\n";
        if (response.data !== undefined && response.data !== null) {
          msg += response.data;
        }
        setAlerts((prevAlerts) => [
          ...prevAlerts,
          { severity: "error", detail: msg },
        ]);
      },
    );
  }

  function addSuccessAlert() {
    setAlerts((prevAlerts) => [
      ...prevAlerts,
      { severity: "info", detail: "Success! Requests have been deleted." },
    ]);
  }

  function addDeleteErrorAlert() {
    setAlerts((prevAlerts) => [
      ...prevAlerts,
      {
        severity: "error",
        detail:
          "Uh oh! It looks like there was a problem deleting the Requests.",
      },
    ]);
  }

  function deleteRequests(
    status: string,
    msg: string,
    is_cancel: boolean = false,
  ) {
    const deleteParams: Record<string, any> = {
      namespace: system.namespace,
      system: system.name,
      system_version: system.version,
      instance_name: instance.name,
    };

    if (is_cancel) {
      deleteParams["is_cancel"] = true;
    }

    if (status != "ALL") {
      deleteParams["status"] = status;
    }

    const accept = () => {
      DeleteRequests(deleteParams)
        .then(() => {
          loadRequests();
          addSuccessAlert();
        }, addDeleteErrorAlert)
        .catch((error) => {
          console.error("Error fetching queues:", error);
          showSnackbar({
            severity: "error",
            summary: "Error",
            detail: `Error fetching queues: ${error}`,
            life: 3000,
          });
        });
    };

    const reject = () => {};

    const confirm = () => {
      showConfirmDialog({
        message: msg,
        header: "Confirmation",
        accept,
        reject,
      });
    };

    confirm();
  }

  const actionTemplate = (counter: any) => {
    return (
      <div>
        <AccessButton
          onClick={() => {
            if (counter.label === "IN PROGRESS") {
              deleteRequests(
                counter.label,
                "Are you sure you want to cancel Requests with status IN PROGRESS? There may be a plugin already running the request.",
                true,
              );
            } else if (["RECEIVED", "CREATED"].includes(counter.label)) {
              deleteRequests(
                counter.label,
                `Are you sure you want to delete Requests with status ${counter.label}?`,
                true,
              );
            } else if (
              counter.label === "Non-Completed (CREATED/RECEIVED/IN PROGRESS)"
            ) {
              deleteRequests(
                "ALL",
                "Are you sure you want to cancel all non-completed Requests?",
                true,
              );
            } else {
              deleteRequests(
                counter.label,
                `Are you sure you want to delete Requests with status ${counter.label}?`,
              );
            }
          }}
          tooltip={`Delete ${counter.count} ${counter.label} requests`}
          label={`Delete ${counter.label === "Non-Completed (CREATED/RECEIVED/IN PROGRESS)" ? "Non-Completed" : counter.label}`}
        >{`Delete ${counter.label === "Non-Completed (CREATED/RECEIVED/IN PROGRESS)" ? "Non-Completed" : counter.label}`}</AccessButton>
      </div>
    );
  };

  const dismissAlert = (index: number) => {
    setAlerts((prevAlerts) =>
      prevAlerts.filter((_, idx: number) => index != idx),
    );
  };

  return (
    <Dialog
      data-testid="instance-cancel-delete-requests-dialog"
      open={isVisible}
      onClose={onClose}
      aria-labelledby="instance-cancel-delete-requests-dialog-title"
    >
      <DialogTitle id="instance-cancel-delete-requests-dialog-title">
        <Grid container>
          <Grid size="grow">{`Cancel/Delete Requests: ${system.name}[${system.version}]-${instance.name}`}</Grid>
          <Grid>
            <AccessButton
              sx={{ ml: 2 }}
              aria-label="Close cancel/delete requests dialog"
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
        <EnhancedTable
          data={countsDataModels}
          displayAll={true}
          header={
            <Box sx={{ m: 2 }}>
              <Typography variant="body1" sx={{ fontWeight: "bold" }}>
                {`Currently ${allCount} Requests present in the database`}
              </Typography>
            </Box>
          }
          columns={[
            {
              id: "label",
              field: "label",
              label: "Status",
            },
            {
              id: "count",
              field: "count",
              label: "Count",
            },
            {
              id: "action",
              label: "Action",
              template: actionTemplate,
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

export default InstanceCancelDeleteRequestsDialog;
