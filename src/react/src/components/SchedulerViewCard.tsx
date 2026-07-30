import { Box, DialogContent, Grid, Typography } from "@mui/material";
import { Dayjs } from "dayjs";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import ConfirmDialog from "../components/ConfirmDialog";
import { FilterColumn } from "../components/EnhancedTable//models/EnhancedTableModels";
import EnhancedTable from "../components/EnhancedTable/components/EnhancedTable";
import {
  CronTrigger,
  DateTrigger,
  FileTrigger,
  IntervalTrigger,
  Job,
  Request,
} from "../models/brewtils-types";
import { Config } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import {
  GetJob,
  PauseJob,
  ResumeJob,
  RunAdhocJob,
} from "../services/job_service";
import { GetRequestList } from "../services/request_service";
import { FAIcon } from "../services/util_service";
import AccessButton from "./AccessButton";

function SchedulerViewCard({
  jobId,
  listeners,
  editJob,
  deleteJob,
  config,
}: {
  jobId: string;
  listeners: Record<string, any>;
  editJob: () => void;
  deleteJob: () => void;
  config: Config;
}) {
  const [job, setJob] = useState<Job | undefined>(undefined);

  const [requests, setRequests] = useState<Array<Request>>([]);
  const altRequests = useRef<Array<Request>>([]);
  const [loading, setLoading] = useState(false);
  const [totalRecords, setTotalRecords] = useState(0);
  const [filteredRecords, setFilteredRecords] = useState<number>(0);
  const [reloadRequestsTrigger, setReloadRequestsTrigger] = useState(0);
  const [recordsUpdated, setRecordsUpdated] = useState(false);

  const [showDelete, setShowDelete] = useState(false);

  const navigate = useNavigate();
  const showSnackbar = useSnackbar();

  useEffect(() => {
    if (job === undefined && jobId !== undefined) {
      GetJob(jobId, {})
        .then((responseJob) => {
          setJob(responseJob);
        })
        .catch((error) => {
          console.error("Error fetching job:", error);
          showSnackbar({
            severity: "error",
            summary: "Error",
            detail: `Error fetching job: ${error}`,
            life: 3000,
          });
        });
    } else {
      setReloadRequestsTrigger(reloadRequestsTrigger + 1);
    }
  }, [job]);

  useEffect(() => {
    if (!(jobId && jobId in listeners)) {
      const MonitorRequestsAndJob = (message: any) => {
        if (
          message.payload_type === "Request" &&
          message.payload.metadata?.bg_job_id === jobId
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
          message.payload_type === "Job" &&
          message.payload.id === jobId
        ) {
          setJob(message.payload);
        }
      };
      if (jobId) {
        listeners[jobId] = { listener: MonitorRequestsAndJob };
      }
      return () => {
        // Cleanup function for when component unmounts
        if (jobId) {
          delete listeners[jobId];
        }
      };
    }
  }, [listeners]);

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
    if (job === undefined && jobId !== undefined) {
      return;
    }

    setLoading(true);

    const queryHeaders = {
      length: rowsPerPage,
      start: (rowsPerPage ?? 0) * (page ?? 0),
      include: [
        "id",
        "command",
        "command_display_name",
        "status",
        "created_at",
      ],
      query: [
        JSON.stringify({
          field_name: "metadata__bg_job_id",
          modifier: "",
          value: jobId,
        }),
      ],
    } as Record<string, string | number | string[]>;

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

          if (Array.isArray(queryHeaders["query"])) {
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
    }

    if (order && orderBy) {
      queryHeaders["order_by"] = order === "asc" ? orderBy : "-" + orderBy;
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

  const formatDate = (value: string | undefined) => {
    if (!value) return "N/A";
    const date = new Date(value);
    return date.toLocaleDateString() + " " + date.toLocaleTimeString();
  };

  const commandNameTemplate = (request: Request) => {
    return (
      <>
        <AccessButton
          rounded
          raised
          onClick={() => void navigate(`/request/${request.id}`)}
          title={
            "Open Request " +
            (request.command_display_name ?? request.command ?? request.id)
          }
          sx={{ mr: 2 }}
        >
          <FAIcon icon="arrow-up-right-from-square" />
        </AccessButton>
        {request.command_display_name ?? request.command ?? request.id}
      </>
    );
  };

  const tableHeader = (
    <Grid container sx={{ mx: 2, mt: 2 }}>
      <Grid size="grow">
        <Typography variant="subtitle1">Associated Requests</Typography>
      </Grid>
      <Grid>
        <AccessButton
          rounded
          raised
          onClick={() => setReloadRequestsTrigger(reloadRequestsTrigger + 1)}
          tooltip={recordsUpdated ? "New updates available" : "Refresh"}
        >
          {recordsUpdated && <FAIcon icon={"circle-exclamation"} />}
          <FAIcon icon="refresh" />
        </AccessButton>
      </Grid>
    </Grid>
  );

  const permissions = {
    config: config,
    hasNamespace: job?.request_template?.namespace,
    hasSystemName: job?.request_template?.system,
    hasSystemVersion: job?.request_template?.system_version,
    hasInstanceName: job?.request_template?.instance_name,
    hasCommandName: job?.request_template?.command,
  };

  const jobDetailDisplay = (label: string, value: any) => {
    return (
      <Box sx={{ display: "flex" }}>
        <Typography
          variant="h6"
          sx={{
            justifyContent: "center",
            alignItems: "center",
            display: "flex",
            mx: 1,
          }}
        >
          {label}:
        </Typography>
        <Typography
          variant="body1"
          sx={{
            justifyContent: "center",
            alignItems: "center",
            display: "flex",
            mx: 1,
          }}
        >
          {value}
        </Typography>
      </Box>
    );
  };

  return (
    <>
      <ConfirmDialog
        open={showDelete}
        setOpen={setShowDelete}
        accept={deleteJob}
        reject={() => {}}
        header={`Confirm Delete ${job?.name}`}
        message="Are you sure you want to delete this job?"
      />
      <DialogContent dividers>
        <Grid container>
          <Grid
            size="grow"
            sx={{
              justifyContent: "center",
              alignItems: "center",

              mx: 1,
            }}
          >
            <Typography variant="h2" sx={{ m: 2 }}>
              {job ? job.name : "Loading..."}
            </Typography>
          </Grid>
          <Grid
            sx={{
              alignSelf: "center",
            }}
          >
            <AccessButton
              rounded
              raised
              onClick={() => {
                if (job?.id) {
                  RunAdhocJob(job.id).catch((error) => {
                    console.error("Error running job:", error);
                    showSnackbar({
                      severity: "error",
                      summary: "Error",
                      detail: `Error running job: ${error}`,
                      life: 3000,
                    });
                  });
                }
              }}
              title={"Run Now " + job?.name}
              className="mr-2"
              {...permissions}
              permission="OPERATOR"
            >
              <FAIcon icon="forward" />
            </AccessButton>

            <AccessButton
              rounded
              raised
              onClick={() => {
                editJob();
              }}
              title={"Update Job " + job?.name}
              className="mr-2"
              {...permissions}
              permission="OPERATOR"
            >
              <FAIcon icon="edit" />
            </AccessButton>
            {job?.status === "RUNNING" && (
              <AccessButton
                rounded
                raised
                onClick={() => {
                  PauseJob(job)
                    .then((updatedJob) => {
                      setJob(updatedJob);
                    })
                    .catch((error) => {
                      console.error("Error pausing job:", error);
                      showSnackbar({
                        severity: "error",
                        summary: "Error",
                        detail: `Error pausing job: ${error}`,
                        life: 3000,
                      });
                    });
                }}
                title={"Pause Job " + job?.name}
                className="mr-2"
                {...permissions}
                permission="OPERATOR"
              >
                <FAIcon icon="pause" />
              </AccessButton>
            )}
            {job?.status === "PAUSED" && (
              <AccessButton
                rounded
                raised
                onClick={() => {
                  ResumeJob(job)
                    .then((updatedJob) => {
                      setJob(updatedJob);
                    })
                    .catch((error) => {
                      console.error("Error resuming job:", error);
                      showSnackbar({
                        severity: "error",
                        summary: "Error",
                        detail: `Error resuming job: ${error}`,
                        life: 3000,
                      });
                    });
                }}
                title={"Resume Job " + job?.name}
                className="mr-2"
                {...permissions}
                permission="OPERATOR"
              >
                <FAIcon icon="play" />
              </AccessButton>
            )}
            <AccessButton
              rounded
              raised
              onClick={() => setShowDelete(true)}
              title={"Delete Job " + job?.name}
              className="mr-2"
              {...permissions}
              permission="OPERATOR"
            >
              <FAIcon icon="trash" />
            </AccessButton>
          </Grid>
        </Grid>

        <Grid container>
          <Grid sx={{ m: 2 }}>
            <Typography variant="h6" sx={{ m: 1 }}>
              Job Details
            </Typography>
            {job ? (
              <>
                {jobDetailDisplay("Status", job.status)}
                {jobDetailDisplay("Coalesce", job.coalesce ? "True" : "False")}
                {jobDetailDisplay(
                  "Misfire Grace Time",
                  job.misfire_grace_time ?? "N/A",
                )}

                {jobDetailDisplay("Max Instances", job.max_instances ?? "N/A")}
                {jobDetailDisplay("Timeout", job.timeout ?? "N/A")}
                {jobDetailDisplay(
                  "Trigger Type",
                  job.trigger_type?.toUpperCase(),
                )}

                {job.trigger_type === "cron" && job.trigger && (
                  <>
                    {jobDetailDisplay(
                      "Cron Expression",
                      `${(job.trigger as CronTrigger).second ?? "*"} ${(job.trigger as CronTrigger).minute ?? "*"} ${(job.trigger as CronTrigger).hour ?? "*"} ${(job.trigger as CronTrigger).day ?? "*"} ${(job.trigger as CronTrigger).month ?? "*"} ${(job.trigger as CronTrigger).dayOfWeek ?? "*"} ${(job.trigger as CronTrigger).year ?? "*"}`,
                    )}
                    {jobDetailDisplay(
                      "Start Date",
                      formatDate((job.trigger as CronTrigger).startDate),
                    )}
                    {jobDetailDisplay(
                      "End Date",
                      formatDate((job.trigger as CronTrigger).endDate),
                    )}
                    {jobDetailDisplay(
                      "Timezone",
                      (job.trigger as CronTrigger).timezone ?? "N/A",
                    )}
                    {jobDetailDisplay(
                      "Jitter",
                      (job.trigger as CronTrigger).jitter ?? "N/A",
                    )}
                  </>
                )}
                {job.trigger_type === "date" && job.trigger && (
                  <>
                    {jobDetailDisplay(
                      "Run Date",
                      formatDate((job.trigger as DateTrigger).run_date),
                    )}
                    {jobDetailDisplay(
                      "Timezone",
                      (job.trigger as DateTrigger).timezone ?? "N/A",
                    )}
                  </>
                )}
                {job.trigger_type === "interval" && job.trigger && (
                  <>
                    {(job.trigger as IntervalTrigger).weeks !== undefined &&
                      (job.trigger as IntervalTrigger).weeks !== 0 &&
                      jobDetailDisplay(
                        "Interval",
                        `Every ${(job.trigger as IntervalTrigger).weeks} Weeks`,
                      )}
                    {(job.trigger as IntervalTrigger).days !== undefined &&
                      (job.trigger as IntervalTrigger).days !== 0 &&
                      jobDetailDisplay(
                        "Interval",
                        `Every ${(job.trigger as IntervalTrigger).days} Days`,
                      )}
                    {(job.trigger as IntervalTrigger).hours !== undefined &&
                      (job.trigger as IntervalTrigger).hours !== 0 &&
                      jobDetailDisplay(
                        "Interval",
                        `Every ${(job.trigger as IntervalTrigger).hours} Hours`,
                      )}
                    {(job.trigger as IntervalTrigger).minutes !== undefined &&
                      (job.trigger as IntervalTrigger).minutes !== 0 &&
                      jobDetailDisplay(
                        "Interval",
                        `Every ${(job.trigger as IntervalTrigger).minutes} Minutes`,
                      )}
                    {(job.trigger as IntervalTrigger).seconds !== undefined &&
                      (job.trigger as IntervalTrigger).seconds !== 0 &&
                      jobDetailDisplay(
                        "Interval",
                        `Every ${(job.trigger as IntervalTrigger).seconds} Seconds`,
                      )}
                    {jobDetailDisplay(
                      "Start Date",
                      formatDate((job.trigger as IntervalTrigger).startDate),
                    )}
                    {jobDetailDisplay(
                      "End Date",
                      formatDate((job.trigger as IntervalTrigger).endDate),
                    )}
                    {jobDetailDisplay(
                      "Timezone",
                      (job.trigger as IntervalTrigger).timezone ?? "N/A",
                    )}
                    {jobDetailDisplay(
                      "Jitter",
                      (job.trigger as IntervalTrigger).jitter ?? "N/A",
                    )}
                    {jobDetailDisplay(
                      "Reschedule On Finish",
                      (job.trigger as IntervalTrigger).rescheduleOnFinish
                        ? "True"
                        : "False",
                    )}
                  </>
                )}
                {job.trigger_type === "file" && job.trigger && (
                  <>
                    {jobDetailDisplay(
                      "Path",
                      (job.trigger as FileTrigger).path,
                    )}
                    {jobDetailDisplay(
                      "Pattern",
                      (job.trigger as FileTrigger).pattern,
                    )}
                    {jobDetailDisplay(
                      "Recursive",
                      (job.trigger as FileTrigger).recursive ? "True" : "False",
                    )}
                    {jobDetailDisplay(
                      "Create",
                      (job.trigger as FileTrigger).create ? "True" : "False",
                    )}
                    {jobDetailDisplay(
                      "Modify",
                      (job.trigger as FileTrigger).modify ? "True" : "False",
                    )}
                    {jobDetailDisplay(
                      "Delete",
                      (job.trigger as FileTrigger).delete ? "True" : "False",
                    )}
                    {jobDetailDisplay(
                      "Move",
                      (job.trigger as FileTrigger).move ? "True" : "False",
                    )}
                  </>
                )}
              </>
            ) : (
              <Typography variant="body1" sx={{ m: 1 }}>
                Loading job details...
              </Typography>
            )}
          </Grid>

          <Grid size="grow">
            <EnhancedTable
              data={requests}
              columns={[
                {
                  id: "command",
                  label: "Command",
                  template: commandNameTemplate,
                },
                {
                  id: "status",
                  field: "status",
                  label: "status",
                  sortable: true,
                  filterable: true,
                  isString: true,
                },
                {
                  id: "created_at",
                  field: "created_at",
                  label: "Created",
                  sortable: true,
                  filterable: true,
                  isDate: true,
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
          </Grid>
        </Grid>
      </DialogContent>
    </>
  );
}

export default SchedulerViewCard;
