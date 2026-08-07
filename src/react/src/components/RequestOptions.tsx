import {
  Box,
  ButtonGroup,
  ClickAwayListener,
  Grow,
  ListItemIcon,
  ListItemText,
  MenuItem,
  MenuList,
  Paper,
  Popper,
  Select,
} from "@mui/material";
import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import AccessButton from "../components/AccessButton";
import { Request } from "../models/brewtils-types";
import {
  Config,
  PermissionCheck,
  RequestCommand,
  RequestItem,
} from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import { checkPermission } from "../services/permission_service";
import { CancelRequest, DeleteRequest } from "../services/request_service";
import { FAIcon, GetBaseURL } from "../services/util_service";
import ConfirmDialog from "./ConfirmDialog";

function RequestOptions({
  request,
  setRequest,
  requestProjections,
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
  requestProjectionSelectedRef: React.RefObject<RequestCommand | undefined>;
  addRequestItem: (itemParams?: Partial<RequestItem>) => void;
  config: Config;
  isCard: boolean;
  openRequest?: () => void;
  closeRequest?: () => void;
}) {
  const navigate = useNavigate();
  const items: any[] = [];
  const showSnackbar = useSnackbar();

  const [requestProjectionSelectedIndex, setRequestProjectionSelectedIndex] =
    useState(0);

  const splitButtonAnchorRef = useRef<HTMLDivElement>(null);
  const [openSplitMenu, setOpenSplitMenu] = useState(false);

  const [showDeletRequest, setShowDeletRequest] = useState(false);

  const handleToggle = () => {
    setOpenSplitMenu((prevOpen) => !prevOpen);
  };
  const handleClose = (event: Event) => {
    if (
      splitButtonAnchorRef.current &&
      splitButtonAnchorRef.current.contains(event.target as HTMLElement)
    ) {
      return;
    }

    setOpenSplitMenu(false);
  };

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
        showSnackbar({
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
        icon: "xmark",
        command: () => {
          CancelRequest(request).catch((error) => {
            console.error("Error canceling request:", error);
            showSnackbar({
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
          icon: "plus",
          command: () => {
            pourAgain(request);
          },
        });
      }
      items.push({
        label: "Download Output",
        icon: "download",
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
          icon: "xmark",
          command: () => setShowDeletRequest(true),
        });
      }
    }
    items.push({
      label: "Reload Request",
      icon: "arrows-rotate",
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
    <Box sx={{ alignItems: "center" }}>
      <ConfirmDialog
        open={showDeletRequest}
        setOpen={() => setShowDeletRequest(false)}
        accept={() => {
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
              showSnackbar({
                severity: "error",
                summary: "Error",
                detail: `Error deleting request: ${error}`,
                life: 3000,
              });
            });
        }}
        reject={() => {}}
        message={"Are you sure you want to delete this request?"}
        header={`Confirm Delete ${request.id}`}
      />
      <Box sx={{ textAlign: "right" }}>
        {execute_authority && (
          <>
            <ButtonGroup
              color="success"
              variant="contained"
              ref={splitButtonAnchorRef}
              aria-label="Button group with a nested menu"
              sx={{ ml: 2, mb: 2 }}
            >
              <AccessButton
                color="success"
                onClick={() => {
                  if (isCard) {
                    if (openRequest) {
                      openRequest();
                    }
                  } else {
                    pourAgain(request);
                  }
                }}
              >
                <Box sx={{ display: "flex" }}>
                  {isCard ? (
                    <FAIcon icon="up-right-from-square" className="mr-2" />
                  ) : (
                    <FAIcon icon="plus" className="mr-2" />
                  )}
                  {isCard ? "Open Request" : "Pour Again"}
                </Box>
              </AccessButton>
              <AccessButton
                aria-controls={openSplitMenu ? "split-button-menu" : undefined}
                aria-expanded={openSplitMenu ? "true" : undefined}
                aria-haspopup="menu"
                onClick={handleToggle}
                sx={{ bgcolor: "success.dark" }}
              >
                <FAIcon icon="caret-down" />
              </AccessButton>
            </ButtonGroup>
            <Popper
              sx={{ zIndex: 1 }}
              open={openSplitMenu}
              anchorEl={splitButtonAnchorRef.current}
              role={undefined}
              transition
              disablePortal
            >
              {({ TransitionProps, placement }) => (
                <Grow
                  {...TransitionProps}
                  style={{
                    transformOrigin:
                      placement === "bottom" ? "center top" : "center bottom",
                  }}
                >
                  <Paper>
                    <ClickAwayListener onClickAway={handleClose}>
                      <MenuList id="split-button-menu" autoFocusItem>
                        {items.map((option) => (
                          <MenuItem key={option.label} onClick={option.command}>
                            <ListItemIcon sx={{ minWidth: "auto", mr: 1 }}>
                              <FAIcon icon={option.icon} />
                            </ListItemIcon>
                            <ListItemText
                              primary={option.label}
                              sx={{ textAlign: "right" }}
                            />
                          </MenuItem>
                        ))}
                      </MenuList>
                    </ClickAwayListener>
                  </Paper>
                </Grow>
              )}
            </Popper>
          </>
        )}
        {!execute_authority && (
          <AccessButton
            label="Download Output"
            onClick={() => handleDownload(request)}
          >
            <Box sx={{ display: "flex" }}>
              <FAIcon icon="download" sx={{ mx: 2 }} />
              Download Output
            </Box>
          </AccessButton>
        )}
      </Box>
      <Box sx={{ textAlign: "right" }}>
        {execute_authority &&
          requestProjections &&
          requestProjections.length > 0 && (
            <Box sx={{ mb: 2, ml: 2 }}>
              <Select value={requestProjectionSelectedIndex} sx={{ mr: 1 }}>
                {requestProjections.map((requestProjection, index) => (
                  <MenuItem
                    value={index}
                    onClick={() => {
                      requestProjectionSelectedRef.current = requestProjection;
                      setRequestProjectionSelectedIndex(index);
                    }}
                  >
                    {commandTemplate(requestProjection)}
                  </MenuItem>
                ))}
              </Select>
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
              >
                Run Next
              </AccessButton>
            </Box>
          )}
      </Box>
    </Box>
  );
}

export default RequestOptions;
