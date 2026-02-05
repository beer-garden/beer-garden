import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Badge } from "primereact/badge";
import { Button } from "primereact/button";
import { Column } from "primereact/column";
import { ConfirmPopup, confirmPopup } from "primereact/confirmpopup";
import { DataTable } from "primereact/datatable";
import React, { useCallback, useEffect, useRef, useState } from "react";

import { Request } from "../models/brewtils-types";
import { DeleteRequest, GetRequestList } from "../services/request_service";

function CurrentRequestsTemplate({ listeners }: { listeners: any }) {
  const [currentRequests, setCurrentRequests] = useState<Array<Request>>([]);
  const altRequests = useRef<Array<Request>>([]);

  const setAllRequests = (requests: Array<Request>) => {
    altRequests.current = requests.map((req) => ({
      id: req.id,
      status: req.status,
    }));
    setCurrentRequests(requests);
  };

  const getCurrentRequests = useCallback(() => {
    const sessionUUID = localStorage.getItem("sessionUUID");

    if (sessionUUID) {
      const filterQuery: Record<string, any> = {};
      filterQuery["include"] = ["id", "status", "command"];
      filterQuery["query"] = [
        JSON.stringify({
          field_name: "metadata__sessionUUID",
          modifier: "",
          value: sessionUUID,
        }),
        JSON.stringify({
          field_name: "status",
          modifier: "in",
          value: ["CREATED", "IN_PROGRESS"],
        }),
      ];
      GetRequestList(filterQuery)
        .then((data: [Array<Request>, Headers]) => {
          const [requests] = data;
          setAllRequests(requests);
          if (!("CurrentRequests" in listeners)) {
            listeners["CurrentRequests"] = { listener: ProcessEventRequests };
          }
        })
        .catch((error) => {
          console.error("Error fetching current requests:", error);
        });
    } else {
      setAllRequests([] as Array<Request>);
    }
  }, []);

  const ProcessEventRequests = (message: any) => {
    if (message.payload_type === "Request") {
      const sessionUUID = localStorage.getItem("sessionUUID");

      if (
        sessionUUID &&
        message.payload &&
        message.payload.metadata &&
        message.payload.metadata.sessionUUID &&
        message.payload.metadata.sessionUUID === sessionUUID
      ) {
        let updateList = false;
        const updatedRequests = [] as Array<Request>;

        for (const request of altRequests.current) {
          if (message.payload.id === request.id) {
            updateList = true;
            if (
              message.payload.status &&
              ["CREATED", "IN_PROGRESS"].includes(message.payload.status)
            ) {
              updatedRequests.push(message.payload);
            }
          } else {
            updatedRequests.push(request);
          }
        }

        if (
          !updateList &&
          ["CREATED", "IN_PROGRESS"].includes(message.payload.status)
        ) {
          updatedRequests.push(message.payload);
          updateList = true;
        }

        if (updateList) {
          setAllRequests(updatedRequests);
        }
      }
    }
  };

  useEffect(() => {
    getCurrentRequests();
  }, [getCurrentRequests]);

  const SeverityCheck = (status?: string) => {
    if (!status) {
      return "danger";
    }
    if (["CREATED"].includes(status)) {
      return "info";
    }
    if (["IN_PROGRESS"].includes(status)) {
      return "warning";
    }
    if (["COMPLETED"].includes(status)) {
      return "success";
    }
    return "danger";
  };

  const statusTemplate = (request: Request) => {
    return (
      <Badge value={request.status} severity={SeverityCheck(request?.status)} />
    );
  };

  const optionsTemplate = (request: Request) => {
    return (
      <div>
        <Button
          rounded
          raised
          link
          onClick={() => window.open("/request/" + request.id, "_self")}
        >
          <FontAwesomeIcon icon="arrow-up-right-from-square" />
        </Button>
        <Button
          rounded
          raised
          link
          onClick={() => {
            DeleteRequest(request).catch((error) => {
              console.error("Error deleting request:", error);
            });
          }}
        >
          <FontAwesomeIcon icon="xmark" />
        </Button>
      </div>
    );
  };

  const header = (
    <div className="flex flex-wrap align-items-center justify-content-between gap-2">
      <span className="text-xl text-900 font-bold">Current Requests</span>
    </div>
  );

  const confirm = (event: any) => {
    confirmPopup({
      target: event.currentTarget,
      message: "",
      icon: "pi pi-exclamation-triangle",
      defaultFocus: "accept",
    });
  };

  return (
    <div>
      <ConfirmPopup
        dismissable={true}
        content={({ acceptBtnRef, hide }: { acceptBtnRef: any; hide: any }) => (
          <div className="bg-gray-900 text-white border-round p-3">
            <div className="card">
              <DataTable
                value={currentRequests}
                header={header}
                paginator
                rows={5}
                rowsPerPageOptions={[5, 10, 25, 50]}
              >
                <Column field="command" header="Command"></Column>
                <Column header="Status" body={statusTemplate}></Column>
                <Column header="Options" body={optionsTemplate}></Column>
              </DataTable>
            </div>
            <div className="flex align-items-center gap-2 mt-3">
              <Button
                ref={acceptBtnRef}
                label="Close"
                onClick={() => {
                  hide();
                }}
                className="p-button-sm p-button-outlined"
              ></Button>
            </div>
          </div>
        )}
      />
      <span className="fa-layers fa-fw fa-2x" onClick={confirm}>
        <FontAwesomeIcon
          icon="envelope"
          className={currentRequests.length > 0 ? "fa-shake" : ""}
          style={{ "--fa-animation-duration": "3s" } as React.CSSProperties}
        />
        {currentRequests.length > 0 && (
          <span className="fa-layers-counter" style={{ fontSize: "1.5em" }}>
            {currentRequests.length}
          </span>
        )}
      </span>
    </div>
  );
}

export default CurrentRequestsTemplate;
