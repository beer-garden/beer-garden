import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Column } from "primereact/column";
import { Tooltip } from "primereact/tooltip";
import { TreeTable } from "primereact/treetable";
import { Link } from "react-router-dom";
import { useNavigate } from "react-router-dom";

import { Request } from "../models/brewtils-types";
import AccessButton from "./AccessButton";
import { TreeNode } from "primereact/treenode";
import { useEffect, useState } from "react";

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

function expandAllKeys(nodes: TreeNode[]) {
  const expanded: Record<any, boolean>[] = [];
  for (const node of nodes) {
    if (node.key) {
      expanded.push({ [node.key]: true });
    }
    if (node.children && node.children.length > 0) {
      expanded.push(...expandAllKeys(node.children));
    }
  }
  return expanded;
}

interface RequestTreeChartProps {
  rootRequest?: Request;
  currentRequestId?: string;
}

function RequestTreeChart({
  rootRequest,
  currentRequestId,
}: RequestTreeChartProps) {
  const [node, setNode] = useState(
    rootRequest !== undefined && rootRequest !== null
      ? parseRequest(rootRequest)
      : {},
  );
  const [expandedKeys, setExpandedKeys] = useState(expandAllKeys([node]));

  useEffect(() => {
    if (rootRequest !== undefined && rootRequest !== null) {
      setNode(parseRequest(rootRequest));
    }
  }, [rootRequest]);

  useEffect(() => {
    setExpandedKeys(expandAllKeys([node]));
  }, [node]);

  const navigate = useNavigate();
  const rowClassName = (node: any) => {
    return { "p-highlight": node.data.id === currentRequestId };
  };

  const commandNameTemplate = (node: any) => {
    return (
      <div>
        {node.data.topic && (
          <>
            <Tooltip
              content={node.data.topic}
              target={`#TOPIC_${node.data.id}`}
            />
            <FontAwesomeIcon
              icon="envelope"
              className="mr-2"
              id={`TOPIC_${node.data.id}`}
            />
          </>
        )}
        <Tooltip
          content={`${node.data.command_type} Command`}
          target={`#ICON_${node.data.id}`}
        />
        {(node.data.command_type === undefined ||
          node.data.command_type.length === 0 ||
          node.data.command_type === "ACTION") && (
          <FontAwesomeIcon
            icon="a"
            className="mr-2"
            id={`ICON_${node.data.id}`}
          />
        )}
        {node.data.command_type === "INFO" && (
          <FontAwesomeIcon
            icon="i"
            className="mr-2"
            id={`ICON_${node.data.id}`}
          />
        )}
        {node.data.command_type === "TEMP" && (
          <FontAwesomeIcon
            icon="hourglass"
            className="mr-2"
            id={`ICON_${node.data.id}`}
          />
        )}
        <span>{node.data.command}</span>
      </div>
    );
  };

  const actionTemplate = (node: any) => {
    return (
      <div>
        <Link
          to={`/request/${node.data.id}`}
          aria-label={`Open Request ${node.data.command_display_name ?? node.data.command} ${node.data.id}`}
          tabIndex={-1}
          style={{ textDecoration: "none" }}
        >
          <AccessButton rounded raised link title="Open">
            <FontAwesomeIcon icon="arrow-up-right-from-square" />{" "}
          </AccessButton>
        </Link>
      </div>
    );
  };

  return (
    node && (
      <TreeTable
        value={[node]}
        rowClassName={rowClassName}
        tableStyle={{ minWidth: "50rem" }}
        pt={{
          row: ({ context }: { context: any }) => ({
            "aria-checked": undefined,
            tabIndex: -1,
          }),
          rowTogglerIcon: { tabIndex: 0 },
          root: {
            role: undefined,
          },
        }}
        selectionMode="single"
        onSelectionChange={(e) =>
          navigate(
            `/request/${e.value && typeof e.value === "string" ? e.value.split("-").at(-1) : ""}`,
          )
        }
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
