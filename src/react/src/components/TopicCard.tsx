import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Card } from "primereact/card";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Request, Topic } from "../models/brewtils-types";
import { RequestItem } from "../models/models";
import { useToast } from "../providers/ToastProvider";
import { GetRequestList } from "../services/request_service";
import { PaginatorTemplate } from "../services/util_service";
import AccessButton from "./AccessButton";

function TopicCard({
  requestItem,
  isDialog,
  listeners,
  removeItem,
}: {
  requestItem: RequestItem;
  isDialog: boolean;
  listeners: Record<string, any>;
  removeItem: (id: string) => void;
}) {
  const [topic, setTopic] = useState<Topic | undefined>(undefined);
  const navigate = useNavigate();
  const showToast = useToast();
  const [requests, setRequests] = useState<Array<Request> | undefined>(
    undefined,
  );
  const altRequests = useRef<Array<Request>>([]);
  const [loading, setLoading] = useState(false);
  const [totalRecords, setTotalRecords] = useState(0);
  const [lazyParams, setLazyParams] = useState({ first: 0, rows: 5, page: 0 });
  const [recordsUpdated, setRecordsUpdated] = useState(false);

  useEffect(() => {
    if (topic?.id) {
      const MonitorRequestsAndTopic = (message: any) => {
        if (
          message.payload_type === "Request" &&
          message.payload.metadata?.bg_topic_id === topic.id
        ) {
          let updateList = false;
          const updatedRequests = [] as Array<Request>;

          for (const request of altRequests.current) {
            if (
              message.payload.id === request.id &&
              message.payload.status &&
              request.status &&
              request.status !== message.payload.status
            ) {
              if (
                (request.status === "IN_PROGRESS" &&
                  ["CANCELED", "SUCCESS", "ERROR", "INVALID"].includes(
                    message.payload.status,
                  )) ||
                (request.status === "RECEIVED" &&
                  [
                    "IN_PROGRESS",
                    "CANCELED",
                    "SUCCESS",
                    "ERROR",
                    "INVALID",
                  ].includes(message.payload.status)) ||
                (request.status === "CREATED" &&
                  [
                    "RECEIVED",
                    "IN_PROGRESS",
                    "CANCELED",
                    "SUCCESS",
                    "ERROR",
                    "INVALID",
                  ].includes(message.payload.status))
              ) {
                updateList = true;
                updatedRequests.push(message.payload);
              } else {
                updatedRequests.push(request);
              }
            } else {
              updatedRequests.push(request);
            }
          }

          if (updateList) {
            setDisplayRequests(updatedRequests);
          } else {
            setRecordsUpdated(true);
          }
        } else if (
          message.payload_type === "Topic" &&
          message.payload.id === topic.id
        ) {
          setTopic(message.payload);
        }
      };
      if (topic?.id) {
        listeners[topic?.id] = { listener: MonitorRequestsAndTopic };
      }
      return () => {
        // Cleanup function for when component unmounts
        if (topic?.id) {
          delete listeners[topic?.id];
        }
      };
    }
  }, [listeners]);

  useEffect(() => {
    if (topic === undefined) {
      setTopic(requestItem.topic);
    } else {
      queryTopicRequests();
    }
  }, [topic, lazyParams]);

  const setDisplayRequests = (requests: Array<Request>) => {
    setRequests(requests);
    altRequests.current = requests;
  };

  const queryTopicRequests = () => {
    setLoading(true);

    if (topic?.id) {
      const queryHeaders = {
        length: lazyParams.rows,
        start: lazyParams.first,
        include_children: true,
        include: [
          "id",
          "command",
          "command_display_name",
          "status",
          "created_at",
        ],
        query: [
          JSON.stringify({
            field_name: "metadata__bg_topic_id",
            modifier: "",
            value: topic.id,
          }),
        ],
      };
      GetRequestList(queryHeaders)
        .then((data: [Array<Request>, Headers]) => {
          const [requests, headers] = data;

          setDisplayRequests(requests);
          setRecordsUpdated(false);

          if (headers.has("recordsfiltered")) {
            setTotalRecords(
              parseInt(headers.get("recordsfiltered") || "0", 10),
            );
          } else {
            setTotalRecords(requests.length);
          }
          setLoading(false);
        })
        .catch((error) => {
          console.error("Error fetching request list:", error);
          showToast({
            severity: "error",
            summary: "Error",
            detail: `Error fetching request list: ${error}`,
            life: 3000,
          });
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  };

  const onPage = (event: any) => {
    setLazyParams(event);
  };

  const formatDate = (value: string | undefined) => {
    if (!value) return "N/A";
    const date = new Date(value);
    return date.toLocaleDateString() + " " + date.toLocaleTimeString();
  };

  const commandNameTemplate = (request: Request) => {
    return (
      <div>
        <AccessButton
          rounded
          raised
          link
          onClick={() => void navigate(`/request/${request.id}`)}
          title={
            "Open Request " +
            (request.command_display_name ?? request.command ?? request.id)
          }
          className="mr-2"
        >
          <FontAwesomeIcon icon="arrow-up-right-from-square" />
        </AccessButton>
        {request.command_display_name ?? request.command ?? request.id}
      </div>
    );
  };

  const tableHeader = (
    <div className="flex flex-wrap align-items-center justify-content-between gap-2">
      <span className="text-xl text-900 font-bold">Associated Requests</span>
      <AccessButton
        rounded
        raised
        onClick={queryTopicRequests}
        tooltip={recordsUpdated ? "New updates available" : "Refresh"}
      >
        {recordsUpdated && <FontAwesomeIcon icon={"circle-exclamation"} />}
        <FontAwesomeIcon icon="refresh" />
      </AccessButton>
    </div>
  );

  return (
    <Card
      className="justify-content-center"
      unstyled={isDialog}
      title={!isDialog && requestItem?.topic?.name}
      header={
        !isDialog && (
          <AccessButton
            onClick={() => {
              removeItem(requestItem.itemId);
            }}
            tooltip={`Close Topic View for ${topic?.name ?? "Unknown Topic"}`}
          >
            <FontAwesomeIcon icon="xmark" />
          </AccessButton>
        )
      }
    >
      <div>
        <div className="mr-4">
          {topic && (
            <div>
              <p>
                <strong className="mr-2">Publisher Count:</strong>
                {topic.publisher_count}
              </p>
              {topic?.subscribers && (
                <DataTable
                  data-testid="topic-datatable"
                  value={topic?.subscribers}
                  header={
                    <div className="flex flex-wrap align-items-center justify-content-between gap-2">
                      <span className="text-xl text-900 font-bold">
                        Subscribers
                      </span>
                    </div>
                  }
                  paginator
                  paginatorTemplate={PaginatorTemplate}
                  rows={5}
                >
                  <Column
                    field="consumer_count"
                    sortable
                    filter
                    header="Consumer Count"
                    showFilterMenu={false}
                  />
                  <Column
                    field="garden"
                    sortable
                    filter
                    header="Garden"
                    body={(row) => row.garden || "*"}
                    showFilterMenu={false}
                  />
                  <Column
                    field="namespace"
                    sortable
                    filter
                    header="Namespace"
                    body={(row) => row.namespace || "*"}
                    showFilterMenu={false}
                  />
                  <Column
                    field="system"
                    sortable
                    filter
                    header="System"
                    body={(row) => row.system || "*"}
                    showFilterMenu={false}
                  />
                  <Column
                    field="version"
                    sortable
                    filter
                    header="Version"
                    body={(row) => row.version || "*"}
                    showFilterMenu={false}
                  />
                  <Column
                    field="instance"
                    sortable
                    filter
                    header="Instance"
                    body={(row) => row.instance || "*"}
                    showFilterMenu={false}
                  />
                  <Column
                    field="command"
                    sortable
                    filter
                    header="Command"
                    body={(row) => row.command || "*"}
                    style={{ maxWidth: "300px", overflowWrap: "break-word" }}
                    showFilterMenu={false}
                  />

                  <Column
                    field="subscriber_type"
                    sortable
                    filter
                    header="Subscriber Type"
                    showFilterMenu={false}
                  />
                </DataTable>
              )}
            </div>
          )}
        </div>
        <div style={{ flexGrow: "1" }}>
          {requests ? (
            <DataTable
              value={requests}
              loading={loading}
              lazy
              paginator
              paginatorTemplate={PaginatorTemplate}
              header={tableHeader}
              rows={lazyParams.rows}
              first={lazyParams.first}
              totalRecords={totalRecords}
              onPage={onPage}
              rowsPerPageOptions={[5, 10, 20, 50]}
            >
              <Column header="Command" body={commandNameTemplate} />
              <Column field="status" header="Status" />
              <Column
                field="created_at"
                dataType="date"
                header="Created"
                body={(rowData) => formatDate(rowData.created_at)}
              />
            </DataTable>
          ) : (
            <p>Loading Requests...</p>
          )}
        </div>
      </div>
    </Card>
  );
}

export default TopicCard;
