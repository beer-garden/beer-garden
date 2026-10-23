import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { confirmDialog } from "primereact/confirmdialog";
import { Dropdown } from "primereact/dropdown";
import { MenuItem } from "primereact/menuitem";
import { SplitButton } from "primereact/splitbutton";
import { useNavigate } from "react-router-dom";

import AccessButton from "../components/AccessButton";
import { Request } from "../models/brewtils-types";
import {
  Config,
  PermissionCheck,
  RequestCommand,
  RequestItem,
} from "../models/models";
import { useToast } from "../providers/ToastProvider";
import { checkPermission } from "../services/permission_service";
import { CancelRequest, DeleteRequest } from "../services/request_service";
import { GetBaseURL } from "../services/util_service";

function RequestOptions({
  request,
  setRequest,
  requestProjections,
  requestProjectionSelected,
  setRequestProjectionSelected,
  requestProjectionSelectedRef,
  addRequestItem,
  config,
  isCard,
  openRequest,
  closeRequest,
}: {
  request: Request;
  setRequest: (request: Request | undefined) => void;
  requestProjections?: RequestCommand[];
  requestProjectionSelected?: RequestCommand;
  setRequestProjectionSelected: (value: RequestCommand | undefined) => void;
  requestProjectionSelectedRef: React.RefObject<RequestCommand | undefined>;
  addRequestItem: (itemParams?: Partial<RequestItem>) => void;
  config: Config;
  isCard: boolean;
  openRequest?: () => void;
  closeRequest?: () => void;
}) {
  const navigate = useNavigate();
  const items: MenuItem[] = [];
  const showToast = useToast();

  const handleDownload = (request: Request) => {
    // Example: fetch a file from a URL
    const fileUrl = `${GetBaseURL()}/api/v1/requests/output/${request.id}`;
    let filename = `${request.id}.txt`;
    if (request.output_type == "HTML") {
      filename = `${request.id}.html`;
    } else if (request.output_type == "JSON") {
      filename = `${request.id}.json`;
    }

    fetch(fileUrl)
      .then((response) => response.blob())
      .then((blob) => {
        // Create blob link to download
        const url = window.URL.createObjectURL(new Blob([blob]));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", filename); // Set the custom download name
        document.body.appendChild(link);
        link.click(); // Trigger the download
        link?.parentNode?.removeChild(link); // Clean up the link
        window.URL.revokeObjectURL(url); // Free up the memory
      })
      .catch((error) => {
        console.error("Error fetching the file:", error);
        showToast({
          severity: "error",
          summary: "Error",
          detail: `Error fetching the file: ${error}`,
          life: 3000,
        });
      });
  };

  const execute_authority = checkPermission(config, "OPERATOR", {
    gardenName: request?.target_garden,
  } as PermissionCheck);

  if (execute_authority) {
    if (
      request.status &&
      ["CREATED", "RECEIVED", "IN_PROGRESS"].includes(request.status)
    ) {
      items.push({
        label: "Cancel Request",
        icon: <FontAwesomeIcon icon="xmark" />,
        command: () => {
          CancelRequest(request).catch((error) => {
            console.error("Error canceling request:", error);
            showToast({
              severity: "error",
              summary: "Error",
              detail: `Error canceling request: ${error}`,
              life: 3000,
            });
          });
        },
      });
    } else {
      if (isCard) {
        items.push({
          label: "Pour Again",
          icon: <FontAwesomeIcon icon="plus" />,
          command: () => {
            pourAgain(request);
          },
        });
      }
      items.push({
        label: "Download Output",
        icon: <FontAwesomeIcon icon="download" />,
        command: () => {
          handleDownload(request);
        },
      });

      if (
        checkPermission(config, "GARDEN_ADMIN", {
          gardenName: request?.target_garden,
        } as PermissionCheck)
      ) {
        items.push({
          label: "Delete Request",
          icon: <FontAwesomeIcon icon="xmark" />,
          command: () => {
            const accept = () => {
              DeleteRequest(request)
                .then(() => {
                  if (closeRequest) {
                    closeRequest();
                  } else {
                    void navigate(`/requests`);
                  }
                })
                .catch((error) => {
                  console.error("Error deleting request:", error);
                  showToast({
                    severity: "error",
                    summary: "Error",
                    detail: `Error deleting request: ${error}`,
                    life: 3000,
                  });
                });
            };
            const reject = () => {};
            const confirm = () => {
              confirmDialog({
                message: "Are you sure you want to delete this request?",
                header: `Confirm Delete ${request.id}`,
                icon: "pi pi-exclamation-triangle",
                defaultFocus: "accept",
                accept,
                reject,
              });
            };
            confirm();
          },
        });
      }
    }
    items.push({
      label: "Reload Request",
      icon: <FontAwesomeIcon icon="arrows-rotate" />,
      command: () => {
        setRequest(undefined);
      },
    });
  }

  const pourAgain = (request: Request) => {
    addRequestItem({ requestId: request.id, type: "REQUEST" });
  };

  const commandTemplate = (requestCommand: RequestCommand) => {
    return (
      <span>
        {requestCommand?.namespace === request.namespace
          ? null
          : `${requestCommand?.namespace} / `}{" "}
        {requestCommand?.systemName} / {requestCommand?.version} /{" "}
        {requestCommand?.instance} / {requestCommand?.command}
      </span>
    );
  };

  return (
    <div className="card justify-content-end">
      <div className="flex flex-end">
        {execute_authority &&
          requestProjections &&
          requestProjections.length > 0 && (
            <div className="card mb-2 mr-2">
              <Dropdown
                value={requestProjectionSelected}
                options={requestProjections}
                valueTemplate={commandTemplate}
                itemTemplate={commandTemplate}
                onChange={(e) => {
                  requestProjectionSelectedRef.current = e.value;
                  setRequestProjectionSelected(e.value);
                }}
                placeholder="Select a command to run next"
                className="mr-1"
              />
              <AccessButton
                label="Run Next"
                basic
                onClick={() => {
                  if (requestProjectionSelectedRef.current) {
                    addRequestItem({
                      type: "REQUEST",
                      requestCommandInput: requestProjectionSelectedRef.current,
                    });
                  }
                }}
              />
            </div>
          )}
        <div>
          {execute_authority && (
            <SplitButton
              label={isCard ? "Open Request" : "Pour Again"}
              icon={
                isCard ? (
                  <FontAwesomeIcon
                    icon="up-right-from-square"
                    className="mr-2"
                  />
                ) : (
                  <FontAwesomeIcon icon="plus" className="mr-2" />
                )
              }
              model={items}
              className="p-button-secondary"
              onClick={() => {
                if (isCard) {
                  if (openRequest) {
                    openRequest();
                  }
                } else {
                  pourAgain(request);
                }
              }}
              severity="success"
              style={{ marginLeft: "auto" }}
              pt={{
                icon: {
                  role: "img",
                  "aria-label": `Split Button Options for Request ${request.id}`,
                },
              }}
            />
          )}
          {!execute_authority && (
            <AccessButton
              icon={<FontAwesomeIcon icon="download" />}
              label="Download Output"
              onClick={() => handleDownload(request)}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default RequestOptions;
