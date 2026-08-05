import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Box, DialogContent, Grid, Stack, Typography } from "@mui/material";
import { Dayjs } from "dayjs";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { FilterColumn } from "../components/EnhancedTable/models/EnhancedTableModels";
import { Request, Topic } from "../models/brewtils-types";
import { RequestItem } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import { GetRequestList } from "../services/request_service";
import AccessButton from "./AccessButton";
import EnhancedTable from "./EnhancedTable/components/EnhancedTable";

function TopicCard({
  requestItem,
  listeners,
  removeItem,
}: {
  requestItem: RequestItem;
  listeners: Record<string, any>;
  removeItem: (id: string) => void;
}) {
  const [topic, setTopic] = useState<Topic | undefined>(undefined);
  const navigate = useNavigate();
  const showSnackbar = useSnackbar();
  const [requests, setRequests] = useState<Array<Request>>([]);
  const altRequests = useRef<Array<Request>>([]);
  const [loading, setLoading] = useState(false);
  const [totalRecords, setTotalRecords] = useState(0);
  const [filteredRecords, setFilteredRecords] = useState<number>(0);
  const [recordsUpdated, setRecordsUpdated] = useState(false);
  const [reloadRequestsTrigger, setReloadRequestsTrigger] = useState(0);

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
      setReloadRequestsTrigger(reloadRequestsTrigger + 1);
    }
  }, [topic]);

  const setDisplayRequests = (requests: Array<Request>) => {
    setRequests(requests);
    altRequests.current = requests;
  };

  const tableLoadData = (
    columnFilters?: FilterColumn[],
    orderBy?: string,
    order?: "asc" | "desc",
    page?: number,
    rowsPerPage?: number,
  ) => {
    if (topic === undefined) {
      return;
    }

    setLoading(true);

    const queryHeaders: Record<string, any> = {
      length: rowsPerPage,
      start: (rowsPerPage ?? 0) * (page ?? 0),
      query: [
        JSON.stringify({
          field_name: "metadata__bg_topic_id",
          modifier: "",
          value: topic.id,
        }),
      ],
    };

    if (columnFilters) {
      for (const filter of columnFilters) {
        let validFilter = true;

        if (
          filter.column === undefined ||
          filter.modifier === undefined ||
          filter.value === undefined
        ) {
          validFilter = false;
        }

        // Is String Empty
        if (
          validFilter &&
          typeof filter.value === "string" &&
          filter.value.length === 0
        ) {
          validFilter = false;
        }

        // Is Array Empty
        if (
          validFilter &&
          typeof filter.value === "object" &&
          Array.isArray(filter.value) &&
          filter.value.length === 0
        ) {
          validFilter = false;
        }

        if (validFilter) {
          queryHeaders["query"] = queryHeaders["query"] || [];

          if (filter.isDate) {
            queryHeaders["query"].push(
              JSON.stringify({
                field_name: filter.column,
                modifier: filter.modifier === "eq" ? "" : filter.modifier,
                value: (filter.value as Dayjs)
                  .toISOString()
                  .substring(0, 19)
                  .replace("T", " "),
              }),
            );
          } else if (filter.isNumeric) {
            queryHeaders["query"].push(
              JSON.stringify({
                field_name: filter.column,
                modifier: filter.modifier === "eq" ? "" : filter.modifier,
                value: String(filter.value),
              }),
            );
          } else {
            queryHeaders["query"].push(
              JSON.stringify({
                field_name: filter.column,
                modifier: filter.modifier === "eq" ? "" : filter.modifier,
                value:
                  filter.modifier === "exists"
                    ? filter.value === "true"
                    : filter.value,
              }),
            );
          }
        }
      }
    }

    if (order && orderBy) {
      queryHeaders["order_by"] = order === "asc" ? orderBy : "-" + orderBy;
    }

    queryHeaders["include_hidden"] = true;

    queryHeaders["include_children"] = true;

    GetRequestList(queryHeaders)
      .then((data: [Array<Request>, Headers]) => {
        const [requests, headers] = data;

        setDisplayRequests(requests);
        setRecordsUpdated(false);

        if (headers.has("Recordstotal")) {
          setTotalRecords(parseInt(headers.get("Recordstotal") || "0", 10));
        } else {
          setTotalRecords(requests.length);
        }
        if (headers.has("Recordsfiltered")) {
          setFilteredRecords(
            parseInt(headers.get("Recordsfiltered") || "0", 10),
          );
        } else {
          setFilteredRecords(requests.length);
        }
        setLoading(false);
      })
      .catch((error) => {
        setLoading(false);
        showSnackbar({
          severity: "error",
          summary: "Error",
          detail: `Error fetching request list: ${error}`,
          life: 3000,
        });
      });
  };

  const commandNameTemplate = (request: Request) => {
    return (
      <div>
        <AccessButton
          rounded
          raised
          onClick={() => {
            void navigate(`/request/${request.id}`);
            removeItem(requestItem.itemId);
          }}
          title={
            "Open Request " +
            (request.command_display_name ?? request.command ?? request.id)
          }
          sx={{ mr: 2 }}
        >
          <FontAwesomeIcon icon="arrow-up-right-from-square" />
        </AccessButton>
        {request.command_display_name ?? request.command ?? request.id}
      </div>
    );
  };

  const tableHeader = (
    <Grid sx={{ m: 2 }} container>
      <Grid size="grow">
        <Typography sx={{ fontWeight: "bold" }}>Associated Requests</Typography>
      </Grid>
      <Grid>
        <AccessButton
          rounded
          raised
          onClick={() => {
            setReloadRequestsTrigger(reloadRequestsTrigger + 1);
          }}
          tooltip={recordsUpdated ? "New updates available" : "Refresh"}
          sx={{ alignItems: "flex-end" }}
        >
          {recordsUpdated && <FontAwesomeIcon icon={"circle-exclamation"} />}
          <FontAwesomeIcon icon="refresh" />
        </AccessButton>
      </Grid>
    </Grid>
  );

  return (
    <>
      <DialogContent>
        <Stack spacing={2}>
          {topic && (
            <Box sx={{ display: "flex" }}>
              <Typography sx={{ fontWeight: "bold" }}>
                Publisher Count:
              </Typography>
              <Typography sx={{ ml: 2 }}>
                {topic.publisher_count ?? "N/A"}
              </Typography>
            </Box>
          )}
          {topic && topic.subscribers && topic.subscribers.length > 0 && (
            <EnhancedTable
              data={topic.subscribers}
              header={
                <Box sx={{ m: 2 }}>
                  <Typography sx={{ fontWeight: "bold" }}>
                    Subscribers
                  </Typography>
                </Box>
              }
              columns={[
                {
                  id: "consumer_count",
                  label: "Consumer Count",
                  field: "consumer_count",
                  sortable: true,
                  filterable: true,
                  isNumeric: true,
                },
                {
                  id: "garden",
                  label: "Garden",
                  field: "garden",
                  sortable: true,
                  filterable: true,
                  isString: true,
                  template: (row) => row.garden || "*",
                },
                {
                  id: "namespace",
                  label: "Namespace",
                  field: "namespace",
                  sortable: true,
                  filterable: true,
                  isString: true,
                  template: (row) => row.namespace || "*",
                },
                {
                  id: "system",
                  label: "System",
                  field: "system",
                  sortable: true,
                  filterable: true,
                  isString: true,
                  template: (row) => row.system || "*",
                },
                {
                  id: "version",
                  label: "Version",
                  field: "version",
                  sortable: true,
                  filterable: true,
                  isString: true,
                  template: (row) => row.version || "*",
                },
                {
                  id: "instance",
                  label: "Instance",
                  field: "instance",
                  sortable: true,
                  filterable: true,
                  isString: true,
                  template: (row) => row.instance || "*",
                },
                {
                  id: "command",
                  label: "Command",
                  field: "command",
                  sortable: true,
                  filterable: true,
                  isString: true,
                  template: (row) => row.command || "*",
                },
                {
                  id: "subscriber_type",
                  label: "Subscriber Type",
                  field: "subscriber_type",
                  sortable: true,
                  filterable: true,
                  isString: true,
                  options: ["ANNOTATED", "GENERATED", "DYNAMIC"],
                },
              ]}
            />
          )}

          <EnhancedTable
            data={requests}
            columns={[
              {
                id: "command",
                label: "Command",
                field: "command",
                sortable: true,
                filterable: true,
                isString: true,
                template: commandNameTemplate,
              },
              {
                id: "status",
                label: "Status",
                field: "status",
                sortable: true,
                filterable: true,
                isString: true,
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
                id: "created_at",
                label: "Created",
                field: "created_at",
                isDate: true,
                sortable: true,
                filterable: true,
              },
            ]}
            header={tableHeader}
            remoteFilter={tableLoadData}
            dataLength={filteredRecords}
            totalDataLength={totalRecords}
            reloadTable={reloadRequestsTrigger}
            defaultOrderBy="created_at"
            defaultOrder="desc"
            isLoading={loading}
          />
        </Stack>
      </DialogContent>
    </>
  );
}

export default TopicCard;
