import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Column } from "primereact/column";
import { Tooltip } from "primereact/tooltip";
import { TreeTable } from "primereact/treetable";
import { Link } from "react-router-dom";

import { Request } from "../models/brewtils-types";
import { Config } from "../models/models";
import { useToast } from "../providers/ToastProvider";
import { DeleteRequest } from "../services/request_service";
import AccessButton from "./AccessButton";

function parseRequest(request: Request, config: Config) {
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
  };

  if (
    typeof request.children !== "undefined" &&
    request.children !== null &&
    request.children.length > 0
  ) {
    request.children.forEach((childRequest: Request) => {
      const child_item = parseRequest(childRequest, config);
      child_item.key = item.key + "-" + child_item.key;
      item.children.push(child_item);
    });
  }

  return item;
}

interface RequestTreeChartProps {
  rootRequest?: Request;
  currentRequestId?: string;
  config: Config;
}

function RequestTreeChart(props: RequestTreeChartProps) {
  const showToast = useToast();
  let node = {};
  if (props.rootRequest !== undefined && props.rootRequest !== null) {
    node = parseRequest(props.rootRequest, props.config);
  }

  const rowClassName = (node: any) => {
    return { "p-highlight": node.data.id === props.currentRequestId };
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

  const actionTemplate = (node: any, config: Config) => {
    if (node.data.id === props.currentRequestId) {
      return;
    }
    const permissions = {
      config: config,
      hasNamespace: props?.rootRequest?.namespace,
      hasSystemName: props?.rootRequest?.system,
      hasSystemVersion: props?.rootRequest?.system_version,
      hasInstanceName: props?.rootRequest?.instance_name,
      hasCommandName: props?.rootRequest?.command,
    };
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
        {!["CANCELED", "SUCCESS", "ERROR", "INVALID"].includes(
          node.data.status,
        ) && (
          <AccessButton
            rounded
            raised
            link
            onClick={() => {}}
            title="Cancel"
            permission="OPERATOR"
            {...permissions}
          >
            <FontAwesomeIcon icon="ban" />{" "}
          </AccessButton>
        )}
        {["CANCELED", "SUCCESS", "ERROR", "INVALID"].includes(
          node.data.status,
        ) && (
          <AccessButton
            rounded
            raised
            link
            onClick={() =>
              DeleteRequest(node.data).catch((error) => {
                console.error("Error deleting request:", error);
                showToast({
                  severity: "error",
                  summary: "Error",
                  detail: `Error deleting request: ${error}`,
                  life: 3000,
                });
              })
            }
            title="Delete"
            {...permissions}
            permission="OPERATOR"
          >
            <FontAwesomeIcon icon="trash" />{" "}
          </AccessButton>
        )}
        {["CANCELED", "SUCCESS", "ERROR", "INVALID"].includes(
          node.data.status,
        ) && (
          <Link
            to={`/recreate/${node.data.id}`}
            aria-label={`Pour Again Request ${node.data.command_display_name ?? node.data.command} ${node.data.id}`}
            tabIndex={-1}
            style={{ textDecoration: "none" }}
          >
            <AccessButton
              rounded
              raised
              link
              title="Pour Again"
              {...permissions}
              permission="OPERATOR"
            >
              <FontAwesomeIcon icon="rotate" />{" "}
            </AccessButton>
          </Link>
        )}
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
            tabIndex:
              context?.node?.data?.children &&
              context.node.data.children.length > 0
                ? 0
                : -1,
          }),
          root: {
            role: undefined,
          },
        }}
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
        <Column body={(node) => actionTemplate(node, props.config)}> </Column>
      </TreeTable>
    )
  );
}

export default RequestTreeChart;
