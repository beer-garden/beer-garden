import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Card } from "primereact/card";
import { Divider } from "primereact/divider";
import { Menubar } from "primereact/menubar";
import { TabMenu } from "primereact/tabmenu";
import { TabPanel, TabView } from "primereact/tabview";
import { Tag } from "primereact/tag";
import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";

import AccessButton from "../components/AccessButton";
import ErrorPage from "../components/ErrorPage";
import RequestOptions from "../components/RequestOptions";
import RequestTreeChart from "../components/RequestTreeChart";
import RequestTreeMenu from "../components/RequestTreeMenu";
import RequestViewMain from "../components/RequestViewMain";
import { Request } from "../models/brewtils-types";
import { Config, RequestCommand, RequestItem } from "../models/models";
import { useToast } from "../providers/ToastProvider";
import { GetRequestProjections } from "../services/request_service";
import { GetRequest } from "../services/request_service";
import { getErrorCode } from "../services/util_service";
import { GetSeverity } from "../services/util_service";

function RequestViewSplit({
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

  const [statusSeverity, setStatusSeverity] = useState<string | undefined>(
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

      if (request.status) {
        setStatusSeverity(GetSeverity(request?.status));
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
              <div className="flex ml-2">
                <div className="flex-1">
                  <h1>{request?.command_display_name ?? request?.command}</h1>

                  <p>
                    {request?.namespace ?? "(NAMESPACE}"}-
                    {request?.system ?? "(SYSTEM}"}-
                    {request?.system_version ?? "(VERISON)"}-
                    {request?.instance_name ?? "(INSTANCE_NAME)"}
                    {statusSeverity && (
                      <Tag
                        value={request?.status}
                        severity={statusSeverity}
                        id={`status_${request?.id}`}
                        className="ml-2"
                      />
                    )}
                  </p>
                </div>

                <div className="flex-2 mr-2 mt-4 mb-4">
                  <div className="flex">
                    <div className="flex-1 mr-2">Request ID:</div>
                    <div className="flex-2">{request?.id}</div>
                  </div>
                  <div className="flex">
                    <div className="flex-1 mr-2">Command Type:</div>
                    <div className="flex-2">{request?.command_type}</div>
                  </div>
                  {request?.metadata?._topic && (
                    <div className="flex">
                      <div className="flex-1 mr-2">Topic:</div>
                      <div className="flex-2">{request?.metadata?._topic}</div>
                    </div>
                  )}

                  <div className="flex">
                    <div className="flex-1 mr-2">Created:</div>
                    <div className="flex-2">
                      {request?.created_at
                        ? new Date(request.created_at).toLocaleString()
                        : ""}
                    </div>
                  </div>

                  <div className="flex">
                    <div className="flex-1 mr-2">Status Updated:</div>
                    <div className="flex-2">
                      {request?.status_updated_at
                        ? new Date(request.status_updated_at).toLocaleString()
                        : ""}
                    </div>
                  </div>

                  <div className="flex">
                    <div className="flex-1 mr-2">Last Updated:</div>
                    <div className="flex-2">
                      {request?.updated_at
                        ? new Date(request.updated_at).toLocaleString()
                        : ""}
                    </div>
                  </div>
                </div>
              </div>

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

export default RequestViewSplit;
