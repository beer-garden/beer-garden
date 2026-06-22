import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Column } from "primereact/column";
import { Tag } from "primereact/tag";
import { Tooltip } from "primereact/tooltip";
import { Tree } from "primereact/tree";
import { TreeNode } from "primereact/treenode";
import { useEffect, useState } from "react";

import { Request } from "../models/brewtils-types";
import { GetSeverity } from "../services/util_service";
import AccessButton from "./AccessButton";

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
    return `${diffHours}h: ${diffMinutes}m: ${diffSeconds}s`;
  }
  if (diffMinutes > 0) {
    return `${diffMinutes}m: ${diffSeconds}s`;
  }
  if (diffSeconds > 0) {
    return `${diffSeconds}s`;
  }
  return "< 1s";
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
      child_item.key = item.key + "-" + child_item.key;
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

interface RequestTreeChartProps {
  rootRequest?: Request | undefined;
  request?: Request;
  setRequest: (request: Request) => void;
}

function RequestTreeMenu({
  rootRequest,
  request,
  setRequest,
}: RequestTreeChartProps) {
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

  const rowClassName = (node: any) => {
    return { "p-highlight": node?.data?.id === request?.id };
  };

  const commandNameTemplate = (node: any) => {
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
        <span>{node.data?.command}</span>
      </div>
    );
  };

  const actionTemplate = (node: any) => {
    return (
      <div>
        <AccessButton
          rounded
          raised
          link
          title={`Open Request ${node.data?.command_display_name ?? node.data?.command} ${node.data?.id}`}
          onClick={() => setRequest(node.data?.raw_request)}
        >
          <FontAwesomeIcon icon="arrow-up-right-from-square" />{" "}
        </AccessButton>
      </div>
    );
  };

  const findNodeRequest = (
    nodeKey: string,
    node: TreeNode,
  ): Request | undefined => {
    if (node.key === nodeKey) {
      return node.data.raw_request;
    }
    if (node?.children) {
      for (const child of node.children) {
        const childRequest = findNodeRequest(nodeKey, child);
        if (childRequest) {
          return childRequest;
        }
      }
    }

    return undefined;
  };
  const [selectedKey, setSelectedKey] = useState<string>(request?.id ?? "");
  const nodeTemplate = (node: any, options: any) => {
    const label = <b>{node.label} </b>;
    const statusSeverity = GetSeverity(node.data.status);

    return (
      <div className={options.className}>
        <div className="flex">
          <b>{node.label}</b>
          <Tag
            value={node.data.status}
            severity={statusSeverity}
            id={`status_${node.data.id}`}
            className="ml-2"
          />
          {node.data?.status && ["SUCCESS"].includes(node.data?.status) && (
            <>
            <span className="ml-4">{node.data.deltaTime}</span>
            <FontAwesomeIcon
            icon="clock"
            className="ml-2"
            id={`request_duration_${node.data?.id}`}
          />
          </>
          )}
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
        onSelectionChange={(e) => setSelectedKey(e.value)}
        nodeTemplate={nodeTemplate}
        className="w-full md:w-30rem"
      />
    )
  );
}

export default RequestTreeMenu;
