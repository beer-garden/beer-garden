import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Card } from "primereact/card";
import { Column } from "primereact/column";
import { confirmDialog } from "primereact/confirmdialog";
import { DataTable } from "primereact/datatable";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  CronTrigger,
  DateTrigger,
  FileTrigger,
  IntervalTrigger,
  Job,
  Request,
} from "../models/brewtils-types";
import { Config } from "../models/models";
import { useToast } from "../providers/ToastProvider";
import {
  GetJob,
  PauseJob,
  ResumeJob,
  RunAdhocJob,
} from "../services/job_service";
import { GetRequestList } from "../services/request_service";
// import HasAccess from "./HasAccess";
import AccessButton from "./AccessButton";

function SchedulerViewCard({
  jobId,
  listeners,
  removeItem,
  editJob,
  deleteJob,
  isDialog,
  config,
}: {
  jobId: string;
  listeners: Record<string, any>;
  removeItem: (id: string) => void;
  editJob: () => void;
  deleteJob: () => void;
  isDialog: boolean;
  config: Config;
}) {
  const [job, setJob] = useState<Job | undefined>(undefined);

  const [requests, setRequests] = useState<Array<Request> | undefined>(
    undefined,
  );
  const altRequests = useRef<Array<Request>>([]);
  const [loading, setLoading] = useState(false);
  const [totalRecords, setTotalRecords] = useState(0);
  const [lazyParams, setLazyParams] = useState({ first: 0, rows: 5, page: 0 });
  const [recordsUpdated, setRecordsUpdated] = useState(false);

  const navigate = useNavigate();
  const showToast = useToast();

  useEffect(() => {
    if (job === undefined && jobId !== undefined) {
      GetJob(jobId, {})
        .then((responseJob) => {
          setJob(responseJob);
        })
        .catch((error) => {
          console.error("Error fetching job:", error);
          showToast({
            severity: "error",
            summary: "Error",
            detail: `Error fetching job: ${error}`,
            life: 3000,
          });
        });
    } else {
      queryJobRequests();
    }
  }, [job, lazyParams]);

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

  const queryJobRequests = () => {
    setLoading(true);

    const queryHeaders = {
      length: lazyParams.rows,
      start: lazyParams.first,
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
    };
    GetRequestList(queryHeaders)
      .then((data: [Array<Request>, Headers]) => {
        const [requests, headers] = data;

        setDisplayRequests(requests);
        setRecordsUpdated(false);

        if (headers.has("recordsfiltered")) {
          setTotalRecords(parseInt(headers.get("recordsfiltered") || "0", 10));
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
        onClick={queryJobRequests}
        tooltip={recordsUpdated ? "New updates available" : "Refresh"}
      >
        {recordsUpdated && <FontAwesomeIcon icon={"circle-exclamation"} />}
        <FontAwesomeIcon icon="refresh" />
      </AccessButton>
    </div>
  );

  const permissions = {
    config: config,
    hasNamespace: job?.request_template?.namespace,
    hasSystemName: job?.request_template?.system,
    hasSystemVersion: job?.request_template?.system_version,
    hasInstanceName: job?.request_template?.instance_name,
    hasCommandName: job?.request_template?.command,
  };

  const confirmDeleteJob = () => {
    const accept = () => {
      deleteJob();
    };
    const reject = () => {};
    const confirm = () => {
      confirmDialog({
        message: "Are you sure you want to delete this job?",
        header: `Confirm Delete ${job?.name}`,
        icon: "pi pi-exclamation-triangle",
        defaultFocus: "accept",
        accept,
        reject,
      });
    };
    confirm();
  };

  return (
    <Card
      className="justify-content-center"
      unstyled={isDialog}
      style={{ maxHeight: "80vh", overflowY: "auto" }}
      header={
        !isDialog && (
          <AccessButton
            onClick={() => {
              removeItem(jobId);
            }}
            className="mr-2 ml-2 mt-2"
            tooltip={"Close Job " + job?.name}
            data-testid={"CLOSE_JOB_" + job?.name}
          >
            <FontAwesomeIcon icon="xmark" />
          </AccessButton>
        )
      }
      title={
        <div className="flex mb-2">
          <div className="flex-1 flex">
            <div className="mr-2">{job ? job.name : "Loading..."}</div>
          </div>

          <AccessButton
            rounded
            raised
            link
            onClick={() => {
              if (job?.id) {
                RunAdhocJob(job.id).catch((error) => {
                  console.error("Error running job:", error);
                  showToast({
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
            <FontAwesomeIcon icon="forward" />
          </AccessButton>

          <AccessButton
            rounded
            raised
            link
            onClick={() => {
              editJob();
            }}
            title={"Update Job " + job?.name}
            className="mr-2"
            {...permissions}
            permission="OPERATOR"
          >
            <FontAwesomeIcon icon="edit" />
          </AccessButton>
          {job?.status === "RUNNING" && (
            <AccessButton
              rounded
              raised
              link
              onClick={() => {
                PauseJob(job)
                  .then((updatedJob) => {
                    setJob(updatedJob);
                  })
                  .catch((error) => {
                    console.error("Error pausing job:", error);
                    showToast({
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
              <FontAwesomeIcon icon="pause" />
            </AccessButton>
          )}
          {job?.status === "PAUSED" && (
            <AccessButton
              rounded
              raised
              link
              onClick={() => {
                ResumeJob(job)
                  .then((updatedJob) => {
                    setJob(updatedJob);
                  })
                  .catch((error) => {
                    console.error("Error resuming job:", error);
                    showToast({
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
              <FontAwesomeIcon icon="play" />
            </AccessButton>
          )}
          <AccessButton
            rounded
            raised
            link
            onClick={() => confirmDeleteJob(job)}
            title={"Delete Job " + job?.name}
            className="mr-2"
            {...permissions}
            permission="OPERATOR"
          >
            <FontAwesomeIcon icon="trash" />
          </AccessButton>
        </div>
      }
    >
      <div className="flex-1 flex flex-wrap gap-4">
        <div className="mr-4">
          <h2>Job Details</h2>
          {job ? (
            <div>
              <p>
                <strong className="mr-2">Status:</strong>
                {job.status}
              </p>
              <p>
                <strong className="mr-2">Coalesce:</strong>
                {job.coalesce ? "True" : "False"}
              </p>
              <p>
                <strong className="mr-2">Misfire Grace Time:</strong>
                {job.misfire_grace_time ?? "N/A"}
              </p>
              <p>
                <strong className="mr-2">Max Instances:</strong>
                {job.max_instances ?? "N/A"}
              </p>
              <p>
                <strong className="mr-2">Timeout:</strong>
                {job.timeout ?? "N/A"}
              </p>
              <p>
                <strong className="mr-2">Trigger Type:</strong>
                {job.trigger_type?.toUpperCase()}
              </p>
              {job.trigger_type === "cron" && job.trigger && (
                <div>
                  <p>
                    <strong className="mr-2">Cron Expression:</strong>
                    {(job.trigger as CronTrigger).second ?? "*"}{" "}
                    {(job.trigger as CronTrigger).minute ?? "*"}{" "}
                    {(job.trigger as CronTrigger).hour ?? "*"}{" "}
                    {(job.trigger as CronTrigger).day ?? "*"}{" "}
                    {(job.trigger as CronTrigger).month ?? "*"}{" "}
                    {(job.trigger as CronTrigger).dayOfWeek ?? "*"}{" "}
                    {(job.trigger as CronTrigger).year ?? "*"}
                  </p>
                  <p>
                    <strong className="mr-2">Start Date:</strong>
                    {formatDate((job.trigger as CronTrigger).startDate)}
                  </p>
                  <p>
                    <strong className="mr-2">End Date:</strong>
                    {formatDate((job.trigger as CronTrigger).endDate)}
                  </p>
                  <p>
                    <strong className="mr-2">Timezone:</strong>
                    {(job.trigger as CronTrigger).timezone ?? "N/A"}
                  </p>
                  <p>
                    <strong className="mr-2">Jitter:</strong>
                    {(job.trigger as CronTrigger).jitter ?? "N/A"}
                  </p>
                </div>
              )}
              {job.trigger_type === "date" && job.trigger && (
                <div>
                  <p>
                    <strong className="mr-2">Run Date:</strong>
                    {formatDate((job.trigger as DateTrigger).run_date)}
                  </p>
                  <p>
                    <strong className="mr-2">Timezone:</strong>
                    {(job.trigger as DateTrigger).timezone ?? "N/A"}
                  </p>
                </div>
              )}
              {job.trigger_type === "interval" && job.trigger && (
                <div>
                  <p>
                    <strong className="mr-2">Interval:</strong>
                    {(job.trigger as IntervalTrigger).weeks !== undefined &&
                      (job.trigger as IntervalTrigger).weeks !== 0 &&
                      "Every " +
                        (job.trigger as IntervalTrigger).weeks +
                        " Weeks"}
                    {(job.trigger as IntervalTrigger).days !== undefined &&
                      (job.trigger as IntervalTrigger).days !== 0 &&
                      "Every " +
                        (job.trigger as IntervalTrigger).days +
                        " Days"}
                    {(job.trigger as IntervalTrigger).hours !== undefined &&
                      (job.trigger as IntervalTrigger).hours !== 0 &&
                      "Every " +
                        (job.trigger as IntervalTrigger).hours +
                        " Hours"}
                    {(job.trigger as IntervalTrigger).minutes !== undefined &&
                      (job.trigger as IntervalTrigger).minutes !== 0 &&
                      "Every " +
                        (job.trigger as IntervalTrigger).minutes +
                        " Minutes"}
                    {(job.trigger as IntervalTrigger).seconds !== undefined &&
                      (job.trigger as IntervalTrigger).seconds !== 0 &&
                      "Every " +
                        (job.trigger as IntervalTrigger).seconds +
                        " Seconds"}
                  </p>
                  <p>
                    <strong className="mr-2">Start Date:</strong>
                    {formatDate((job.trigger as IntervalTrigger).startDate)}
                  </p>
                  <p>
                    <strong className="mr-2">End Date:</strong>
                    {formatDate((job.trigger as IntervalTrigger).endDate)}
                  </p>
                  <p>
                    <strong className="mr-2">Timezone:</strong>
                    {(job.trigger as IntervalTrigger).timezone ?? "N/A"}
                  </p>
                  <p>
                    <strong className="mr-2">Jitter:</strong>
                    {(job.trigger as IntervalTrigger).jitter ?? "N/A"}
                  </p>
                  <p>
                    <strong className="mr-2">Reschedule On Finish:</strong>
                    {(job.trigger as IntervalTrigger).rescheduleOnFinish
                      ? "True"
                      : "False"}
                  </p>
                </div>
              )}
              {job.trigger_type === "file" && job.trigger && (
                <div>
                  <p>
                    <strong className="mr-2">Path:</strong>
                    {(job.trigger as FileTrigger).path}
                  </p>
                  <p>
                    <strong className="mr-2">Pattern:</strong>
                    {(job.trigger as FileTrigger).pattern}
                  </p>
                  <p>
                    <strong className="mr-2">Recursive:</strong>
                    {(job.trigger as FileTrigger).recursive ? "True" : "False"}
                  </p>
                  <p>
                    <strong className="mr-2">Create:</strong>
                    {(job.trigger as FileTrigger).create ? "True" : "False"}
                  </p>
                  <p>
                    <strong className="mr-2">Modify:</strong>
                    {(job.trigger as FileTrigger).modify ? "True" : "False"}
                  </p>
                  <p>
                    <strong className="mr-2">Delete:</strong>
                    {(job.trigger as FileTrigger).delete ? "True" : "False"}
                  </p>
                  <p>
                    <strong className="mr-2">Move:</strong>
                    {(job.trigger as FileTrigger).move ? "True" : "False"}
                  </p>
                </div>
              )}
            </div>
          ) : (
            <p>Loading job details...</p>
          )}
        </div>
        <div style={{ flexGrow: "1" }}>
          {requests ? (
            <DataTable
              value={requests}
              loading={loading}
              lazy
              paginator
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

export default SchedulerViewCard;
