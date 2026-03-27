import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "primereact/button";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { Dialog } from "primereact/dialog";
import { useEffect, useState } from "react";

import SchedulerViewCard from "../components/SchedulerViewCard";
import { Job } from "../models/brewtils-types";
import {
  DeleteJob,
  GetJobList,
  PauseJob,
  ResumeJob,
} from "../services/job_service";
import { GetBaseURL } from "../services/util_service";

function JobIndex({ listeners }: { listeners: Record<string, any> }) {
  const [jobs, setJobs] = useState<Array<Job>>([]);
  const [selectedJob, setSelectedJob] = useState<Job | undefined>(undefined);

  useEffect(() => {
    const MonitorJobs = (message: any) => {
      if (message.payload_type === "Job") {
        let updateList = false;
        const updatedJobs = [] as Array<Job>;

        for (const job of jobs) {
          if (message.payload.id === job.id) {
            updateList = true;
            updatedJobs.push(message.payload);
          } else {
            updatedJobs.push(job);
          }
        }

        if (updateList) {
          setJobs(updatedJobs);
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
        console.error("Error fetching jobs:", error);
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

  const nameTemplate = (job: Job) => {
    return (
      <div>
        <Button
          rounded
          raised
          link
          onClick={() => setSelectedJob(job)}
          title={"View Job " + job.name}
          className="mr-2"
        >
          <FontAwesomeIcon icon="arrow-up-right-from-square" />
        </Button>
        <Button
          rounded
          raised
          link
          onClick={() => window.open(`${GetBaseURL()}/job/${job.id}`, "_self")}
          title={"Update Job " + job.name}
          className="mr-2"
        >
          <FontAwesomeIcon icon="edit" />
        </Button>
        {job.status === "RUNNING" && (
          <Button
            rounded
            raised
            link
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
                  console.error("Error pausing job:", error);
                });
            }}
            title={"Pause Job " + job.name}
            className="mr-2"
          >
            <FontAwesomeIcon icon="pause" />
          </Button>
        )}
        {job.status === "PAUSED" && (
          <Button
            rounded
            raised
            link
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
                  console.error("Error resuming job:", error);
                });
            }}
            title={"Resume Job " + job.name}
            className="mr-2"
          >
            <FontAwesomeIcon icon="play" />
          </Button>
        )}
        <Button
          rounded
          raised
          link
          onClick={() => {
            DeleteJob(job)
              .then(() => {
                setJobs((prevJobs) => prevJobs.filter((j) => j.id !== job.id));
              })
              .catch((error) => {
                console.error("Error deleting job:", error);
              });
          }}
          title={"Delete Job " + job.name}
          className="mr-2"
        >
          <FontAwesomeIcon icon="trash" />
        </Button>
        {job.name}
      </div>
    );
  };

  const createJob = () => {
    window.open(`${GetBaseURL()}/create/job`, "_self");
  };

  const header = (
    <div className="flex flex-wrap align-items-center justify-content-between gap-2">
      <span className="text-xl text-900 font-bold">Requests Scheduler</span>
      <div>
        <Button rounded raised onClick={createJob}>
          Create Job
        </Button>
        <Button rounded raised onClick={createJob}>
          Import Jobs
        </Button>
        <Button rounded raised onClick={createJob}>
          Export Jobs
        </Button>
      </div>
    </div>
  );

  return (
    <div>
      <Dialog
        visible={selectedJob !== undefined}
        style={{ width: "50vw" }}
        onHide={() => {
          if (!selectedJob) return;
          setSelectedJob(undefined);
        }}
      >
        {selectedJob && selectedJob.id && (
          <SchedulerViewCard jobId={selectedJob.id} listeners={listeners} />
        )}
      </Dialog>
      <DataTable
        value={jobs}
        header={header}
        paginator
        rows={5}
        rowsPerPageOptions={[5, 10, 25, 50]}
        tableStyle={{ minWidth: "50rem" }}
      >
        <Column field="name" header="Name" body={nameTemplate}></Column>
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
