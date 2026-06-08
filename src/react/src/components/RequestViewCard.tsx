import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Badge } from "primereact/badge";
import { Card } from "primereact/card";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import ErrorPage from "../components/ErrorPage";
import RequestViewMain from "../components/RequestViewMain";
import { Request } from "../models/brewtils-types";
import { Config, RequestItem } from "../models/models";
import { GetRequest } from "../services/request_service";
import { DeleteRequest } from "../services/request_service";
import { getErrorCode } from "../services/util_service";
import AccessButton from "./AccessButton";

function RequestViewCard({
  requestItem,
  updateRequestItem,
  removeItem,
  listeners,
  config,
  isDialog,
}: {
  requestItem: RequestItem;
  updateRequestItem: (itemParams?: Partial<RequestItem>) => void;
  removeItem: (id: string) => void;
  listeners: Record<string, any>;
  config: Config;
  isDialog: boolean;
}) {
  const [error, setError] = useState<Error>();
  const requestId = useRef<string | null | undefined>(
    requestItem?.requestId ?? null,
  );
  const [request, setRequest] = useState<Request | null>(
    requestItem?.request ?? null,
  );

  const navigate = useNavigate();

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
    if (["SUCCESS"].includes(status)) {
      return "success";
    }
    return "danger";
  };

  const statusTemplate = (request: Request) => {
    return (
      <Badge value={request.status} severity={SeverityCheck(request?.status)} />
    );
  };

  const CardTitle = () => {
    let title = "Request View";
    if (request?.namespace && request?.system && request?.instance_name) {
      title =
        request.namespace +
        " / " +
        request.system +
        " / " +
        request.instance_name;
    }
    if (request?.command_display_name) {
      title += " / " + request.command_display_name;
    } else if (request?.command) {
      title += " / " + request.command;
    }
    return title;
  };

  const openRequest = () => {
    if (request) {
      void navigate(`/request/${request.id}`);
      if (isDialog) {
        removeItem(requestItem.itemId);
      }
    }
  };

  const deleteRequest = () => {
    if (requestItem.requestId) {
      DeleteRequest({ id: requestItem.requestId } as any)
        .then(() => {
          removeItem(requestItem.itemId);
        })
        .catch((error) => {
          console.error("Error deleting request:", error);
        });
    }
  };

  useEffect(() => {
    const MonitorRequestId = (message: any) => {
      if (message.payload_type === "Request") {
        if (
          requestId.current &&
          message.payload.id &&
          message.payload.id === requestId.current
        ) {
          setRequest(message.payload as Request);
          updateRequestItem({
            ...requestItem,
            ...{ request: message.payload as Request },
          });
        }
      }
    };

    if (!requestId.current) {
      requestId.current = requestItem?.requestId ?? null;

      if (
        request &&
        request.status &&
        ["CREATED", "IN_PROGRESS"].includes(request.status)
      ) {
        // First load, force a refresh of data to ensure latest is rendered in case the completed
        // event has already been received before the listener was registered
        setRequest(null);
      }
    }

    const loadRequest = (loadRequestId: string) => {
      GetRequest(loadRequestId, {})
        .then((data: Request) => {
          setRequest(data);
          updateRequestItem({
            ...requestItem,
            ...{ request: data },
          });

          if (
            requestId.current &&
            !(requestId.current in listeners) &&
            data.status &&
            ["CREATED", "IN_PROGRESS"].includes(data.status)
          ) {
            listeners[requestId.current] = {
              listener: MonitorRequestId,
            };
          }
        })
        .catch((error) => {
          setError(error);
        });
    };

    if (!request && requestId.current) {
      loadRequest(requestId.current);
    }

    if (
      request &&
      requestId.current &&
      !(requestId.current in listeners) &&
      request?.status &&
      ["CREATED", "IN_PROGRESS"].includes(request.status)
    ) {
      listeners[requestId.current] = {
        listener: MonitorRequestId,
      };
    }

    if (
      requestId.current &&
      requestId.current in listeners &&
      request?.status &&
      !["CREATED", "IN_PROGRESS"].includes(request.status)
    ) {
      delete listeners[requestId.current];
    }

    const reloadRequestTimer = setTimeout(() => {
      // Wait 5 seconds and reload if not completed
      // Sometimes the event comes in before the handler is registered
      if (
        requestId.current &&
        request &&
        ((request.status &&
          ["CREATED", "IN_PROGRESS"].includes(request.status)) ||
          request.status === undefined)
      ) {
        loadRequest(requestId.current);
      }
    }, 5000);

    return () => {
      if (requestId.current) {
        delete listeners[requestId.current];
      }
      clearTimeout(reloadRequestTimer);
    };
  }, [request, listeners]);

  return (
    <Card
      title={CardTitle()}
      unstyled={isDialog}
      header={
        !isDialog && (
          <AccessButton
            onClick={() => {
              removeItem(requestItem.itemId);
            }}
            tooltip={`Close Request View for ${request?.command_display_name ?? request?.command ?? "Unknown Request"}`}
          >
            <FontAwesomeIcon icon="xmark" />
          </AccessButton>
        )
      }
    >
      {error ? (
        <ErrorPage
          errorCode={getErrorCode(error?.message)}
          errorMsg={`Request ${requestId.current} was not found`}
          isCard={true}
        />
      ) : (
        request && (
          <div>
            <DataTable value={[request]}>
              <Column field="command" header="Command"></Column>
              <Column header="Status" body={statusTemplate}></Column>
            </DataTable>

            {request && (
              <RequestViewMain
                request={request}
                setRequest={setRequest}
                addRequestItem={updateRequestItem}
                showProjections={false}
                isCard={true}
                config={config}
                openRequest={openRequest}
                deleteRequest={deleteRequest}
              />
            )}
          </div>
        )
      )}
    </Card>
  );
}

export default RequestViewCard;
