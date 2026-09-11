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
  const [reloadRequest, setReloadRequest] = useState(false);

  const [rootRequest, setRootRequest] = useState<Request | undefined>(
    undefined,
  );

  const rootRequestRef = useRef<Request | undefined>(undefined);

  const updateRootRequest = (request?: Request) => {
    rootRequestRef.current = request;
    setRootRequest(request);
  };

  const updateRequest = (request?: Request) => {
    setRequest(request);
    if (request !== undefined) {
      // Force the UI to reload the request for parameters and output fields
      setReloadRequest(true);
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
          reloadRootRequest().catch((error) => {
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
            reloadRootRequest().catch((error) => {
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

  const loadDisplayRequest = async (update_request?: Request) => {
    const request_id = update_request?.id ?? requestId;

    if (request_id === undefined) {
      throw new Error("Unable to determine display request id");
    }

    const queryHeaders: Record<string, any> = {
      children_depth: 0,
      parent_depth: 0,
    };

    const data = await GetRequest(request_id, {}, queryHeaders);

    setRequest(data);

    setReloadRequest(false);
  };

  const reloadRootRequest = async () => {
    if (requestId === undefined && rootRequestRef.current?.id === undefined) {
      throw new Error("Unable to determine root request id");
    }

    let rootRequestId = rootRequestRef.current?.id;

    if (rootRequestId === undefined) {
      if (requestId === undefined) {
        throw new Error("Unable to determine root request id");
      }
      const queryLookupHeaders: Record<string, any> = {
        parent_depth: -1,
        include: ["id", "parent"],
      };
      const loadedRequest = await GetRequest(requestId, {}, queryLookupHeaders);

      if (loadedRequest === undefined) {
        throw new Error("Unable to load root request");
      }
      const findRootParent = (request: Request) => {
        if (request.parent !== undefined && request.parent !== null) {
          return findRootParent(request.parent);
        }
        return request.id;
      };

      rootRequestId = findRootParent(loadedRequest);
    }
    if (rootRequestId) {
      const queryChildrenHeaders: Record<string, any> = {
        children_depth: -1,
        parent_depth: 0,
        include: [
          "id",
          "parent",
          "command_type",
          "command_display_name",
          "command",
          "namespace",
          "system",
          "system_version",
          "instance_name",
          "status",
          "created_at",
          "updated_at",
          "status_updated_at",
          "has_parent",
          "target_garden",
        ],
      };

      const root_request = await GetRequest(
        rootRequestId,
        {},
        queryChildrenHeaders,
      );
      updateRootRequest(root_request);
    }
  };

  useEffect(() => {
    if (urlRequestId.current != requestId && request !== undefined) {
      // New Page Load
      setRequest(undefined);
      updateRootRequest(undefined);
      urlRequestId.current = requestId;
    } else if (!request || request.id === undefined) {
      if (requestId !== undefined) {
        loadDisplayRequest().catch((error) => {
          showSnackbar({
            severity: "error",
            summary: "Error",
            detail: `Error fetching request: ${error}`,
            life: 3000,
          });
          setError(error);
        });
      }
    } else if (reloadRequest) {
      loadDisplayRequest(request).catch((error) => {
        showSnackbar({
          severity: "error",
          summary: "Error",
          detail: `Error fetching request: ${error}`,
          life: 3000,
        });
        setError(error);
      });
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

      if (rootRequestRef.current === undefined) {
        reloadRootRequest().catch((error) => {
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
  }, [request, requestId, reloadRequest, listeners, MonitorRequestId]);

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
                setRequest={updateRequest}
              />
            </Grid>
            <Grid size="grow">
              <Box sx={{ mx: 2 }} key={request?.id}>
                {request && (
                  <RequestViewMain
                    request={request}
                    setRequest={updateRequest}
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
