import { Column } from "primereact/column";
import { confirmDialog } from "primereact/confirmdialog";
import { DataTable } from "primereact/datatable";
import { Dialog } from "primereact/dialog";
import { Messages } from "primereact/messages";
import { useEffect, useRef, useState } from "react";

import { Request } from "../models/brewtils-types";
import { InstanceDialogProps } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import { DeleteRequests, GetRequestList } from "../services/request_service";
import AccessButton from "./AccessButton";

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

  const msgs = useRef<Messages>(null);
  const showSnackbar = useSnackbar();

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
        console.log(msg);
        msgs.current?.show({
          severity: "error",
          detail: msg,
          sticky: true,
        });
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
        console.log(msg);
        msgs.current?.show({
          severity: "error",
          detail: msg,
          sticky: true,
        });
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
        console.log(msg);
        msgs.current?.show({
          severity: "error",
          detail: msg,
          sticky: true,
        });
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
        console.log(msg);
        msgs.current?.show({
          severity: "error",
          detail: msg,
          sticky: true,
        });
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
        console.log(msg);
        msgs.current?.show({
          severity: "error",
          detail: msg,
          sticky: true,
        });
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
        console.log(msg);
        msgs.current?.show({
          severity: "error",
          detail: msg,
          sticky: true,
        });
      },
    );
  }

  function addSuccessAlert() {
    msgs.current?.show({
      severity: "info",
      detail: "Success! Requests have been deleted.",
      sticky: true,
    });
  }

  function addDeleteErrorAlert() {
    msgs.current?.show({
      severity: "error",
      detail: "Uh oh! It looks like there was a problem deleting the Requests.",
      sticky: true,
    });
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
      confirmDialog({
        message: msg,
        header: "Confirmation",
        icon: "pi pi-exclamation-triangle",
        defaultFocus: "accept",
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
        />
      </div>
    );
  };

  return (
    <Dialog
      header={`Cancel/Delete Requests: ${system.name}[${system.version}]-${instance.name}`}
      footer={
        <AccessButton label="Close" onClick={onClose}>
          Close
        </AccessButton>
      }
      visible={isVisible}
      style={{ width: "50vw" }}
      onHide={onClose}
    >
      <Messages ref={msgs} />
      <DataTable
        value={countsDataModels}
        header={`Currently ${allCount} Requests present in the database`}
      >
        <Column field="label" header="Status"></Column>
        <Column field="count" header="Count"></Column>
        <Column body={actionTemplate} header="Action"></Column>
      </DataTable>
    </Dialog>
  );
}

export default InstanceCancelDeleteRequestsDialog;
