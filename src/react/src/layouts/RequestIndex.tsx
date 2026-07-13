import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { FilterMatchMode } from "primereact/api";
import { Calendar } from "primereact/calendar";
import { Checkbox, CheckboxChangeEvent } from "primereact/checkbox";
import { Column } from "primereact/column";
import { DataTable, SortOrder } from "primereact/datatable";
import { Divider } from "primereact/divider";
import { MultiSelect } from "primereact/multiselect";
import { Tooltip } from "primereact/tooltip";
import {
  RefObject,
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { Link } from "react-router-dom";

import AccessButton from "../components/AccessButton";
import { ColumnField } from "../components/EnhancedTable";
import EnhancedTable from "../components/EnhancedTable";
import { Request } from "../models/brewtils-types";
import { RequestItem } from "../models/models";
import { TourStepProps } from "../models/models";
import { useToast } from "../providers/ToastProvider";
import { GetRequestList } from "../services/request_service";
import {
  AddTourStep,
  ClearTourSteps,
  GenerateTourProps,
} from "../services/tour_service";
import { GetBaseURL, PaginatorTemplate } from "../services/util_service";

interface LazyParams {
  first: number;
  rows: number;
  page: number;
  sortField: string | undefined;
  sortOrder: SortOrder | undefined;
}

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
  const showToast = useToast();
  const [loading, setLoading] = useState(false);
  const [totalRecords, setTotalRecords] = useState(0);
  const [filteredRecords, setFilteredRecords] = useState<number>(0);
  const [lazyParams, setLazyParams] = useState<LazyParams>({
    first: 0,
    rows: 10,
    page: 0,
    sortField: undefined,
    sortOrder: undefined,
  });
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
        if (showHidden) {
          filterQuery["include"].push("hidden");
        }
        if (showChildren) {
          filterQuery["include"].push("parent");
        }

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

    const generateSortQuery = () => {
      const sortQuery: Record<string, any> = {};

      if (lazyParams.sortField) {
        if (lazyParams.sortOrder && [-1, 1].includes(lazyParams.sortOrder)) {
          sortQuery["order_by"] =
            lazyParams.sortOrder == -1
              ? "-" + lazyParams.sortField
              : lazyParams.sortField;
        }
      }
      return sortQuery;
    };

    const queryHeaders: Record<string, any> = {
      length: lazyParams.rows,
      start: lazyParams.first,
      ...generateFilterQuery(),
      ...generateSortQuery(),
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
        showToast({
          severity: "error",
          summary: "Error",
          detail: `Error fetching request list: ${error}`,
          life: 3000,
        });
      });
  }, [lazyParams, filters, showHidden, showChildren]);

  const onPage = (event: any) => {
    setLazyParams(event);
  };

  const onSort = (event: any) => {
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
      <h1 className="text-xl text-900 font-bold">Requests</h1>
      <div className="flex align-items-center">
        <label className="mr-2" htmlFor="autoRefreshButton">
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
        <AccessButton
          rounded
          raised
          basic
          onClick={lazyLoadData}
          tooltip={recordsUpdated ? "New updates available" : "Refresh"}
          {...GenerateTourProps(RefreshTableTourStep)}
        >
          {recordsUpdated && <FontAwesomeIcon icon={"circle-exclamation"} />}
          <FontAwesomeIcon icon="refresh" />
        </AccessButton>
      </div>
    </div>
  );

  const PeekRequestView = (request: Request) => {
    if (request.id) {
      addRequestItem({ requestId: request.id, type: "VIEW_REQUEST" });
    }
  };

  const commandNameTemplate = (request: Request) => {
    return (
      <div>
        {request.parent && (
          <>
            <Tooltip target=".parent-icon">
              <div className="flex flex-column">
                <div
                  className="justify-center font-bold"
                  style={{ marginBottom: "4px" }}
                >
                  parent request
                </div>
                <Divider className="p-0 mx-0 my-1" />
                <span>{request.parent.command}</span>
              </div>
            </Tooltip>
            <Link
              to={`${GetBaseURL()}/request/${request.parent.id}`}
              style={{ textDecoration: "none" }}
              tabIndex={-1}
            >
              <FontAwesomeIcon
                icon="level-up"
                className="parent-icon mr-2"
                data-pr-position="top"
              />
            </Link>
          </>
        )}
        <span>{request.command_display_name ?? request.command}</span>
        {request.hidden && (
          <FontAwesomeIcon icon="user-secret" style={{ float: "right" }} />
        )}
      </div>
    );
  };

  const commandActionTemplate = (request: Request) => {
    return (
      <div>
        <Link
          to={`/request/${request.id}`}
          aria-label={`Open Request ${request.command_display_name ?? request.command} ${request.id}`}
          tabIndex={-1}
          style={{ textDecoration: "none" }}
        >
          <AccessButton
            rounded
            raised
            link
            basic
            tooltip={`Open Request ${request.command_display_name ?? request.command} ${request.id}`}
            className="mr-2"
            {...GenerateTourProps(OpenRequestTourStep)}
          >
            <FontAwesomeIcon icon="arrow-up-right-from-square" />
          </AccessButton>
        </Link>
        <AccessButton
          rounded
          raised
          link
          basic
          onClick={() => PeekRequestView(request)}
          tooltip={`View Request ${request.command_display_name ?? request.command} ${request.id}`}
          className="mr-2"
          {...GenerateTourProps(ViewRequestTourStep)}
        >
          <FontAwesomeIcon icon="eye" />
        </AccessButton>
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

  const paginatorTemplate = {
    ...PaginatorTemplate,

    CurrentPageReport: () => {
      const lastCount = lazyParams.first + lazyParams.rows;
      if (filteredRecords > 0 && filteredRecords < totalRecords) {
        return (
          <div className="mx-4">
            <span>{`Showing ${lazyParams.first} to ${lastCount > filteredRecords ? filteredRecords : lastCount} of ${filteredRecords} entries (filtered from ${totalRecords} entries)`}</span>
          </div>
        );
      } else {
        return (
          <div className="mx-4">
            <span>{`Showing ${lazyParams.first} to ${lastCount > totalRecords ? totalRecords : lastCount} of ${totalRecords} entries`}</span>
          </div>
        );
      }
    },
  };

  interface HeadCell {
    disablePadding: boolean;
    id: keyof Request;
    label: string;
    numeric: boolean;
  }

  const tableColumns: ColumnField[] = [
    {
      id: "action",
      label: "Action",
      template: commandActionTemplate,
    },
    {
      id: "command",
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

  return (
    <div>
      <EnhancedTable data={requests} columns={tableColumns} header={header} />
      <DataTable
        value={requests}
        loading={loading}
        lazy
        paginator
        header={header}
        rows={lazyParams.rows}
        first={lazyParams.first}
        sortField={lazyParams.sortField}
        sortOrder={lazyParams.sortOrder}
        totalRecords={totalRecords}
        onPage={onPage}
        onSort={onSort}
        filters={filters}
        onFilter={(e) => setFilters(e.filters as typeof filters)}
        rowsPerPageOptions={[5, 10, 20, 50]}
        paginatorTemplate={paginatorTemplate}
        pt={{
          paginator: {
            firstPageIcon: {
              role: "img",
              "aria-label": "First Paginator Icon",
            },
            prevPageIcon: {
              role: "img",
              "aria-label": "Previous Paginator Icon",
            },
            nextPageIcon: {
              role: "img",
              "aria-label": "Next Paginator Icon",
            },
            lastPageIcon: {
              role: "img",
              "aria-label": "Last Paginator Icon",
            },
          },
        }}
      >
        <Column header="Actions" body={commandActionTemplate} />
        <Column
          field="command_display_name"
          filter
          sortable
          header="Command"
          body={commandNameTemplate}
        />
        <Column field="namespace" filter sortable header="Namespace" />
        <Column field="system" filter sortable header="System" />
        <Column field="system_version" filter sortable header="Version" />
        <Column field="instance_name" filter sortable header="Instance" />
        <Column
          field="status"
          filter
          sortable
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
          sortable
          dataType="date"
          header="Created"
          body={(rowData) => formatDate(rowData.created_at)}
          filterElement={dateTimeFilterTemplate}
        />
        <Column field="comment" filter sortable header="Comment" />
      </DataTable>
    </div>
  );
}

export default RequestIndex;
