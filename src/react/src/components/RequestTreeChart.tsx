import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Column } from "primereact/column";
import { TreeTable } from "primereact/treetable";
import { Link } from "react-router-dom";

import { Request } from "../models/brewtils-types";
import { Config } from "../models/models";
import { DeleteRequest } from "../services/request_service";
import AccessButton from "./AccessButton";

function parseRequest(request: Request, config: Config) {
  const item = {
    key: request.id,
    data: {
      id: request.id,
      command: request.command,
      command_display_name: request.command_display_name,
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
  let node = {};
  if (props.rootRequest !== undefined && props.rootRequest !== null) {
    node = parseRequest(props.rootRequest, props.config);
  }

  const rowClassName = (node: any) => {
    return { "p-highlight": node.data.id === props.currentRequestId };
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
        <Link to={`/request/${node.data.id}`}>
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
          <Link to={`/recreate/${node.data.id}`}>
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
      >
        <Column field="command" header="Command" expander></Column>

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
