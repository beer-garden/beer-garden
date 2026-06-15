import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Column } from "primereact/column";
import { Tooltip } from "primereact/tooltip";
import { TreeNode } from "primereact/treenode";
import { TreeTable } from "primereact/treetable";
import { useEffect, useState } from "react";

import { Request } from "../models/brewtils-types";
import AccessButton from "./AccessButton";

function parseRequest(request: Request): TreeNode {
  const item = {
    key: request.id,
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
      raw_request: request,
    },
    children: [] as Array<any>,
    expanded: true,
  };

  if (
    typeof request.children !== "undefined" &&
    request.children !== null &&
    request.children.length > 0
  ) {
    request.children.forEach((childRequest: Request) => {
      const child_item = parseRequest(childRequest);
      child_item.key = item.key + "-" + child_item.key;
      // child_item.expanded = true;
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

function RequestTreeChart({
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

  return (
    node && (
      <TreeTable
        value={[node]}
        rowClassName={rowClassName}
        tableStyle={{ minWidth: "50rem" }}
        pt={{
          row: {
            "aria-checked": undefined,
            tabIndex: -1,
          },
          rowTogglerIcon: { tabIndex: 0 },
          root: {
            role: undefined,
          },
        }}
        selectionMode="single"
        onSelectionChange={(e) => {
          if (e.value && typeof e.value === "string") {
            const targetRequest = findNodeRequest(e.value, node);
            if (targetRequest) {
              setRequest(targetRequest);
            }
          }
        }}
        expandedKeys={expandedKeys}
        onToggle={(e) => setExpandedKeys(e.value)}
      >
        <Column
          field="command"
          header="Command"
          expander
          body={commandNameTemplate}
        ></Column>

        <Column field="status" header="status"></Column>
        <Column field="namespace" header="Namespace"></Column>
        <Column field="system" header="System"></Column>
        <Column field="system_version" header="System Version"></Column>
        <Column field="instance_name" header="Instance Name"></Column>

        <Column field="created_at" header="Created"></Column>
        <Column field="status_updated_at" header="Status Updated"></Column>
        <Column field="updated_at" header="Updated"></Column>
        <Column field="comment" header="Comment"></Column>
        <Column body={actionTemplate} header="Action">
          {" "}
        </Column>
      </TreeTable>
    )
  );
}

export default RequestTreeChart;
