import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "primereact/button";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Job } from "../models/brewtils-types";
import { GetJobList } from "../services/job_service";
import { GetBaseURL } from "../services/util_service";

function JobIndex() {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<Array<Job>>([]);

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
          onClick={() => navigate(`${GetBaseURL()}/job/${job.id}`)}
          title={"Update Job " + job.name}
        >
          <FontAwesomeIcon icon="arrow-up-right-from-square" />
        </Button>
        {job.name}
      </div>
    );
  };

  const createJob = () => {
    navigate(`${GetBaseURL()}/create/job`);
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
