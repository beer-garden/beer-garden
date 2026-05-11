import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { FilterMatchMode } from "primereact/api";
import { Button } from "primereact/button";
import { Calendar } from "primereact/calendar";
import { Checkbox, CheckboxChangeEvent } from "primereact/checkbox";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { MultiSelect } from "primereact/multiselect";
import {
  RefObject,
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { Link } from "react-router-dom";

import { Request } from "../models/brewtils-types";
import { RequestItem } from "../models/models";
import { TourStepProps } from "../models/models";
import { GetRequestList } from "../services/request_service";
import {
  AddTourStep,
  ClearTourSteps,
  GenerateTourProps,
} from "../services/tour_service";
import { GetBaseURL } from "../services/util_service";

function RequestIndex({
  listeners,
  tourStepsRef,
  addRequestItem,
}: {
  listeners: Record<string, any>;
  tourStepsRef: RefObject<Array<TourStepProps>>;
  addRequestItem: (itemParams?: Partial<RequestItem>) => void;
}) {
  const [requests, setRequests] = useState<Array<Request>>([]);
  const altRequests = useRef<Array<Request>>([]);
  const [loading, setLoading] = useState(false);
  const [totalRecords, setTotalRecords] = useState(0);
  const [lazyParams, setLazyParams] = useState({ first: 0, rows: 10, page: 0 });
  const [recordsUpdated, setRecordsUpdated] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState<boolean>(false);
  const [showHidden, setShowHidden] = useState<boolean>(false);
  const [showChildren, setShowChildren] = useState<boolean>(false);

  const [filters, setFilters] = useState({
    command_display_name: {
      value: null,
      matchMode: FilterMatchMode.STARTS_WITH,
    },
    namespace: { value: null, matchMode: FilterMatchMode.STARTS_WITH },
    system: { value: null, matchMode: FilterMatchMode.STARTS_WITH },
    system_version: { value: null, matchMode: FilterMatchMode.STARTS_WITH },
    instance_name: { value: null, matchMode: FilterMatchMode.STARTS_WITH },
    status: { value: null, matchMode: FilterMatchMode.IN },
    created_at: { value: null, matchMode: FilterMatchMode.DATE_IS },
    comment: { value: null, matchMode: FilterMatchMode.STARTS_WITH },
  });

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

  const lazyLoadData = useCallback(() => {
    setLoading(true);

    const generateFilterQuery = () => {
      const filterQuery: Record<string, any> = {};

      Object.entries(filters).forEach(([field, filterMeta]) => {
        if (field === null || field === undefined) {
          return;
        }

        filterQuery["include"] = filterQuery["include"] || ["id"];
        filterQuery["include"].push(field);

        if (
          filterMeta.value === null ||
          filterMeta.value === undefined ||
          filterMeta.value === ""
        ) {
          return;
        }

        filterQuery["query"] = filterQuery["query"] || [];

        const filter: Record<string, any> = {
          field_name: field,
          modifier: "",
          value: filterMeta.value,
        };

        if (filterMeta.matchMode === FilterMatchMode.STARTS_WITH) {
          filter["modifier"] = "startswith";
        } else if (filterMeta.matchMode === FilterMatchMode.ENDS_WITH) {
          filter["modifier"] = "endswith";
        } else if (filterMeta.matchMode === FilterMatchMode.EQUALS) {
          // Skip
        } else if (filterMeta.matchMode === FilterMatchMode.NOT_EQUALS) {
          filter["modifier"] = "ne";
        } else if (filterMeta.matchMode === FilterMatchMode.CONTAINS) {
          filter["modifier"] = "contains";
        } else if (filterMeta.matchMode === FilterMatchMode.NOT_CONTAINS) {
          filter["modifier"] = "not__contains";
        } else if (filterMeta.matchMode === FilterMatchMode.LESS_THAN) {
          filter["modifier"] = "lt";
        } else if (
          filterMeta.matchMode === FilterMatchMode.LESS_THAN_OR_EQUAL_TO
        ) {
          filter["modifier"] = "lte";
        } else if (filterMeta.matchMode === FilterMatchMode.GREATER_THAN) {
          filter["modifier"] = "gt";
        } else if (
          filterMeta.matchMode === FilterMatchMode.GREATER_THAN_OR_EQUAL_TO
        ) {
          filter["modifier"] = "gte";
        } else if (filterMeta.matchMode === FilterMatchMode.DATE_IS) {
          filter["value"] = (filterMeta.value as Date)
            .toISOString()
            .substring(0, 19)
            .replace("T", " ");
        } else if (filterMeta.matchMode === FilterMatchMode.DATE_IS_NOT) {
          filter["modifier"] = "ne";
          filter["value"] = (filterMeta.value as Date)
            .toISOString()
            .substring(0, 19)
            .replace("T", " ");
        } else if (filterMeta.matchMode === FilterMatchMode.DATE_AFTER) {
          filter["modifier"] = "gt";
          filter["value"] = (filterMeta.value as Date)
            .toISOString()
            .substring(0, 19)
            .replace("T", " ");
        } else if (filterMeta.matchMode === FilterMatchMode.DATE_BEFORE) {
          filter["modifier"] = "lt";
          filter["value"] = (filterMeta.value as Date)
            .toISOString()
            .substring(0, 19)
            .replace("T", " ");
        } else if (filterMeta.matchMode === FilterMatchMode.IN) {
          filter["modifier"] = "in";
          filter["value"] = (filterMeta.value as Array<any>).map(
            (item) => item["name"],
          );
        } else if (filterMeta.matchMode === FilterMatchMode.NOT_IN) {
          filter["modifier"] = "nin";
          filter["value"] = (filterMeta.value as Array<any>).map(
            (item) => item["name"],
          );
        } else {
          // Not Defined yet
        }

        filterQuery["query"].push(JSON.stringify(filter));
      });

      return filterQuery;
    };

    const queryHeaders: Record<string, any> = {
      length: lazyParams.rows,
      start: lazyParams.first,
      ...generateFilterQuery(),
    };

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
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error fetching request list:", error);
        setLoading(false);
      });
  }, [lazyParams, filters, showHidden, showChildren]);

  const onPage = (event: any) => {
    setLazyParams(event);
  };

  const formatDate = (value: string) => {
    const date = new Date(value);
    return date.toLocaleDateString() + " " + date.toLocaleTimeString();
  };

  const dateTimeFilterTemplate = (options: any) => {
    return (
      <Calendar
        value={options.value}
        onChange={(e) => options.filterCallback(e.value, options.index)}
        dateFormat="mm/dd/yy"
        showTime
        hourFormat="24" // or "12"
        placeholder="MM/DD/YYYY HH:MM"
        mask="99/99/9999 99:99"
      />
    );
  };

  const statuses = [
    { name: "CREATED" },
    { name: "RECEIVED" },
    { name: "IN_PROGRESS" },
    { name: "CANCELED" },
    { name: "SUCCESS" },
    { name: "ERROR" },
    { name: "INVALID" },
  ];

  const statusFilterTemplate = (options: any) => {
    return (
      <MultiSelect
        value={options.value}
        onChange={(e) => options.filterCallback(e.value, options.index)}
        options={statuses}
        optionLabel="name"
        placeholder="Status"
        className="w-full md:w-20rem"
      />
    );
  };
  useLayoutEffect(() => {
    if (autoRefresh && recordsUpdated) {
      lazyLoadData();
    }
  }, [autoRefresh, recordsUpdated]);

  const header = (
    <div className="flex flex-wrap align-items-center justify-content-between gap-2">
      <span className="text-xl text-900 font-bold">Requests</span>
      <div className="flex align-items-center">
        <label htmlFor="autoRefreshButton">
          <Checkbox
            id="autoRefreshButton"
            onChange={(e: CheckboxChangeEvent) =>
              setAutoRefresh(e.target?.checked ?? false)
            }
            checked={autoRefresh}
            className="mr-2"
            {...GenerateTourProps(AutoRefreshTourStep)}
          />
          Auto Refresh
        </label>
      </div>
      <div className="flex align-items-center">
        <label className="mr-2" htmlFor="showHiddenButton">
          <Checkbox
            id="showHiddenButton"
            onChange={(e: CheckboxChangeEvent) =>
              setShowHidden(e.target?.checked ?? false)
            }
            checked={showHidden}
            className="mr-2"
            {...GenerateTourProps(ShowHiddenTourStep)}
          />
          Show Hidden
        </label>
        <label className="mr-2" htmlFor="showChildrenButton">
          <Checkbox
            id="showChildrenButton"
            onChange={(e: CheckboxChangeEvent) =>
              setShowChildren(e.target?.checked ?? false)
            }
            checked={showChildren}
            className="mr-2"
            {...GenerateTourProps(ShowChildrenTourStep)}
          />
          Show Children
        </label>
        <Button
          rounded
          raised
          onClick={lazyLoadData}
          tooltip={recordsUpdated ? "New updates available" : "Refresh"}
          {...GenerateTourProps(RefreshTableTourStep)}
        >
          {recordsUpdated && <FontAwesomeIcon icon={"circle-exclamation"} />}
          <FontAwesomeIcon icon="refresh" />
        </Button>
      </div>
    </div>
  );

  const PeekRequestView = (request: Request) => {
    if (request.id) {
      addRequestItem({ requestId: request.id, type: "VIEW_REQUEST" });
    }
  };

  const commandNameTemplate = (request: Request) => {
    if (request.command_display_name) {
      return <span>{request.command_display_name}</span>;
    }
    return <span>{request.command}</span>;
  };

  const commandActionTemplate = (request: Request) => {
    return (
      <div>
        <Link to={`${GetBaseURL()}/request/${request.id}`}>
          <Button
            rounded
            raised
            link
            tooltip={"Open Request " + request.command_display_name}
            className="mr-2"
            {...GenerateTourProps(OpenRequestTourStep)}
          >
            <FontAwesomeIcon icon="arrow-up-right-from-square" />
          </Button>
        </Link>
        <Button
          rounded
          raised
          link
          onClick={() => PeekRequestView(request)}
          tooltip={"View " + request.command_display_name}
          className="mr-2"
          {...GenerateTourProps(ViewRequestTourStep)}
        >
          <FontAwesomeIcon icon="eye" />
        </Button>
      </div>
    );
  };

  useEffect(() => {
    lazyLoadData();
  }, [lazyLoadData, lazyParams, filters]);

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

  return (
    <div>
      <DataTable
        value={requests}
        loading={loading}
        lazy
        paginator
        header={header}
        rows={lazyParams.rows}
        first={lazyParams.first}
        totalRecords={totalRecords}
        onPage={onPage}
        filters={filters}
        onFilter={(e) => setFilters(e.filters as typeof filters)}
        rowsPerPageOptions={[5, 10, 20, 50]}
      >
        <Column header="Actions" body={commandActionTemplate} />
        <Column
          field="command_display_name"
          filter
          header="Command"
          body={commandNameTemplate}
        />
        <Column field="namespace" filter header="Namespace" />
        <Column field="system" filter header="System" />
        <Column field="system_version" filter header="Version" />
        <Column field="instance_name" filter header="Instance" />
        <Column
          field="status"
          filter
          header="Status"
          filterElement={statusFilterTemplate}
          filterMatchModeOptions={[
            { label: "In", value: FilterMatchMode.IN },
            { label: "Not In", value: FilterMatchMode.NOT_IN },
          ]}
        />
        <Column
          field="created_at"
          filter
          dataType="date"
          header="Created"
          body={(rowData) => formatDate(rowData.created_at)}
          filterElement={dateTimeFilterTemplate}
        />
        <Column field="comment" filter header="Comment" />
      </DataTable>
    </div>
  );
}

export default RequestIndex;
