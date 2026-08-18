import { Box, Chip, Typography } from "@mui/material";
import Stack from "@mui/material/Stack";
import Tooltip from "@mui/material/Tooltip";
import { useEffect, useState } from "react";

import { Request } from "../models/brewtils-types";
import { FAIcon, GetSeverity } from "../services/util_service";
import TreeMenu, { ExtendedTreeItemProps } from "./TreeMenu";

function timeDelta(createdDate: Date, statusUpdated: Date) {
  if (!createdDate || !statusUpdated) {
    return "";
  }

  if (statusUpdated === createdDate) {
    return "<1s";
  }

  if (statusUpdated < createdDate) {
    return "<1s";
  }

  const diffInMs = statusUpdated.getTime() - createdDate.getTime();

  const msHour = 60 * 60 * 1000;
  const msMinutes = 60 * 1000;
  const diffHours = Math.floor(diffInMs / msHour);
  const diffMinutes = Math.floor((diffInMs - diffHours * msHour) / msMinutes);
  const diffSeconds = Math.floor(
    (diffInMs - diffHours * msHour - diffMinutes * msMinutes) / 1000,
  );

  if (diffHours > 0) {
    return `${diffHours}h:${diffMinutes}m:${diffSeconds}s`;
  }
  if (diffMinutes > 0) {
    return `${diffMinutes}m:${diffSeconds}s`;
  }
  if (diffSeconds > 0) {
    return `${diffSeconds}s`;
  }
  return "<1s";
}

function parseRequest(request: Request): ExtendedTreeItemProps {
  const item = {
    id: request.id,
    label: request.command,
    data: {
      id: request.id,
      command: request.command,
      command_display_name: request.command_display_name,
      command_type: request.command_type,
      topic: request?.metadata?._topic,
      status: request.status,
      namespace: request.namespace,
      system: request.system,
      system_version: request.system_version,
      instance_name: request.instance_name,
      created_at: new Date(request.created_at).toLocaleString(),
      status_updated_at: new Date(request.status_updated_at).toLocaleString(),
      updated_at: new Date(request.updated_at).toLocaleString(),
      comment: request.comment,
      parent: request.parent_id,
      has_parent: request.has_parent,
      deltaTime: timeDelta(
        new Date(request.created_at),
        new Date(request.status_updated_at),
      ),
      raw_request: request,
    },
    children: [] as Array<ExtendedTreeItemProps>,
  };

  if (
    typeof request.children !== "undefined" &&
    request.children !== null &&
    request.children.length > 0
  ) {
    request.children.forEach((childRequest: Request) => {
      const child_item = parseRequest(childRequest);
      item.children.push(child_item);
    });
  }

  return item;
}

interface RequestTreeMenuProps {
  rootRequest?: Request | undefined;
  request?: Request;
  setRequest: (request: Request) => void;
}

function RequestTreeMenu({
  rootRequest,
  request,
  setRequest,
}: RequestTreeMenuProps) {
  const [node, setNode] = useState(
    rootRequest !== undefined ? parseRequest(rootRequest) : {},
  );

  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (rootRequest && rootRequest !== undefined) {
      setNode(parseRequest(rootRequest));
      setIsLoading(false);
    }
  }, [rootRequest]);
  const findRequest = (requestId: string, request?: Request) => {
    if (request === undefined) {
      return;
    }
    if (request.id === requestId) {
      setRequest(request);
      return;
    }

    if (request.children) {
      for (const child of request.children) {
        findRequest(requestId, child);
      }
    }
  };

  const commandIcons = (node: any) => {
    return (
      <div>
        {node.data?.topic && (
          <>
            <Tooltip title={node.data?.topic}>
              <span>
                <FAIcon
                  icon="envelope"
                  sx={{ mr: 2 }}
                  role="img"
                  aria-label={`Topic: ${node.data?.topic}`}
                  aria-hidden={undefined}
                />
              </span>
            </Tooltip>
          </>
        )}
        <Tooltip title={`${node?.data?.command_type} Command`}>
          <Box component="span" aria-label={undefined}>
            {(node.data?.command_type === undefined ||
              node.data?.command_type.length === 0 ||
              node.data?.command_type === "ACTION") && (
              <FAIcon
                icon="a"
                sx={{ mr: 2 }}
                role="img"
                title="Action Command"
                aria-label="Action Command"
              />
            )}
            {node.data?.command_type === "INFO" && (
              <FAIcon
                icon="i"
                sx={{ mr: 2 }}
                role="img"
                title="Info Command"
                aria-label="Info Command"
              />
            )}
            {node.data?.command_type === "TEMP" && (
              <FAIcon
                icon="hourglass"
                sx={{ mr: 2 }}
                role="img"
                title="Temp Command"
                aria-label="Temp Command"
              />
            )}
          </Box>
        </Tooltip>
      </div>
    );
  };

  const nodeTemplate = (node: any) => {
    const statusSeverity = GetSeverity(node.data.status);

    return (
      <Box>
        <Stack>
          <Box sx={{ display: "flex" }}>
            {commandIcons(node)}

            <Typography sx={{ fontWeight: "bold", ml: 1 }}>
              {node.data?.command_display_name ?? node.data?.command}
            </Typography>

            <Chip
              label={node.data.status}
              color={statusSeverity}
              id={`request_menu_status_${node.data.id}`}
              sx={{ ml: 1 }}
            />

            {node.data?.status && ["SUCCESS"].includes(node.data?.status) && (
              <Typography sx={{ ml: 1 }}>{node.data.deltaTime}</Typography>
            )}
            <Tooltip
              title={
                <Box>
                  <Box sx={{ display: "flex" }}>
                    <Typography variant="caption" sx={{ mr: 2 }}>
                      Created At:
                    </Typography>
                    <Typography variant="caption" sx={{ marginLeft: "auto" }}>
                      {node.data?.created_at}
                    </Typography>
                  </Box>
                  <Box sx={{ display: "flex" }}>
                    <Typography variant="caption" sx={{ mr: 2 }}>
                      Status Updated At:
                    </Typography>
                    <Typography variant="caption" sx={{ marginLeft: "auto" }}>
                      {node.data?.status_updated_at}
                    </Typography>
                  </Box>
                  <Box sx={{ display: "flex" }}>
                    <Typography variant="caption" sx={{ mr: 2 }}>
                      Last Updated At:
                    </Typography>
                    <Typography variant="caption" sx={{ marginLeft: "auto" }}>
                      {node.data?.updated_at}
                    </Typography>
                  </Box>
                </Box>
              }
            >
              <FAIcon
                icon="clock"
                sx={{ ml: 1 }}
                role="img"
                aria-label="Request timing information"
                id={`request_duration_${node.data?.id}`}
              />
            </Tooltip>
          </Box>
          <Box>
            <Typography variant="caption">
              {node.data.namespace}-{node.data.system}-
              {node.data.system_version}-{node.data.instance_name}
            </Typography>
          </Box>
        </Stack>
      </Box>
    );
  };

  return (
    node && (
      <TreeMenu
        items={[node]}
        itemTemplate={nodeTemplate}
        expandAll={true}
        changeSelected={(id: string) => findRequest(id, rootRequest)}
        selectedItems={request && request.id ? request.id : undefined}
        sx={{ mt: 2 }}
        isLoading={isLoading}
      />
    )
  );
}

export default RequestTreeMenu;
