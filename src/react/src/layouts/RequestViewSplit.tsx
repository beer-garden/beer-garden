import { Card } from "primereact/card";
import { Tag } from "primereact/tag";
import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";

import ErrorPage from "../components/ErrorPage";
import RequestOptions from "../components/RequestOptions";
import RequestTreeChart from "../components/RequestTreeChart";
import RequestTreeMenu from "../components/RequestTreeMenu";
import RequestViewMain from "../components/RequestViewMain";
import { Request } from "../models/brewtils-types";
import { Config, RequestCommand,RequestItem } from "../models/models";
import { useToast } from "../providers/ToastProvider";
import { GetRequestProjections } from "../services/request_service";
import { GetRequest } from "../services/request_service";
import { getErrorCode } from "../services/util_service";
import { GetSeverity } from "../services/util_service";
import { Menubar } from "primereact/menubar";
import { TabMenu } from "primereact/tabmenu";
import { Divider } from "primereact/divider";
import AccessButton from "../components/AccessButton";

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

  const [requestProjections, setRequestProjections] = useState<
    RequestCommand[] | undefined
  >(undefined);
  const [requestProjectionSelected, setRequestProjectionSelected] = useState<
    RequestCommand | undefined
  >(undefined);
  const requestProjectionSelectedRef = useRef<RequestCommand | undefined>(
    undefined,
  );

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

      if (request !== undefined) {
        GetRequestProjections(request)
          .then((projections) => {
            setRequestProjections(projections);
            setRequestProjectionSelected(projections[0]);
            requestProjectionSelectedRef.current = projections[0];
          })
          .catch((error) => {
            console.error("Error fetching request projections:", error);
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

  const requestMenuRenderer = (item: any) => {
    return (<a className="flex align-items-center p-menuitem-link">
      <span> {item.label}</span>
    </a>)
  }

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
            <div className="mr-2">
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

                <div className="flex-2 mr-2 mt-4">
                  <div className="flex">
                    <div className="flex-1">Request ID:</div>
                    <div className="flex-2">{request?.id}</div>
                  </div>

                  <div className="flex">
                    <div className="flex-1">Created:</div>
                    <div className="flex-2">
                      {request?.created_at
                        ? new Date(request.created_at).toLocaleString()
                        : ""}
                    </div>
                  </div>

                  <div className="flex">
                    <div className="flex-1">Status Updated:</div>
                    <div className="flex-2">
                      {request?.status_updated_at
                        ? new Date(request.status_updated_at).toLocaleString()
                        : ""}
                    </div>
                  </div>

                  <div className="flex">
                    <div className="flex-1">Last Updated:</div>
                    <div className="flex-2">
                      {request?.updated_at
                        ? new Date(request.updated_at).toLocaleString()
                        : ""}
                    </div>
                  </div>

                </div>
              </div>

              <div className="flex">

                <div className="flex-1">
                  <AccessButton
                  className="mt-2 mr-2"
                    label="Request Parameters"
                    />
                    <AccessButton
                    className="mt-2 mr-2"
                    label="Request Output"
                    disabled
                    />

                </div>
                <div className="flex-2">
                  {request && (<RequestOptions
                    request={request}
                    setRequest={setRequest}
                    config={config}
                    addRequestItem={addRequestItem}
                    requestProjections={requestProjections}
                    requestProjectionSelected={requestProjectionSelected}
                    setRequestProjectionSelected={setRequestProjectionSelected}
                    requestProjectionSelectedRef={requestProjectionSelectedRef}
                    isCard={false}
                    openRequest={() => {}}
                    closeRequest={() => {}}
                  />)}
                </div>
              </div>


              {/* <div>
                <Menubar model={[
                  {
                    label: "Request Parameters",
                    template: requestMenuRenderer
                  },
                  {
                    label: "Request Ouput",
                    template: requestMenuRenderer
                  }
                ]} 
                pt={{
                  root:{
                    style:{color:"transparent",
                    backgroundColor:"transparent",
                    border: "transparent"
                  }
                  },
                  content:{
                    style:{
                      textDecorator:"underline"
                    }
                  }
                }}
                end={request && (<RequestOptions
                    request={request}
                    setRequest={setRequest}
                    config={config}
                    addRequestItem={addRequestItem}
                    requestProjections={requestProjections}
                    requestProjectionSelected={requestProjectionSelected}
                    setRequestProjectionSelected={setRequestProjectionSelected}
                    requestProjectionSelectedRef={requestProjectionSelectedRef}
                    isCard={false}
                    openRequest={() => {}}
                    closeRequest={() => {}}
                  />)}/>
              </div> */}
              <Divider/>

              <p>Hello World!</p>
              {/* <div>
                <TabMenu model={[
                  {
                    label: "Request Parameters"
                  },
                  {
                    label: "Request Ouput",
                  }
                ]} 
                />
              </div> */}

              {/* <div>
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
              </div> */}
            </Card>
          </div>
        </div>
      )}
    </>
  );
}

export default RequestViewSplit;
