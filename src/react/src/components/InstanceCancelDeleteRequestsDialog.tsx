import { Button } from "primereact/button";
import { confirmDialog } from "primereact/confirmdialog";
import { Dialog } from "primereact/dialog";
import { Messages } from "primereact/messages";
import { useEffect, useRef, useState } from "react";

import { Request } from "../models/brewtils-types";
import { InstanceDialogProps } from "../models/models";
import { DeleteRequests, GetRequestList } from "../services/request_service";

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

  useEffect(() => {
    loadRequests();
  }, [isVisible]);

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

  return (
    <Dialog
      header={`Cancel/Delete Requests: ${system.name}[${system.version}]-${instance.name}`}
      footer={<Button onClick={onClose}>Close</Button>}
      visible={isVisible}
      style={{ width: "50vw" }}
      onHide={onClose}
    >
      <Messages ref={msgs} />
      <div>Currently {allCount} Requests present in the database</div>
      <br />
      <table
        id="requestDeleteCancelTable"
        className="table table-striped table-bordered w-100"
      >
        <tbody>
          <tr>
            <th>Status</th>
            <th>Count</th>
            <th>Action</th>
          </tr>
          <tr>
            <td>SUCCESS</td>
            <td>{successCount}</td>
            <td>
              <Button
                onClick={() =>
                  deleteRequests(
                    "SUCCESS",
                    "Are you sure you want to delete Requests with status SUCCESS?",
                  )
                }
              >
                Delete SUCCESS
              </Button>
            </td>
          </tr>
          <tr>
            <td>CANCELED</td>
            <td>{canceledCount}</td>
            <td>
              <Button
                onClick={() =>
                  deleteRequests(
                    "CANCELED",
                    "Are you sure you want to delete Requests with status CANCELED?",
                  )
                }
              >
                Delete CANCELED
              </Button>
            </td>
          </tr>
          <tr>
            <td>ERROR</td>
            <td>{errorCount}</td>
            <td>
              <Button
                onClick={() =>
                  deleteRequests(
                    "ERROR",
                    "Are you sure you want to delete Requests with status ERROR?",
                  )
                }
              >
                Delete ERROR
              </Button>
            </td>
          </tr>
          <tr>
            <td>IN PROGRESS</td>
            <td>{inProgressCount}</td>
            <td>
              <Button
                onClick={() =>
                  deleteRequests(
                    "IN PROGRESS",
                    "Are you sure you want to cancel Requests with status IN PROGRESS? There may be a plugin already running the request.",
                    true,
                  )
                }
              >
                Cancel IN PROGRESS
              </Button>
            </td>
          </tr>
          <tr>
            <td>RECEIVED</td>
            <td>{receivedCount}</td>
            <td>
              <Button
                onClick={() =>
                  deleteRequests(
                    "RECEIVED",
                    "Are you sure you want to cancel Requests with status RECEIVED?",
                    true,
                  )
                }
              >
                Cancel RECEIVED
              </Button>
            </td>
          </tr>
          <tr>
            <td>CREATED</td>
            <td>{createdCount}</td>
            <td>
              <Button
                onClick={() =>
                  deleteRequests(
                    "CREATED",
                    "Are you sure you want to cancel Requests with status CREATED? Recommend clearing topics as well.",
                    true,
                  )
                }
              >
                Cancel CREATED
              </Button>
            </td>
          </tr>
          <tr>
            <td>Non-Completed (CREATED/RECEIVED/IN PROGRESS)</td>
            <td>{inProgressCount + receivedCount + createdCount}</td>
            <td>
              <Button
                onClick={() =>
                  deleteRequests(
                    "ALL",
                    "Are you sure you want to cancel all non-completed Requests?",
                    true,
                  )
                }
              >
                Cancel Non-Completed
              </Button>
            </td>
          </tr>
          <tr>
            <td>ALL</td>
            <td>{allCount}</td>
            <td>
              <Button
                onClick={() =>
                  deleteRequests(
                    "ALL",
                    "Are you sure you want to delete all the Requests?",
                  )
                }
              >
                Delete All
              </Button>
            </td>
          </tr>
        </tbody>
      </table>
    </Dialog>
  );
}

export default InstanceCancelDeleteRequestsDialog;
