import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Column } from "primereact/column";
import { confirmDialog } from "primereact/confirmdialog";
import { DataTable } from "primereact/datatable";
import { FileUpload } from "primereact/fileupload";
import { RefObject, useEffect, useRef, useState } from "react";

import AccessButton from "../components/AccessButton";
import { Job } from "../models/brewtils-types";
import { Config, RequestItem, TourStepProps } from "../models/models";
import { useToast } from "../providers/ToastProvider";
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
import { PaginatorTemplate } from "../services/util_service";

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
  const showToast = useToast();
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

  useEffect(() => {
    ClearTourSteps(tourStepsRef, tourPrefix, tourUuid);
    AddTourStep(tourStepsRef, createJobTourStep);
    AddTourStep(tourStepsRef, importJobTourStep);
    AddTourStep(tourStepsRef, exportJobTourStep);

    if (jobs.length > 0) {
      AddTourStep(tourStepsRef, runNowTourStep);
      AddTourStep(tourStepsRef, viewJobTourStep);
      AddTourStep(tourStepsRef, editJobTourStep);
      AddTourStep(tourStepsRef, pauseResumeJobTourStep);
      AddTourStep(tourStepsRef, deleteJobTourStep);
    }

    return () => {
      ClearTourSteps(tourStepsRef, tourPrefix, tourUuid);
    };
  }, [jobs]);
  const jobImportFileRef = useRef<FileUpload | null>(null);

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
        showToast({
          severity: "error",
          summary: "Error",
          detail: `Error fetching jobs: ${error}`,
          life: 3000,
        });
      });
  }, []);

  const runTimeTemplate = (job: Job) => {
    if (
      job?.next_run_time &&
      (typeof job.next_run_time === "string" ||
        typeof job.next_run_time === "number")
    ) {
      return new Date(job.next_run_time).toLocaleString();
    }
    return job.next_run_time;
  };

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
          link
          basic
          onClick={() => addRequestItem({ jobId: job.id, type: "VIEW_JOB" })}
          title={"View Job " + job.name}
          className="mr-2"
          {...GenerateTourProps(viewJobTourStep)}
        >
          <FontAwesomeIcon icon="arrow-up-right-from-square" />
        </AccessButton>
        <>
          <AccessButton
            rounded
            raised
            link
            basic
            onClick={() => {
              if (job.id) {
                RunAdhocJob(job.id).catch((error) => {
                  showToast({
                    severity: "error",
                    summary: "Error",
                    detail: `Error running job: ${error}`,
                    life: 3000,
                  });
                });
              }
            }}
            title={"Run Now " + job.name}
            className="mr-2"
            {...GenerateTourProps(runNowTourStep)}
            {...permissions}
            permission="OPERATOR"
          >
            <FontAwesomeIcon icon="forward" />
          </AccessButton>

          <AccessButton
            rounded
            raised
            link
            basic
            onClick={() => {
              if (job.id) {
                editJob(job.id);
              }
            }}
            title={"Update Job " + job.name}
            className="mr-2"
            {...GenerateTourProps(editJobTourStep)}
            {...permissions}
            permission="OPERATOR"
          >
            <FontAwesomeIcon icon="edit" />
          </AccessButton>
          {job.status === "RUNNING" && (
            <AccessButton
              rounded
              raised
              link
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
                    showToast({
                      severity: "error",
                      summary: "Error",
                      detail: `Error pausing job: ${error}`,
                      life: 3000,
                    });
                  });
              }}
              title={"Pause Job " + job.name}
              className="mr-2"
              {...GenerateTourProps(pauseResumeJobTourStep)}
              {...permissions}
              permission="OPERATOR"
            >
              <FontAwesomeIcon icon="pause" />
            </AccessButton>
          )}
          {job.status === "PAUSED" && (
            <AccessButton
              rounded
              raised
              link
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
                    showToast({
                      severity: "error",
                      summary: "Error",
                      detail: `Error resuming job: ${error}`,
                      life: 3000,
                    });
                  });
              }}
              title={"Resume Job " + job.name}
              className="mr-2"
              {...GenerateTourProps(pauseResumeJobTourStep)}
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
                    showToast({
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
            className="mr-2"
            {...GenerateTourProps(deleteJobTourStep)}
            {...permissions}
            permission="OPERATOR"
          >
            <FontAwesomeIcon icon="trash" />
          </AccessButton>
        </>
      </div>
    );
  };

  const createJob = () => {
    addRequestItem({ type: "REQUEST", showSchedule: true });
  };

  const customJobImporter = (event: any) => {
    const file = event?.files?.[0];

    if (!file) {
      showToast({
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
          showToast({
            severity: "success",
            summary: "Success",
            detail: "Jobs imported successfully",
            life: 3000,
          });

          if (jobImportFileRef.current) {
            jobImportFileRef.current.clear();
          }

          // Refresh the job list after successful import
          GetJobList()
            .then((data: [Array<Job>, Headers]) => {
              const [responseJobs] = data;
              setJobs(responseJobs);
            })
            .catch((error) => {
              showToast({
                severity: "error",
                summary: "Error",
                detail: `Error fetching jobs: ${error}`,
                life: 3000,
              });
            });
        } catch (error) {
          if (error instanceof Error) {
            showToast({
              severity: "error",
              summary: "Error",
              detail: `Failed to import jobs: ${error}`,
              life: 3000,
            });
          } else {
            console.error("Error importing jobs:", error);
            showToast({
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

  const header = (
    <div className="flex flex-wrap align-items-center justify-content-between gap-2">
      <h1 className="text-xl text-900 font-bold">Requests Scheduler</h1>

      <div className="flex">
        <AccessButton
          className="mr-2"
          raised
          onClick={createJob}
          {...GenerateTourProps(createJobTourStep)}
          config={config}
          permission="OPERATOR"
          label="Create Job"
        />

        <FileUpload
          ref={jobImportFileRef}
          className="mr-2"
          mode="basic"
          name="file"
          accept=".json"
          maxFileSize={1000000}
          chooseLabel="Import Jobs"
          customUpload
          auto
          uploadHandler={customJobImporter}
          {...GenerateTourProps(importJobTourStep)}
          pt={{
            uploadIcon: { role: "img", "aria-label": "Upload Job File" },
            cancelIcon: { role: "img", "aria-label": "Remove Upload Job File" },
            chooseIcon: { role: "img", "aria-label": "Choose Upload Job File" },
            basicButton: { role: "button" },
          }}
        />

        <AccessButton
          className="mr-2"
          raised
          onClick={() =>
            ExportJobs().catch((error) =>
              showToast({
                severity: "error",
                summary: "Error",
                detail: `Error exporting jobs: ${error}`,
                life: 3000,
              }),
            )
          }
          {...GenerateTourProps(exportJobTourStep)}
          config={config}
          permission="OPERATOR"
          label="Export Jobs"
        />
      </div>
    </div>
  );

  return (
    <div>
      <DataTable
        value={jobs}
        header={header}
        paginator
        rows={5}
        rowsPerPageOptions={[5, 10, 25, 50]}
        paginatorTemplate={PaginatorTemplate}
        tableStyle={{ minWidth: "50rem" }}
      >
        <Column field="name" header="Actions" body={actionTemplate}></Column>
        <Column field="name" header="Name"></Column>
        <Column field="status" header="Status"></Column>
        <Column field="request_template.system" header="System"></Column>
        <Column
          field="request_template.instance_name"
          header="Instance"
        ></Column>
        <Column field="request_template.command" header="Command"></Column>
        <Column
          field="next_run_time"
          header="Next Run Time"
          body={runTimeTemplate}
        ></Column>
        <Column field="success_count" header="Success Count"></Column>
        <Column field="error_count" header="Error Count"></Column>
        <Column field="canceled_count" header="Canceled Count"></Column>
        <Column field="skip_count" header="Skip Count"></Column>
      </DataTable>
    </div>
  );
}

export default JobIndex;
