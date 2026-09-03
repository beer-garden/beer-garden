import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  Box,
  Checkbox,
  Divider,
  FormLabel,
  Tooltip,
  Typography,
} from "@mui/material";
import { Dayjs } from "dayjs";
import { RefObject, useEffect, useLayoutEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import AccessButton from "../components/AccessButton";
import EnhancedTable from "../components/EnhancedTable/components/EnhancedTable";
import {
  ColumnField,
  FilterColumn,
} from "../components/EnhancedTable/models/EnhancedTableModels";
import { Request } from "../models/brewtils-types";
import { Config, RequestItem } from "../models/models";
import { TourStepProps } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import { GetRequestList } from "../services/request_service";
import {
  AddTourStep,
  ClearTourSteps,
  GenerateTourProps,
} from "../services/tour_service";
import { FAIcon, GetBaseURL } from "../services/util_service";

function RequestIndex({
  listeners,
  tourStepsRef,
  addRequestItem,
  config,
}: {
  listeners: Record<string, any>;
  tourStepsRef: RefObject<Array<TourStepProps>>;
  addRequestItem: (itemParams?: Partial<RequestItem>) => void;
  config: Config;
}) {
  const [requests, setRequests] = useState<Array<Request>>([]);
  const altRequests = useRef<Array<Request>>([]);
  const showSnackbar = useSnackbar();
  const [loading, setLoading] = useState(false);
  const [totalRecords, setTotalRecords] = useState(0);
  const [filteredRecords, setFilteredRecords] = useState<number>(0);

  const [recordsUpdated, setRecordsUpdated] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState<boolean>(false);
  const [showHidden, setShowHidden] = useState<boolean>(false);
  const [showChildren, setShowChildren] = useState<boolean>(false);
  const [reloadRequestsTrigger, setReloadRequestsTrigger] = useState(0);

  const setDisplayRequests = (requests: Array<Request>) => {
    setRequests(requests);
    altRequests.current = requests;
  };

  const tourPrefix = "request-index";
  const tourUUID = "main-table";

  const AutoRefreshTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUUID,
    label: "Auto Refresh",
    content:
      "Toggling this option will automatically refresh the table when new updates are available.",
    layer: "LAYOUT",
    pos: 0,
  };

  const ShowHiddenTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUUID,
    label: "Show Hidden",
    content: "Toggling this option will show hidden requests.",
    layer: "LAYOUT",
    pos: 1,
  };

  const ShowChildrenTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUUID,
    label: "Show Children",
    content: "Toggling this option will show child requests.",
    layer: "LAYOUT",
    pos: 2,
  };

  const RefreshTableTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUUID,
    label: "Refresh Table",
    content:
      "Clicking this button will refresh the table with the latest data.",
    layer: "LAYOUT",
    pos: 3,
  };

  const OpenRequestTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUUID,
    label: `Open Request`,
    content: `View details about this request on View Request Page`,
    layer: "LAYOUT",
    pos: 4,
  };

  const ViewRequestTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUUID,
    label: `View Request`,
    content: `View Request in popup modal.`,
    layer: "LAYOUT",
    pos: 5,
  };

  const ViewJobTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUUID,
    label: `View Job`,
    content: `View associated Job in popup modal.`,
    layer: "LAYOUT",
    pos: 6,
  };

  useLayoutEffect(() => {
    if (autoRefresh && recordsUpdated) {
      setReloadRequestsTrigger(reloadRequestsTrigger + 1);
    }
  }, [autoRefresh, recordsUpdated]);

  useEffect(() => {
    setReloadRequestsTrigger(reloadRequestsTrigger + 1);
  }, [showChildren, showHidden]);

  const header = (
    <Box sx={{ display: "flex", justifyContent: "space-between", mx: 2 }}>
      <Typography variant="h2" component="h1">
        Requests
      </Typography>
      <Box sx={{ display: "flex", alignItems: "center" }}>
        <Checkbox
          id="autoRefreshButton"
          onChange={(e) => setAutoRefresh(e.target?.checked ?? false)}
          checked={autoRefresh}
          sx={{ mr: 2 }}
          {...GenerateTourProps(AutoRefreshTourStep)}
        />
        <FormLabel sx={{ mr: 2 }} htmlFor="autoRefreshButton">
          Auto Refresh
        </FormLabel>

        <Checkbox
          id="showHiddenButton"
          onChange={(e) => setShowHidden(e.target?.checked ?? false)}
          checked={showHidden}
          sx={{ mr: 2 }}
          {...GenerateTourProps(ShowHiddenTourStep)}
        />
        <FormLabel sx={{ mr: 2 }} htmlFor="showHiddenButton">
          Show Hidden
        </FormLabel>

        <Checkbox
          id="showChildrenButton"
          onChange={(e) => setShowChildren(e.target?.checked ?? false)}
          checked={showChildren}
          sx={{ mr: 2 }}
          {...GenerateTourProps(ShowChildrenTourStep)}
        />
        <FormLabel sx={{ mr: 2 }} htmlFor="showChildrenButton">
          Show Children
        </FormLabel>

        <AccessButton
          basic
          onClick={() => setReloadRequestsTrigger(reloadRequestsTrigger + 1)}
          tooltip={recordsUpdated ? "New updates available" : "Refresh"}
          {...GenerateTourProps(RefreshTableTourStep)}
        >
          {recordsUpdated && <FontAwesomeIcon icon={"circle-exclamation"} />}
          <FontAwesomeIcon icon="refresh" />
        </AccessButton>
      </Box>
    </Box>
  );

  const PeekRequestView = (request: Request) => {
    if (request.id) {
      addRequestItem({ requestId: request.id, type: "VIEW_REQUEST" });
    }
  };

  const PeekJobView = (request: Request) => {
    if (
      request?.metadata?.bg_job_id &&
      typeof request.metadata.bg_job_id === "string"
    ) {
      addRequestItem({ jobId: request.metadata.bg_job_id, type: "VIEW_JOB" });
    }
  };

  const commandNameTemplate = (request: Request) => {
    return (
      <div>
        {request.parent && (
          <Tooltip
            title={
              <Box>
                <Typography sx={{ fontWeight: "bold" }}>
                  parent request
                </Typography>
                <Divider sx={{ my: 1 }} />
                <span>{request.parent.command}</span>
              </Box>
            }
          >
            <Link
              to={`${GetBaseURL()}/request/${request.parent.id}`}
              style={{ textDecoration: "none" }}
              tabIndex={-1}
            >
              <FAIcon icon="level-up" sx={{ mr: 2 }} data-pr-position="top" />
            </Link>
          </Tooltip>
        )}
        <span>{request.command_display_name ?? request.command}</span>
        {request.hidden && (
          <FontAwesomeIcon icon="user-secret" style={{ float: "right" }} />
        )}
      </div>
    );
  };

  const commandActionTemplate = (request: Request) => {
    const showJob =
      request?.metadata?.bg_job_id !== undefined &&
      request.source_garden === config.garden_name;

    return (
      <div>
        <Link
          to={`/request/${request.id}`}
          aria-label={`Open Request ${request.command_display_name ?? request.command} ${request.id}`}
          tabIndex={-1}
          style={{ textDecoration: "none" }}
        >
          <AccessButton
            basic
            tooltip={`Open Request ${request.command_display_name ?? request.command} ${request.id}`}
            sx={{ mr: 1 }}
            {...GenerateTourProps(OpenRequestTourStep)}
          >
            <FontAwesomeIcon icon="arrow-up-right-from-square" />
          </AccessButton>
        </Link>
        <AccessButton
          basic
          onClick={() => PeekRequestView(request)}
          tooltip={`View Request ${request.command_display_name ?? request.command} ${request.id}`}
          sx={{ mr: 1 }}
          {...GenerateTourProps(ViewRequestTourStep)}
        >
          <FontAwesomeIcon icon="eye" />
        </AccessButton>
        {showJob && (
          <AccessButton
            basic
            onClick={() => PeekJobView(request)}
            tooltip={`View Job ${request?.metadata?.bg_job_id}`}
            sx={{ mr: 1 }}
            {...GenerateTourProps(ViewJobTourStep)}
          >
            <FontAwesomeIcon icon="briefcase" />
          </AccessButton>
        )}
      </div>
    );
  };

  useEffect(() => {
    if (!("requestIndex" in listeners)) {
      const MonitorNewRequests = (message: any) => {
        if (message.payload_type === "Request") {
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
        }
      };
      listeners["requestIndex"] = { listener: MonitorNewRequests };
      return () => {
        // Cleanup function for when component unmounts
        delete listeners["requestIndex"];
      };
    }
  }, [listeners]);

  useEffect(() => {
    ClearTourSteps(tourStepsRef, tourPrefix, tourUUID);
    AddTourStep(tourStepsRef, AutoRefreshTourStep);
    AddTourStep(tourStepsRef, ShowHiddenTourStep);
    AddTourStep(tourStepsRef, ShowChildrenTourStep);
    AddTourStep(tourStepsRef, RefreshTableTourStep);
    if (requests && requests.length > 0) {
      AddTourStep(tourStepsRef, OpenRequestTourStep);
      AddTourStep(tourStepsRef, ViewRequestTourStep);
    }

    return () => {
      ClearTourSteps(tourStepsRef, tourPrefix, tourUUID);
    };
  }, [requests]);

  const tableColumns: ColumnField[] = [
    {
      id: "action",
      label: "Action",
      template: commandActionTemplate,
    },
    {
      id: "command",
      field: "command",
      label: "Command",
      template: commandNameTemplate,
      sortable: true,
      filterable: true,
      isString: true,
    },
    {
      id: "namespace",
      label: "Namespace",
      field: "namespace",
      sortable: true,
      filterable: true,
      isString: true,
    },
    {
      id: "system",
      label: "System",
      field: "system",
      sortable: true,
      filterable: true,
      isString: true,
    },
    {
      id: "system_version",
      label: "Version",
      field: "system_version",
      sortable: true,
      filterable: true,
      isString: true,
    },
    {
      id: "instance_name",
      label: "Instance",
      field: "instance_name",
      sortable: true,
      filterable: true,
      isString: true,
    },
    {
      id: "status",
      label: "Status",
      sortable: true,
      filterable: true,
      field: "status",
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
    {
      id: "comment",
      label: "Comment",
      field: "comment",
      sortable: true,
      filterable: true,
      isString: true,
    },
  ];

  const tableLoadData = (
    columnFilters?: FilterColumn[],
    orderBy?: string,
    order?: "asc" | "desc",
    page?: number,
    rowsPerPage?: number,
  ) => {
    setLoading(true);

    const queryHeaders: Record<string, any> = {
      length: rowsPerPage,
      start: (rowsPerPage ?? 0) * (page ?? 0),
      include: [
        "id",
        "command",
        "namespace",
        "system",
        "system_version",
        "instance_name",
        "status",
        "created_at",
        "comment",
        "source_garden",
        "metadata",
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

    if (showHidden) {
      queryHeaders["include_hidden"] = true;
    }
    if (showChildren) {
      queryHeaders["include_children"] = true;
    }

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

  return (
    <div>
      <EnhancedTable
        data={requests}
        columns={tableColumns}
        header={header}
        remoteFilter={tableLoadData}
        dataLength={filteredRecords}
        totalDataLength={totalRecords}
        reloadTable={reloadRequestsTrigger}
        defaultOrderBy="created_at"
        defaultOrder="desc"
        isLoading={loading}
        defaultRowsPerPageOptions={25}
      />
    </div>
  );
}

export default RequestIndex;
