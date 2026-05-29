import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { BreadCrumb } from "primereact/breadcrumb";
import { Toast } from "primereact/toast";
import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";

import ErrorPage from "../components/ErrorPage";
import RequestTreeChart from "../components/RequestTreeChart";
import RequestViewMain from "../components/RequestViewMain";
import { Request } from "../models/brewtils-types";
import { Config, RequestItem } from "../models/models";
import { GetRequest } from "../services/request_service";
import { getErrorCode } from "../services/util_service";

function RequestHeader(request: Request) {
  const iconItemTemplate = (item: any, options: any) => {
    if (item.icon) {
      return (
        <span className={options.className}>
          <FontAwesomeIcon icon={item.icon} />
        </span>
      );
    }
    return <span className={options.className}>{item.label}</span>;
  };

  const items = [
    {
      icon: "file-lines",
      template: iconItemTemplate,
    },
    {
      label: request.namespace,
      template: iconItemTemplate,
    },
    {
      label: request.system,
      template: iconItemTemplate,
    },
    {
      label: request.system_version,
      template: iconItemTemplate,
    },
    {
      label: request.instance_name,
      template: iconItemTemplate,
    },
    {
      label: request.command,
      template: iconItemTemplate,
    },
    {
      label: request.id,
      template: iconItemTemplate,
    },
  ];

  // ARC Toolkit Errors:
  //     1) An element other than an <li> list item was found as the first child element of a list.
  // PrimeReact CSS styling is `list-style-type:none` that hides it from check in DOM
  return (
    <h1>
      <BreadCrumb model={items} />
    </h1>
  );
}

function RequestView({
  listeners,
  config,
  addRequestItem,
}: {
  listeners: Record<string, any>;
  config: Config;
  addRequestItem: (itemParams?: Partial<RequestItem>) => void;
}) {
  const toast = useRef<Toast>(null);
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
          setRequest(message.payload as Request);
        }
        if (
          rootRequestId.current &&
          message.payload.id &&
          message.payload.id === rootRequestId.current
        ) {
          setRootRequest(message.payload as Request);
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
            toast.current?.show({
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

      const loadRootRequest = (check_request: Request) => {
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
              toast.current?.show({
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
          <Toast ref={toast} />
          {request && <RequestHeader {...request} />}

          {rootRequest && (
            <RequestTreeChart
              {...{
                rootRequest: rootRequest,
                currentRequestId: requestId,
                config: config,
              }}
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
