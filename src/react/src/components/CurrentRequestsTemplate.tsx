import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Box, Chip, ClickAwayListener, Typography } from "@mui/material";
import Fade from "@mui/material/Fade";
import Popper from "@mui/material/Popper";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { Request } from "../models/brewtils-types";
import { Config } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import { DeleteRequest, GetRequestList } from "../services/request_service";
import { GetCurrentUser } from "../services/user_service";
import AccessButton from "./AccessButton";
import EnhancedTable from "./EnhancedTable/components/EnhancedTable";

function CurrentRequestsTemplate({
  listeners,
  config,
}: {
  listeners: any;
  config: Config;
}) {
  const [currentRequests, setCurrentRequests] = useState<Array<Request>>([]);
  const altRequests = useRef<Array<Request>>([]);
  const showSnackbar = useSnackbar();

  const [currentRequestsOpen, setCurrentRequestsOpen] = React.useState(false);
  const [currentRequestsAnchorEl, setCurrentRequestsAnchorEl] =
    React.useState<null | HTMLElement>(null);

  const handleCurrentRequestsOpen = (event: React.MouseEvent<HTMLElement>) => {
    setCurrentRequestsAnchorEl(event.currentTarget);
    setCurrentRequestsOpen(true);
  };

  const handleCurrentRequestsClickAway = () => {
    setCurrentRequestsOpen(false);
  };

  const canBeOpen = currentRequestsOpen && Boolean(currentRequestsAnchorEl);
  const currentRequestsId = canBeOpen ? "currentRequestPopper" : undefined;

  const setAllRequests = (requests: Array<Request>) => {
    altRequests.current = requests.map((req) => {
      const request = {
        id: req.id,
        status: req.status,
        updated_at: req.updated_at,
        command: req.command,
      };
      if (config?.auth_enabled === true) {
        return {
          ...request,
          ...{
            target_garden: req.target_garden,
            namespace: req.namespace,
            system: req.system,
            instance_name: req.instance_name,
            system_version: req.system_version,
          },
        };
      }
      return request;
    });
    setCurrentRequests(requests);
  };

  const getCurrentRequests = useCallback(() => {
    const sessionUUID = localStorage.getItem("sessionUUID");
    const username =
      config?.auth_enabled === true ? GetCurrentUser() : undefined;

    if (config?.auth_enabled === true && !username) {
      setAllRequests([] as Array<Request>);
      return;
    }

    if (sessionUUID || username) {
      const filterQuery: Record<string, any> = {};
      if (config?.auth_enabled === true && username) {
        filterQuery["include"] = [
          "id",
          "status",
          "command",
          "updated_at",
          "target_garden",
          "namespace",
          "system",
          "instance_name",
          "system_version",
        ];
        filterQuery["query"] = [
          JSON.stringify({
            field_name: "requester",
            modifier: "",
            value: username,
          }),
        ];
      } else if (sessionUUID) {
        filterQuery["include"] = ["id", "status", "command", "updated_at"];
        filterQuery["query"] = [
          JSON.stringify({
            field_name: "metadata__sessionUUID",
            modifier: "",
            value: sessionUUID,
          }),
        ];
      } else {
        setAllRequests([] as Array<Request>);
        return;
      }

      filterQuery["query"].push(
        JSON.stringify({
          field_name: "status",
          modifier: "in",
          value: ["CREATED", "IN_PROGRESS"],
        }),
      );

      GetRequestList(filterQuery)
        .then((data: [Array<Request>, Headers]) => {
          const [requests] = data;
          setAllRequests(requests);
          if (!("CurrentRequests" in listeners)) {
            listeners["CurrentRequests"] = { listener: ProcessEventRequests };
          }
        })
        .catch((error) => {
          console.error("Error fetching current requests:", error);
          showSnackbar({
            severity: "error",
            summary: "Error",
            detail: `Error fetching current requests: ${error}`,
            life: 3000,
          });
        });
    } else {
      setAllRequests([] as Array<Request>);
    }
  }, [config]);

  const requestStickyCheck = (request: Request) => {
    const requestStickyLimit = 30; // Seconds
    return (
      new Date(request.updated_at) >
      new Date(Date.now() - requestStickyLimit * 1000)
    );
  };

  const ProcessEventRequests = (message: any) => {
    if (message.payload_type === "Request") {
      const sessionUUID = localStorage.getItem("sessionUUID");
      const username =
        config?.auth_enabled === true ? GetCurrentUser() : undefined;
      if (
        (message.payload &&
          config?.auth_enabled === true &&
          username &&
          message.payload?.requester === username) ||
        (config?.auth_enabled !== true &&
          sessionUUID &&
          message.payload?.metadata?.sessionUUID === sessionUUID)
      ) {
        let updateList = false;
        const updatedRequests = [] as Array<Request>;

        for (const request of altRequests.current) {
          if (message.payload.id === request.id) {
            updateList = true;
            updatedRequests.push(message.payload);
          } else {
            updatedRequests.push(request);
          }
        }

        if (
          !updateList &&
          (["CREATED", "IN_PROGRESS"].includes(message.payload.status) ||
            requestStickyCheck(message.payload))
        ) {
          updatedRequests.push(message.payload);
          updateList = true;
        }

        if (updateList) {
          setAllRequests(updatedRequests);
        }
      }
    }
  };

  useEffect(() => {
    getCurrentRequests();
  }, [getCurrentRequests]);

  useEffect(() => {
    const interval = setInterval(() => {
      let updateList = false;
      const updatedRequests = [] as Array<Request>;
      for (const request of altRequests.current) {
        if (
          !request.status ||
          ["CREATED", "IN_PROGRESS"].includes(request.status) ||
          requestStickyCheck(request)
        ) {
          updatedRequests.push(request);
        } else {
          updateList = true;
        }
        if (updateList) {
          setAllRequests(updatedRequests);
        }
      }
    }, 5000); // check every 5 seconds

    return () => clearInterval(interval);
  }, []);

  const SeverityCheck = (status?: string) => {
    if (!status) {
      return "error";
    }
    if (["CREATED"].includes(status)) {
      return "info";
    }
    if (["IN_PROGRESS"].includes(status)) {
      return "warning";
    }
    if (["COMPLETED"].includes(status)) {
      return "success";
    }
    return "error";
  };

  const statusTemplate = (request: Request) => {
    return (
      <Chip color={SeverityCheck(request?.status)} label={request.status} />
    );
  };

  const optionsTemplate = (request: Request) => {
    return (
      <div>
        <Link
          to={`/request/${request.id}`}
          tabIndex={-1}
          aria-label={`Open Request ${request.id}`}
          style={{ textDecoration: "none" }}
        >
          <AccessButton
            rounded
            raised
            tooltip={`Open Request ${request.id}`}
            className="mr-2"
          >
            <FontAwesomeIcon icon="arrow-up-right-from-square" />
          </AccessButton>
        </Link>

        <AccessButton
          rounded
          raised
          onClick={() => {
            DeleteRequest(request)
              .then(() => {
                setAllRequests(
                  altRequests.current.filter(
                    (r: Request) => r.id != request.id,
                  ),
                );
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
          tooltip={`Delete Request for ${request?.command_display_name ?? request?.command ?? "Unknown Request"}`}
          config={config}
          permission="PLUGIN_ADMIN"
          hasGardenName={request?.target_garden}
          hasNamespace={request?.namespace}
          hasSystemName={request?.system}
          hasInstanceName={request?.instance_name}
          hasSystemVersion={request?.system_version}
          hasCommandName={request?.command}
        >
          <FontAwesomeIcon icon="xmark" />
        </AccessButton>
      </div>
    );
  };

  const header = (
    <Typography sx={{ fontWeight: "bold", m: 2 }}>Current Requests</Typography>
  );

  const footer = (
    <AccessButton
      label="Close"
      onClick={handleCurrentRequestsClickAway}
      tooltip="Close Current Requests, this will capture auto focus for popup. Navigate backwards in tab order to access the list with screen readers."
      sx={{ m: 2 }}
    >
      Close
    </AccessButton>
  );

  return (
    <>
      <AccessButton
        sx={{ height: "36px", color: "primary.contrastText" }}
        label="Current Requests"
        onClick={handleCurrentRequestsOpen}
        text
        basic
      >
        <FontAwesomeIcon icon="envelope" />
        {currentRequests.filter(
          (request) =>
            request.status &&
            ["CREATED", "IN_PROGRESS"].includes(request.status),
        ).length > 0 && (
          <span className="fa-layers-counter" style={{ fontSize: "3em" }}>
            {
              currentRequests.filter(
                (request) =>
                  request.status &&
                  ["CREATED", "IN_PROGRESS"].includes(request.status),
              ).length
            }
          </span>
        )}
      </AccessButton>
      <Popper
        sx={{ zIndex: 1000 }}
        disablePortal
        id={currentRequestsId}
        open={currentRequestsOpen}
        anchorEl={currentRequestsAnchorEl}
        transition
        placement="bottom-end"
        modifiers={[
          {
            name: "offset",
            options: {
              offset: [0, 15], // [X-offset, Y-offset] in pixels
            },
          },
        ]}
      >
        {({ TransitionProps }) => (
          <ClickAwayListener onClickAway={handleCurrentRequestsClickAway}>
            <Fade {...TransitionProps} timeout={350}>
              <Box
                sx={{
                  boxShadow: 3,
                  bgcolor: "background.paper",
                }}
              >
                <EnhancedTable
                  data={currentRequests}
                  header={header}
                  footer={footer}
                  columns={[
                    {
                      id: "command",
                      label: "Command",
                      field: "command",
                      sortable: true,
                      filterable: true,
                      isString: true,
                    },

                    {
                      id: "status",
                      label: "Status",
                      field: "status",
                      sortable: true,
                      filterable: true,
                      isString: true,
                      template: statusTemplate,
                      options: [
                        "CREATED",
                        "RECEIVED",
                        "IN_PROGRESS",
                        "CANCELED",
                        "SUCCESS",
                        "ERROR",
                        "INVALID",
                      ],
                    },
                    {
                      id: "options",
                      label: "Options",
                      template: optionsTemplate,
                    },
                  ]}
                />
              </Box>
            </Fade>
          </ClickAwayListener>
        )}
      </Popper>
    </>
  );
}

export default CurrentRequestsTemplate;
