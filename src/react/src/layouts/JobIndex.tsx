import { Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import { confirmDialog } from "primereact/confirmdialog";
import { RefObject, useEffect, useState } from "react";

import AccessButton from "../components/AccessButton";
import EnhancedTable from "../components/EnhancedTable/components/EnhancedTable";
import { Job } from "../models/brewtils-types";
import { Config, RequestItem, TourStepProps } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import {
  DeleteJob,
  ExportJobs,
  GetJobList,
  ImportJobs,
  PauseJob,
  ResumeJob,
  RunAdhocJob,
} from "../services/job_service";
import {
  AddTourStep,
  ClearTourSteps,
  GenerateTourProps,
} from "../services/tour_service";
import { FAIcon } from "../services/util_service";

function JobIndex({
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
  const showSnackbar = useSnackbar();
  const [jobs, setJobs] = useState<Array<Job>>([]);
  const tourUuid = "job_index_tour";
  const tourPrefix = "job_index";

  const createJobTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Create Job",
    content: "Create a new scheduled job to run requests on a schedule.",
    layer: "LAYOUT",
    pos: 0,
  };

  const importJobTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Import Jobs",
    content: "Import jobs from a file.",
    layer: "LAYOUT",
    pos: 1,
  };

  const exportJobTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Export Jobs",
    content: "Export jobs to a file.",
    layer: "LAYOUT",
    pos: 2,
  };

  const runNowTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Run Now",
    content: "Run the job immediately.",
    layer: "LAYOUT",
    pos: 3,
  };

  const viewJobTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "View Job",
    content: "View details about the job and see past runs.",
    layer: "LAYOUT",
    pos: 4,
  };

  const editJobTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Edit Job",
    content: "Edit the job's schedule and request template.",
    layer: "LAYOUT",
    pos: 5,
  };

  const pauseResumeJobTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Pause/Resume Job",
    content:
      "Pause a running job or resume a paused job to control when it runs.",
    layer: "LAYOUT",
    pos: 6,
  };

  const deleteJobTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Delete Job",
    content: "Delete a job that is no longer needed.",
    layer: "LAYOUT",
    pos: 7,
  };

  const buttonStyle = { m: 1 };

  useEffect(() => {
    ClearTourSteps(tourStepsRef, tourPrefix, tourUuid);
    AddTourStep(tourStepsRef, createJobTourStep);
    AddTourStep(tourStepsRef, importJobTourStep);
    AddTourStep(tourStepsRef, exportJobTourStep);

    if (jobs.length > 0) {
      AddTourStep(tourStepsRef, viewJobTourStep);
      AddTourStep(tourStepsRef, runNowTourStep);
      AddTourStep(tourStepsRef, editJobTourStep);
      AddTourStep(tourStepsRef, pauseResumeJobTourStep);
      AddTourStep(tourStepsRef, deleteJobTourStep);
    }

    return () => {
      ClearTourSteps(tourStepsRef, tourPrefix, tourUuid);
    };
  }, [jobs]);

  useEffect(() => {
    const MonitorJobs = (message: any) => {
      if (message.payload_type === "Job") {
        if (message.name == "JOB_CREATED") {
          setJobs((prevJobs: Job[]) => {
            return [...prevJobs, message.payload];
          });
        } else if (message.name == "JOB_DELETED") {
          setJobs((prevJobs: Job[]) => {
            return prevJobs.filter((job: Job) => job.id != message.payload.id);
          });
        } else if (
          ["JOB_UPDATED", "JOB_PAUSED", "JOB_RESUMED"].includes(message.name)
        ) {
          setJobs((prevJobs: Job[]) => {
            return prevJobs.map((job: Job) => {
              if (job.id === message.payload.id) {
                return {
                  ...job,
                  ...message.payload,
                };
              }
              return job;
            });
          });
        }
      }
    };

    listeners["JobIndex"] = { listener: MonitorJobs };

    return () => {
      // Cleanup function for when component unmounts
      delete listeners["JobIndex"];
    };
  }, [listeners]);

  useEffect(() => {
    GetJobList()
      .then((data: [Array<Job>, Headers]) => {
        const [responseJobs] = data;
        setJobs(responseJobs);
      })
      .catch((error) => {
        showSnackbar({
          severity: "error",
          summary: "Error",
          detail: `Error fetching jobs: ${error}`,
          life: 3000,
        });
      });
  }, []);

  const editJob = (jobId: string) => {
    addRequestItem({ jobId: jobId, type: "REQUEST" });
  };

  const actionTemplate = (job: Job) => {
    const permissions = {
      config: config,
      hasNamespace: job.request_template?.namespace,
      hasSystemName: job.request_template?.system,
      hasInstanceName: job.request_template?.instance_name,
      hasSystemVersion: job.request_template?.system_version,
      hasCommandName: job.request_template?.command,
    };
    
    return (
      <div>
        <AccessButton
          rounded
          raised
          basic
          onClick={() => addRequestItem({ jobId: job.id, type: "VIEW_JOB" })}
          title={"View Job " + job.name}
          sx={buttonStyle}
          {...GenerateTourProps(viewJobTourStep)}
        >
          <FAIcon icon="arrow-up-right-from-square" />
        </AccessButton>
        <>
          <AccessButton
            rounded
            raised
            basic
            onClick={() => {
              if (job.id) {
                RunAdhocJob(job.id).catch((error) => {
                  showSnackbar({
                    severity: "error",
                    summary: "Error",
                    detail: `Error running job: ${error}`,
                    life: 3000,
                  });
                });
              }
            }}
            title={"Run Now " + job.name}
            sx={buttonStyle}
            {...GenerateTourProps(runNowTourStep)}
            {...permissions}
            permission="OPERATOR"
          >
            <FAIcon icon="forward" />
          </AccessButton>

          <AccessButton
            rounded
            raised
            basic
            onClick={() => {
              if (job.id) {
                editJob(job.id);
              }
            }}
            title={"Update Job " + job.name}
            sx={buttonStyle}
            {...GenerateTourProps(editJobTourStep)}
            {...permissions}
            permission="OPERATOR"
          >
            <FAIcon icon="edit" />
          </AccessButton>
          {job.status === "RUNNING" && (
            <AccessButton
              rounded
              raised
              basic
              onClick={() => {
                PauseJob(job)
                  .then((updatedJob) => {
                    setJobs((prevJobs) =>
                      prevJobs.map((j) =>
                        j.id === updatedJob.id ? updatedJob : j,
                      ),
                    );
                  })
                  .catch((error) => {
                    showSnackbar({
                      severity: "error",
                      summary: "Error",
                      detail: `Error pausing job: ${error}`,
                      life: 3000,
                    });
                  });
              }}
              title={"Pause Job " + job.name}
              sx={buttonStyle}
              {...GenerateTourProps(pauseResumeJobTourStep)}
              {...permissions}
              permission="OPERATOR"
            >
              <FAIcon icon="pause" />
            </AccessButton>
          )}
          {job.status === "PAUSED" && (
            <AccessButton
              rounded
              raised
              basic
              onClick={() => {
                ResumeJob(job)
                  .then((updatedJob) => {
                    setJobs((prevJobs) =>
                      prevJobs.map((j) =>
                        j.id === updatedJob.id ? updatedJob : j,
                      ),
                    );
                  })
                  .catch((error) => {
                    showSnackbar({
                      severity: "error",
                      summary: "Error",
                      detail: `Error resuming job: ${error}`,
                      life: 3000,
                    });
                  });
              }}
              title={"Resume Job " + job.name}
              sx={buttonStyle}
              {...GenerateTourProps(pauseResumeJobTourStep)}
              {...permissions}
              permission="OPERATOR"
            >
              <FAIcon icon="play" />
            </AccessButton>
          )}
          <AccessButton
            rounded
            raised
            basic
            onClick={() => {
              const accept = () => {
                DeleteJob(job)
                  .then(() => {
                    setJobs((prevJobs) =>
                      prevJobs.filter((j) => j.id !== job.id),
                    );
                  })
                  .catch((error) => {
                    showSnackbar({
                      severity: "error",
                      summary: "Error",
                      detail: `Error deleting job: ${error}`,
                      life: 3000,
                    });
                  });
              };
              const reject = () => {};
              const confirm = () => {
                confirmDialog({
                  message: "Are you sure you want to delete this job?",
                  header: `Confirm Delete ${job.name}`,
                  icon: "pi pi-exclamation-triangle",
                  defaultFocus: "accept",
                  accept,
                  reject,
                });
              };
              confirm();
            }}
            title={"Delete Job " + job.name}
            sx={buttonStyle}
            {...GenerateTourProps(deleteJobTourStep)}
            {...permissions}
            permission="OPERATOR"
          >
            <FAIcon icon="trash" />
          </AccessButton>
        </>
      </div>
    );
  };

  const createJob = () => {
    addRequestItem({ type: "REQUEST", showSchedule: true });
  };

  const customJobImporter = (event: any) => {
    const file = event?.target?.files?.[0];

    if (!file) {
      showSnackbar({
        severity: "error",
        summary: "Error",
        detail: "No file selected for import",
        life: 3000,
      });
      return;
    }

    const reader = new FileReader();
    reader.onload = async (e) => {
      const contents = e.target?.result;
      if (typeof contents === "string") {
        try {
          await ImportJobs(JSON.parse(contents));
          showSnackbar({
            severity: "success",
            summary: "Success",
            detail: "Jobs imported successfully",
            life: 3000,
          });

          // Refresh the job list after successful import
          GetJobList()
            .then((data: [Array<Job>, Headers]) => {
              const [responseJobs] = data;
              setJobs(responseJobs);
            })
            .catch((error) => {
              showSnackbar({
                severity: "error",
                summary: "Error",
                detail: `Error fetching jobs: ${error}`,
                life: 3000,
              });
            });
        } catch (error) {
          if (error instanceof Error) {
            showSnackbar({
              severity: "error",
              summary: "Error",
              detail: `Failed to import jobs: ${error}`,
              life: 3000,
            });
          } else {
            console.error("Error importing jobs:", error);
            showSnackbar({
              severity: "error",
              summary: "Error",
              detail: "Error importing jobs",
              life: 3000,
            });
          }
        }
      }
    };
    reader.readAsText(file);
  };

  const VisuallyHiddenInput = styled("input")({
    clip: "rect(0 0 0 0)",
    clipPath: "inset(50%)",
    height: 1,
    overflow: "hidden",
    position: "absolute",
    bottom: 0,
    left: 0,
    whiteSpace: "nowrap",
    width: 1,
  });

  const header = (
    <div className="flex flex-wrap align-items-center justify-content-between gap-2">
      <Typography variant="h2" component="h1">
        Requests Scheduler
      </Typography>

      <div className="flex">
        <AccessButton
          sx={buttonStyle}
          raised
          onClick={createJob}
          startIcon={<FAIcon icon="pencil" />}
          {...GenerateTourProps(createJobTourStep)}
          config={config}
          permission="OPERATOR"
        >
          Create Job
        </AccessButton>

        <AccessButton
          component="label"
          role={undefined}
          variant="contained"
          tabIndex={-1}
          startIcon={<FAIcon icon="upload" />}
          sx={buttonStyle}
          {...GenerateTourProps(importJobTourStep)}
        >
          Import Jobs
          <VisuallyHiddenInput
            type="file"
            accept=".json,application/json"
            onChange={customJobImporter}
          />
        </AccessButton>

        <AccessButton
          sx={buttonStyle}
          raised
          onClick={() =>
            ExportJobs().catch((error) =>
              showSnackbar({
                severity: "error",
                summary: "Error",
                detail: `Error exporting jobs: ${error}`,
                life: 3000,
              }),
            )
          }
          startIcon={<FAIcon icon="file-export" />}
          {...GenerateTourProps(exportJobTourStep)}
          config={config}
          permission="OPERATOR"
        >
          Export Jobs
        </AccessButton>
      </div>
    </div>
  );

  return (
    <div>
      <EnhancedTable
        data={jobs}
        columns={[
          {
            id: "action",
            label: "Action",
            template: actionTemplate,
          },
          {
            id: "name",
            field: "name",
            label: "Name",
            sortable: true,
            filterable: true,
            isString: true,
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
            id: "system",
            field: "request_template.system",
            label: "System",
            sortable: true,
            filterable: true,
            isString: true,
          },
          {
            id: "instance",
            field: "request_template.instance_name",
            label: "Instance",
            sortable: true,
            filterable: true,
            isString: true,
          },
          {
            id: "command",
            field: "request_template.command",
            label: "Command",
            sortable: true,
            filterable: true,
            isString: true,
          },
          {
            id: "next_run_time",
            field: "next_run_time",
            label: "Next Run Time",
            sortable: true,
            filterable: true,
            isDate: true,
          },
          {
            id: "success_count",
            field: "success_count",
            label: "Success Count",
            sortable: true,
            filterable: true,
            isNumeric: true,
          },
          {
            id: "error_count",
            field: "error_count",
            label: "Error Count",
            sortable: true,
            filterable: true,
            isNumeric: true,
          },
          {
            id: "canceled_count",
            field: "canceled_count",
            label: "Canceled Count",
            sortable: true,
            filterable: true,
            isNumeric: true,
          },
          {
            id: "skip_count",
            field: "skip_count",
            label: "Skip Count",
            sortable: true,
            filterable: true,
            isNumeric: true,
          },
        ]}
        header={header}
        defaultOrderBy="name"
        defaultOrder="desc"
      />
    </div>
  );
}

export default JobIndex;
