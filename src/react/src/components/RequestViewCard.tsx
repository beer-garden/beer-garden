import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Card } from "primereact/card";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import ErrorPage from "../components/ErrorPage";
import RequestViewMain from "../components/RequestViewMain";
import { Request } from "../models/brewtils-types";
import { Config, RequestItem } from "../models/models";
import { GetRequest } from "../services/request_service";
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
  const [request, setRequest] = useState<Request | undefined>(
    requestItem?.request ?? undefined,
  );

  const navigate = useNavigate();

  const openRequest = () => {
    if (request) {
      void navigate(`/request/${request.id}`);
      if (isDialog) {
        removeItem(requestItem.itemId);
      }
    }
  };

  const closeRequest = () => {
    if (requestItem.requestId) {
      removeItem(requestItem.itemId);
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
        setRequest(undefined);
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
            {request && (
              <RequestViewMain
                request={request}
                setRequest={setRequest}
                addRequestItem={updateRequestItem}
                showProjections={false}
                isCard={true}
                config={config}
                openRequest={openRequest}
                closeRequest={closeRequest}
              />
            )}
          </div>
        )
      )}
    </Card>
  );
}

export default RequestViewCard;
