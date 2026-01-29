import { Job } from "../models/brewtils-types";
import { useState, useEffect } from "react";
import { GetJobList } from "../services/job_service";
import { DataTable } from "primereact/datatable";
import { Column } from "primereact/column";
import { Button } from "primereact/button";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

function JobIndex() {
  const [jobs, setJobs] = useState<Array<Job>>([]);

  useEffect(() => {
    GetJobList().then((data: [Array<Job>, Headers]) => {
      const [responseJobs, ] = data;
      setJobs(responseJobs);
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
          onClick={() => window.open("/job/" + job.id, "_self")}
          title={"Update Job " + job.name}
        >
          <FontAwesomeIcon icon="arrow-up-right-from-square" />
        </Button>
        {job.name}
      </div>
    );
  };

  const createJob = () => {
    window.open("/create/job", "_self");
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
