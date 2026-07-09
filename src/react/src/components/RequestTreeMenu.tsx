import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Tag } from "primereact/tag";
import { Tooltip } from "primereact/tooltip";
import { Tree, TreeSelectionEvent } from "primereact/tree";
import { TreeNode } from "primereact/treenode";
import { useEffect, useState } from "react";

import { Request } from "../models/brewtils-types";
import { GetSeverity } from "../services/util_service";

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

function parseRequest(request: Request): TreeNode {
  const item = {
    key: request.id,
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
    children: [] as Array<any>,
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

function expandAllKeys(nodes: TreeNode[]): Record<string, boolean> {
  const expanded: Record<string, boolean> = {};
  for (const node of nodes) {
    if (node && node.key) {
      expanded[String(node.key)] = true;
    }
    if (node.children && node.children.length > 0) {
      Object.assign(expanded, expandAllKeys(node.children));
    }
  }
  return expanded;
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
  const [expandedKeys, setExpandedKeys] = useState<Record<string, boolean>>(
    expandAllKeys([node]),
  );

  useEffect(() => {
    if (rootRequest && rootRequest !== undefined) {
      setNode(parseRequest(rootRequest));
    }
  }, [rootRequest]);

  useEffect(() => {
    setExpandedKeys(expandAllKeys([node]));
  }, [node]);

  const findRequest = (requestId: string, request: Request) => {
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

  const updateSelectedRequest = (event: TreeSelectionEvent) => {
    if (event.value && typeof event.value === "string") {
      setSelectedKey(event.value);
      if (rootRequest) {
        findRequest(event.value, rootRequest);
      }
    }
  };

  const commandIcons = (node: any) => {
    return (
      <div>
        {node.data?.topic && (
          <>
            <Tooltip
              content={node.data?.topic}
              target={`#TOPIC_${node.data?.id}`}
            />
            <FontAwesomeIcon
              icon="envelope"
              className="mr-2"
              id={`TOPIC_${node.data?.id}`}
            />
          </>
        )}
        <Tooltip
          content={`${node?.data?.command_type} Command`}
          target={`#ICON_${node.data?.id}`}
        />
        {(node.data?.command_type === undefined ||
          node.data?.command_type.length === 0 ||
          node.data?.command_type === "ACTION") && (
          <FontAwesomeIcon
            icon="a"
            className="mr-2"
            id={`ICON_${node.data?.id}`}
          />
        )}
        {node.data?.command_type === "INFO" && (
          <FontAwesomeIcon
            icon="i"
            className="mr-2"
            id={`ICON_${node.data?.id}`}
          />
        )}
        {node.data?.command_type === "TEMP" && (
          <FontAwesomeIcon
            icon="hourglass"
            className="mr-2"
            id={`ICON_${node.data?.id}`}
          />
        )}
      </div>
    );
  };

  const [selectedKey, setSelectedKey] = useState<string>(request?.id ?? "");
  const nodeTemplate = (node: any, options: any) => {
    const statusSeverity = GetSeverity(node.data.status);

    return (
      <div className={options.className}>
        <div className="flex">
          <div>{commandIcons(node)}</div>
          <div>
            <strong>
              {node.data?.command_display_name ?? node.data?.command}
            </strong>
          </div>
          <div>
            <Tag
              value={node.data.status}
              severity={statusSeverity}
              id={`request_menu_status_${node.data.id}`}
              className="ml-2"
            />
          </div>
          <div>
            <div className="flex">
              {node.data?.status && ["SUCCESS"].includes(node.data?.status) && (
                <span className="ml-2">{node.data.deltaTime}</span>
              )}
              <Tooltip target={`#request_duration_${node.data?.id}`}>
                <div>
                  <div className="flex">
                    <div className="flex-1">Created At:</div>
                    <div className="ml-2 flex-2">{node.data?.created_at}</div>
                  </div>
                  <div className="flex">
                    <div className="flex-1">Status Updated At:</div>
                    <div className="ml-2 flex-2">
                      {node.data?.status_updated_at}
                    </div>
                  </div>
                  <div className="flex">
                    <div className="flex-1">Last Updated At:</div>
                    <div className="ml-2 flex-2">{node.data?.updated_at}</div>
                  </div>
                </div>
              </Tooltip>
              <FontAwesomeIcon
                icon="clock"
                className="ml-2"
                id={`request_duration_${node.data?.id}`}
              />
            </div>
          </div>
        </div>
        <div className="flex">
          <sub>
            {node.data.namespace}-{node.data.system}-{node.data.system_version}-
            {node.data.instance_name}
          </sub>
        </div>
      </div>
    );
  };

  return (
    node && (
      <Tree
        value={[node]}
        selectionMode="single"
        selectionKeys={selectedKey}
        onSelectionChange={updateSelectedRequest}
        nodeTemplate={nodeTemplate}
        className="w-auto"
        expandedKeys={expandedKeys}
      />
    )
  );
}

export default RequestTreeMenu;
