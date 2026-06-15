import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";

import ErrorPage from "../components/ErrorPage";
import RequestTreeChart from "../components/RequestTreeChart";
import RequestViewMain from "../components/RequestViewMain";
import { Request } from "../models/brewtils-types";
import { Config, RequestItem } from "../models/models";
import { useToast } from "../providers/ToastProvider";
import { GetRequest, GetRequestList } from "../services/request_service";
import { getErrorCode } from "../services/util_service";

function RequestView({
  listeners,
  config,
  addRequestItem,
}: {
  listeners: Record<string, any>;
  config: Config;
  addRequestItem: (itemParams?: Partial<RequestItem>) => void;
}) {
  const showToast = useToast();
  const [error, setError] = useState<Error>();
  const { requestId } = useParams<{ requestId: string }>();
  const [request, setRequest] = useState<Request | null>(null);

  const [rootRequest, setRootRequest] = useState<Request | null>(null);

  const rootRequestId = useRef<string | null>(null);

  const MonitorRequestId = useCallback(
    (message: any) => {
      if (message.payload_type === "Request") {
        if (
          requestId &&
          message.payload.id &&
          message.payload.id === requestId
        ) {
          setRequest({
            ...message.payload,
            children: request?.children,
          } as Request);
        }
        if (
          rootRequestId.current &&
          message.payload.id &&
          message.payload.id === rootRequestId.current
        ) {
          setRootRequest({
            ...message.payload,
            children: rootRequest?.children,
          } as Request);
        }
      }
    },
    [requestId],
  );

  useEffect(() => {
    if (!request || request.id !== requestId) {
      if (requestId !== undefined) {
        GetRequest(requestId, {})
          .then((data: Request) => {
            setRequest(data);

            if (
              !(requestId in listeners) &&
              data.status &&
              ["CREATED", "IN_PROGRESS"].includes(data.status)
            ) {
              listeners[requestId] = {
                listener: MonitorRequestId,
              };
            }
          })
          .catch((error) => {
            showToast({
              severity: "error",
              summary: "Error",
              detail: `Error fetching request: ${error}`,
              life: 3000,
            });
            setError(error);
          });
      }
    } else {
      if (
        request.status &&
        ["CANCELED", "SUCCESS", "ERROR", "INVALID"].includes(request.status)
      ) {
        if (requestId && requestId in listeners) {
          delete listeners[requestId];
        }
      }

      const loadChildrenRequests = async (parent_request: Request) => {
        if (parent_request.children) {
          const requestQueries = [];
          const loadedChildren = [];
          for (const childRequest of parent_request.children) {
            if (
              childRequest.id &&
              (childRequest.children === undefined ||
                childRequest.children.length === 0)
            ) {
              requestQueries.push(GetRequest(childRequest.id, {}));
            } else {
              loadedChildren.push(childRequest);
            }
          }

          if (requestQueries.length > 0) {
            parent_request.children = [
              ...loadedChildren,
              ...(await Promise.all(requestQueries)),
            ];
          }
          for (const childRequest of parent_request.children) {
            await loadChildrenRequests(childRequest);
          }
        }
        return parent_request;
      };

      const loadRootRequest = async (check_request: Request) => {
        if (
          check_request.has_parent === true &&
          check_request.parent &&
          check_request.parent.id
        ) {
          GetRequest(check_request.parent.id, {})
            .then((root_request) => {
              loadRootRequest(root_request);
            })
            .catch((error) => {
              showToast({
                severity: "error",
                summary: "Error",
                detail: `Error fetching parent request: ${error}`,
                life: 3000,
              });
            });
        } else {
          setRootRequest(check_request);
          if (check_request.id) {
            rootRequestId.current = check_request.id;
            if (!(check_request.id in listeners)) {
              listeners[check_request.id] = { listener: MonitorRequestId };
            }
          }
          setRootRequest(await loadChildrenRequests(check_request));
        }
      };

      loadRootRequest(request);
    }

    return () => {
      if (requestId) {
        delete listeners[requestId];
      }
      if (rootRequestId.current) {
        delete listeners[rootRequestId.current];
      }
    };
  }, [request, requestId, listeners, MonitorRequestId]);

  return (
    <>
      {error ? (
        <ErrorPage
          errorCode={getErrorCode(error?.message)}
          errorMsg={`Request ${requestId} was not found`}
        />
      ) : (
        <div>
          {request && <h1>Request View: {request.id}</h1>}

          {rootRequest && (
            <RequestTreeChart
              rootRequest={rootRequest}
              currentRequestId={requestId}
            />
          )}

          {request && (
            <RequestViewMain
              request={request}
              setRequest={setRequest}
              addRequestItem={addRequestItem}
              showProjections={true}
              config={config}
              isCard={false}
            />
          )}
        </div>
      )}
    </>
  );
}

export default RequestView;
