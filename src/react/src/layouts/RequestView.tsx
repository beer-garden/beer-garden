import { Card } from "primereact/card";
import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";

import ErrorPage from "../components/ErrorPage";
import RequestTreeMenu from "../components/RequestTreeMenu";
import RequestViewMain from "../components/RequestViewMain";
import { Request } from "../models/brewtils-types";
import { Config, RequestItem } from "../models/models";
import { useToast } from "../providers/ToastProvider";
import { GetRequest } from "../services/request_service";
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
  const [request, setRequest] = useState<Request | undefined>(undefined);

  const [rootRequest, setRootRequest] = useState<Request | undefined>(
    undefined,
  );

  const rootRequestId = useRef<string | undefined>(undefined);

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
    if (!request || request.id === undefined) {
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
        requestId &&
        request.id !== requestId &&
        rootRequestId.current !== requestId
      ) {
        delete listeners[requestId];
      }

      if (
        request.status &&
        ["CANCELED", "SUCCESS", "ERROR", "INVALID"].includes(request.status)
      ) {
        if (request && request.id in listeners) {
          delete listeners[request.id];
        }
      } else if (
        request &&
        request.id &&
        !Object.hasOwn(listeners, request.id)
      ) {
        listeners[request.id] = {
          listener: MonitorRequestId,
        };
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
          const root_request = await GetRequest(check_request.parent.id, {});
          await loadRootRequest(root_request).catch((error) => {
            throw new error();
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

      if (rootRequest === undefined) {
        loadRootRequest(request).catch((error) => {
          showToast({
            severity: "error",
            summary: "Error",
            detail: `Error fetching parent request: ${error}`,
            life: 3000,
          });
        });
      }
    }

    return () => {
      if (requestId) {
        delete listeners[requestId];
      }
      if (request && request.id) {
        delete listeners[request.id];
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
          <div className="flex">
            <div className="mr-2" style={{ width: "auto" }}>
              {rootRequest && (
                <RequestTreeMenu
                  rootRequest={rootRequest}
                  request={request}
                  setRequest={setRequest}
                />
              )}
            </div>

            <Card
              className="mb-4"
              style={{ width: "100%" }}
              unstyled
              key={request?.id}
            >
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
            </Card>
          </div>
        </div>
      )}
    </>
  );
}

export default RequestView;
