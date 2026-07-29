import { Skeleton } from "@mui/material";
import { Card } from "primereact/card";
import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";

import ErrorPage from "../components/ErrorPage";
import RequestTreeMenu from "../components/RequestTreeMenu";
import RequestViewMain from "../components/RequestViewMain";
import { Request } from "../models/brewtils-types";
import { Config, RequestItem } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
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
  const showSnackbar = useSnackbar();
  const [error, setError] = useState<Error>();
  const { requestId } = useParams<{ requestId: string }>();
  const [request, setRequest] = useState<Request | undefined>(undefined);

  const [rootRequest, setRootRequest] = useState<Request | undefined>(
    undefined,
  );

  const rootRequestRef = useRef<Request | undefined>(undefined);

  const updateRootRequest = (request: Request) => {
    rootRequestRef.current = request;
    setRootRequest(request);
  };

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
          } as Request);
        }
        if (
          rootRequestRef.current?.id &&
          message.payload.id &&
          message.payload.id === rootRequestRef.current?.id
        ) {
          updateRootRequest({
            ...message.payload,
            children: rootRequestRef.current?.children,
          } as Request);
        } else if (rootRequestRef.current) {
          updateRootRequest(
            updateNestedRequest(message.payload, rootRequestRef.current),
          );
        }
      }
    },
    [requestId],
  );

  const updateNestedRequest = (
    updatedRequest: Request,
    parentRequest: Request,
  ) => {
    // Only check requests that have parents
    const parent_id = updatedRequest?.parent_id ?? updatedRequest?.parent?.id;

    if (parent_id) {
      if (parent_id === parentRequest.id) {
        if (
          parentRequest?.children &&
          parentRequest.children.some(
            (childRequest: Request) => childRequest.id === updatedRequest.id,
          )
        ) {
          // Replace Request
          parentRequest.children = parentRequest.children.map(
            (childRequest: Request) => {
              if (childRequest.id !== updatedRequest.id) {
                return childRequest;
              }
              return { ...updatedRequest, children: childRequest.children };
            },
          );
          return parentRequest;
        } else {
          // Insert Request
          if (parentRequest?.children) {
            parentRequest.children.push(updatedRequest);
          } else {
            parentRequest.children = [updatedRequest];
          }
          return parentRequest;
        }
      } else if (parentRequest?.children) {
        // Check Children
        parentRequest.children.map((childRequest: Request) => {
          return updateNestedRequest(updatedRequest, childRequest);
        });
      }
    }

    return parentRequest;
  };

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
            showSnackbar({
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
        rootRequestRef.current?.id !== requestId
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
          updateRootRequest(check_request);
          if (check_request.id) {
            if (!(check_request.id in listeners)) {
              listeners[check_request.id] = { listener: MonitorRequestId };
            }
          }
          await loadChildrenRequests(check_request)
            .then((updatedRequest) => {
              updateRootRequest(updatedRequest);
            })
            .catch((error) => {
              showSnackbar({
                severity: "error",
                summary: "Error",
                detail: `Error fetching children requests: ${error}`,
                life: 3000,
              });
            });
        }
      };

      if (rootRequest === undefined) {
        loadRootRequest(request).catch((error) => {
          showSnackbar({
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
      if (rootRequestRef.current?.id) {
        delete listeners[rootRequestRef.current?.id];
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
              {rootRequest === undefined && (
                <Skeleton
                  variant="rectangular"
                  width={210}
                  height={"100%"}
                  sx={{ m: 2 }}
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
