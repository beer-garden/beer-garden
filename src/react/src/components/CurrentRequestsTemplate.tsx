import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Badge } from "primereact/badge";
import { Column } from "primereact/column";
import { ConfirmPopup, confirmPopup } from "primereact/confirmpopup";
import { DataTable } from "primereact/datatable";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { Request } from "../models/brewtils-types";
import { Config } from "../models/models";
import { DeleteRequest, GetRequestList } from "../services/request_service";
import { GetCurrentUser } from "../services/user_service";
import { PaginatorTemplate } from "../services/util_service";
import AccessButton from "./AccessButton";

function CurrentRequestsTemplate({
  listeners,
  config,
}: {
  listeners: any;
  config: Config;
}) {
  const [currentRequests, setCurrentRequests] = useState<Array<Request>>([]);
  const altRequests = useRef<Array<Request>>([]);

  const setAllRequests = (requests: Array<Request>) => {
    altRequests.current = requests.map((req) => {
      const request = {
        id: req.id,
        status: req.status,
        updated_at: req.updated_at,
        command: req.command,
      };
      if (config?.auth_enabled === true) {
        return {
          ...request,
          ...{
            target_garden: req.target_garden,
            namespace: req.namespace,
            system: req.system,
            instance_name: req.instance_name,
            system_version: req.system_version,
          },
        };
      }
      return request;
    });
    setCurrentRequests(requests);
  };

  const getCurrentRequests = useCallback(() => {
    const sessionUUID = localStorage.getItem("sessionUUID");
    const username =
      config?.auth_enabled === true ? GetCurrentUser() : undefined;

    if (config?.auth_enabled === true && !username) {
      setAllRequests([] as Array<Request>);
      return;
    }

    if (sessionUUID || username) {
      const filterQuery: Record<string, any> = {};
      if (config?.auth_enabled === true && username) {
        filterQuery["include"] = [
          "id",
          "status",
          "command",
          "updated_at",
          "target_garden",
          "namespace",
          "system",
          "instance_name",
          "system_version",
        ];
        filterQuery["query"] = [
          JSON.stringify({
            field_name: "requester",
            modifier: "",
            value: username,
          }),
        ];
      } else if (sessionUUID) {
        filterQuery["include"] = ["id", "status", "command", "updated_at"];
        filterQuery["query"] = [
          JSON.stringify({
            field_name: "metadata__sessionUUID",
            modifier: "",
            value: sessionUUID,
          }),
        ];
      } else {
        setAllRequests([] as Array<Request>);
        return;
      }

      filterQuery["query"].push(
        JSON.stringify({
          field_name: "status",
          modifier: "in",
          value: ["CREATED", "IN_PROGRESS"],
        }),
      );

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
  }, [config]);

  const requestStickyCheck = (request: Request) => {
    const requestStickyLimit = 30; // Seconds
    return (
      new Date(request.updated_at) >
      new Date(Date.now() - requestStickyLimit * 1000)
    );
  };

  const ProcessEventRequests = (message: any) => {
    if (message.payload_type === "Request") {
      const sessionUUID = localStorage.getItem("sessionUUID");
      const username =
        config?.auth_enabled === true ? GetCurrentUser() : undefined;
      if (
        (message.payload &&
          config?.auth_enabled === true &&
          username &&
          message.payload?.requester === username) ||
        (config?.auth_enabled !== true &&
          sessionUUID &&
          message.payload?.metadata?.sessionUUID === sessionUUID)
      ) {
        let updateList = false;
        const updatedRequests = [] as Array<Request>;

        for (const request of altRequests.current) {
          if (message.payload.id === request.id) {
            updateList = true;
            updatedRequests.push(message.payload);
          } else {
            updatedRequests.push(request);
          }
        }

        if (
          !updateList &&
          (["CREATED", "IN_PROGRESS"].includes(message.payload.status) ||
            requestStickyCheck(message.payload))
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

  useEffect(() => {
    const interval = setInterval(() => {
      let updateList = false;
      const updatedRequests = [] as Array<Request>;
      for (const request of altRequests.current) {
        if (
          !request.status ||
          ["CREATED", "IN_PROGRESS"].includes(request.status) ||
          requestStickyCheck(request)
        ) {
          updatedRequests.push(request);
        } else {
          updateList = true;
        }
        if (updateList) {
          setAllRequests(updatedRequests);
        }
      }
    }, 5000); // check every 5 seconds

    return () => clearInterval(interval);
  }, []);

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
        <Link
          to={`/request/${request.id}`}
          tabIndex={-1}
          aria-label={`Open Request ${request.id}`}
          style={{ textDecoration: "none" }}
        >
          <AccessButton
            rounded
            raised
            link
            tooltip={`Open Request ${request.id}`}
            className="mr-2"
          >
            <FontAwesomeIcon icon="arrow-up-right-from-square" />
          </AccessButton>
        </Link>

        <AccessButton
          rounded
          raised
          link
          onClick={() => {
            DeleteRequest(request)
              .then(() => {
                setAllRequests(
                  altRequests.current.filter(
                    (r: Request) => r.id != request.id,
                  ),
                );
              })
              .catch((error) => {
                console.error("Error deleting request:", error);
              });
          }}
          tooltip={`Delete Request for ${request?.command_display_name ?? request?.command ?? "Unknown Request"}`}
          config={config}
          permission="PLUGIN_ADMIN"
          hasGardenName={request?.target_garden}
          hasNamespace={request?.namespace}
          hasSystemName={request?.system}
          hasInstanceName={request?.instance_name}
          hasSystemVersion={request?.system_version}
          hasCommandName={request?.command}
        >
          <FontAwesomeIcon icon="xmark" />
        </AccessButton>
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
    <div className="flex align-items-center mr-2">
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
                paginatorTemplate={PaginatorTemplate}
              >
                <Column field="command" header="Command"></Column>
                <Column header="Status" body={statusTemplate}></Column>
                <Column header="Options" body={optionsTemplate}></Column>
              </DataTable>
            </div>
            <div className="flex align-items-center gap-2 mt-3">
              <AccessButton
                ref={acceptBtnRef}
                label="Close"
                onClick={() => {
                  hide();
                }}
                className="p-button-sm p-button-outlined"
                tooltip="Close Current Requests, this will capture auto focus for popup. Navigate backwards in tab order to access the list with screen readers."
              />
            </div>
          </div>
        )}
      />
      <AccessButton
        className="fa-layers fa-fw fa-2x"
        onClick={confirm}
        text
        basic
      >
        <FontAwesomeIcon
          icon="envelope"
          className={
            currentRequests.filter(
              (request) =>
                request.status &&
                ["CREATED", "IN_PROGRESS"].includes(request.status),
            ).length > 0
              ? "fa-shake"
              : ""
          }
          style={{ "--fa-animation-duration": "3s" } as React.CSSProperties}
        />
        {currentRequests.filter(
          (request) =>
            request.status &&
            ["CREATED", "IN_PROGRESS"].includes(request.status),
        ).length > 0 && (
          <span className="fa-layers-counter" style={{ fontSize: "1.5em" }}>
            {
              currentRequests.filter(
                (request) =>
                  request.status &&
                  ["CREATED", "IN_PROGRESS"].includes(request.status),
              ).length
            }
          </span>
        )}
      </AccessButton>
    </div>
  );
}

export default CurrentRequestsTemplate;
