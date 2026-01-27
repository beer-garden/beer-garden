import { TreeTable } from "primereact/treetable";
import { Column } from "primereact/column";
import { Request } from "../models/brewtils-types";
import { Button } from "primereact/button";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { DeleteRequest } from "../services/request_service";

function parseRequest(request: Request, currentRequestId?: string) {
  let item = {
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
      let child_item = parseRequest(childRequest);
      child_item.key = item.key + "-" + child_item.key;
      item.children.push(child_item);
    });
  }

  return item;
}

interface RequestTreeChartProps {
  rootRequest?: Request;
  currentRequestId?: string;
}

function RequestTreeChart(props: RequestTreeChartProps) {
  let node = {};
  if (props.rootRequest !== undefined && props.rootRequest !== null) {
    node = parseRequest(props.rootRequest, props.currentRequestId);
  }

  const rowClassName = (node: any) => {
    return { "p-highlight": node.data.id === props.currentRequestId };
  };

  const actionTemplate = (node: any) => {
    if (node.data.id === props.currentRequestId) {
      return;
    }
    return (
      <div>
        <Button
          rounded
          raised
          link
          onClick={() => window.open("/request/" + node.data.id, "_self")}
          title="Open"
        >
          <FontAwesomeIcon icon="arrow-up-right-from-square" />{" "}
        </Button>
        {!["CANCELED", "SUCCESS", "ERROR", "INVALID"].includes(
          node.data.status,
        ) && (
          <Button rounded raised link onClick={() => {}} title="Cancel">
            <FontAwesomeIcon icon="ban" />{" "}
          </Button>
        )}
        {["CANCELED", "SUCCESS", "ERROR", "INVALID"].includes(
          node.data.status,
        ) && (
          <Button
            rounded
            raised
            link
            onClick={() => DeleteRequest(node.data)}
            title="Delete"
          >
            <FontAwesomeIcon icon="trash" />{" "}
          </Button>
        )}
        {["CANCELED", "SUCCESS", "ERROR", "INVALID"].includes(
          node.data.status,
        ) && (
          <Button
            rounded
            raised
            link
            onClick={() => window.open("/recreate/" + node.data.id, "_self")}
            title="Pour Again"
          >
            <FontAwesomeIcon icon="rotate" />{" "}
          </Button>
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
        <Column body={actionTemplate}> </Column>
      </TreeTable>
    )
  );
}

export default RequestTreeChart;
