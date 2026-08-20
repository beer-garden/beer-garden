import { Box, Grid } from "@mui/material";
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
  const urlRequestId = useRef<string | undefined>(undefined);
  const [request, setRequest] = useState<Request | undefined>(undefined);

  const [rootRequest, setRootRequest] = useState<Request | undefined>(
    undefined,
  );

  const rootRequestRef = useRef<Request | undefined>(undefined);

  const updateRootRequest = async (request: Request) => {
    if (request === undefined) {
      rootRequestRef.current = undefined;
      setRootRequest(undefined);
    } else {
      await loadChildrenRequests(request)
        .then((updatedRequest) => {
          rootRequestRef.current = updatedRequest;
          setRootRequest(updatedRequest);
        })
        .catch((error) => {
          showSnackbar({
            severity: "error",
            summary: "Error",
            detail: `Error fetching children requests: ${error}`,
            life: 3000,
          });
        });
      if (
        request.id &&
        request.status &&
        !["CANCELED", "SUCCESS", "ERROR", "INVALID"].includes(request.status)
      ) {
        if (!(request.id in listeners)) {
          listeners[request.id] = { listener: MonitorRequestId };
        }
      }
    }
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
          } as Request).catch((error) => {
            showSnackbar({
              severity: "error",
              summary: "Error",
              detail: `Error Updating Root request: ${error}`,
              life: 3000,
            });
            setError(error);
          });
        } else if (rootRequestRef.current) {
          const matchParentId = (
            checkRequest: Request,
            parentId: string,
          ): boolean => {
            if (checkRequest?.id === parentId) {
              return true;
            }
            if (checkRequest?.children) {
              return checkRequest.children.some((child) => {
                return matchParentId(child, parentId);
              });
            }
            return false;
          };

          if (
            rootRequestRef.current?.id &&
            message.payload?.parent?.id &&
            matchParentId(rootRequestRef.current, message.payload.parent.id)
          ) {
            GetRequest(rootRequestRef.current.id, {})
              .then((updatedRootRequest) => {
                updateRootRequest(updatedRootRequest).catch((error) => {
                  showSnackbar({
                    severity: "error",
                    summary: "Error",
                    detail: `Error Updating Root request: ${error}`,
                    life: 3000,
                  });
                  setError(error);
                });
              })
              .catch((error) => {
                showSnackbar({
                  severity: "error",
                  summary: "Error",
                  detail: `Error Updating Root request: ${error}`,
                  life: 3000,
                });
                setError(error);
              });
          }
        }
      }
    },
    [requestId],
  );

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

  useEffect(() => {
    if (urlRequestId.current != requestId && request !== undefined) {
      // New Page Load
      setRequest(undefined);
      setRootRequest(undefined);
      urlRequestId.current = requestId;
    } else if (!request || request.id === undefined) {
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
          updateRootRequest(check_request).catch((error) => {
            showSnackbar({
              severity: "error",
              summary: "Error",
              detail: `Error Updating Root request: ${error}`,
              life: 3000,
            });
            setError(error);
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
        <Box sx={{ m: 2 }}>
          <Grid container>
            <Grid>
              <RequestTreeMenu
                rootRequest={rootRequest}
                request={request}
                setRequest={setRequest}
              />
            </Grid>
            <Grid size="grow">
              <Box sx={{ mx: 2 }} key={request?.id}>
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
              </Box>
            </Grid>
          </Grid>
        </Box>
      )}
    </>
  );
}

export default RequestView;
