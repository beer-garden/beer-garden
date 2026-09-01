import { Job, Operation } from "../models/brewtils-types";
import { GetAuthHeaders } from "./token_service";
import { GetBaseURL } from "./util_service";

export const GetJobList = async (
  headerData?: any,
): Promise<[Job[], Headers]> => {
  try {
    const headers = GetAuthHeaders();
    if (headerData) {
      for (const [key, value] of Object.entries(headerData)) {
        headers.append(key, value as string);
      }
    }

    const response = await fetch(`${GetBaseURL()}/api/v1/jobs`, {
      headers: headers,
    });
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }
    const data = (await response.json()) as Job[];
    const responseHeaders = response.headers;
    return [data, responseHeaders];
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching Requests:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};

export const GetJob = async (jobId: string, headerData: any): Promise<Job> => {
  try {
    const headers = GetAuthHeaders();
    for (const [key, value] of Object.entries(headerData)) {
      headers.append(key, value as string);
    }

    const response = await fetch(`${GetBaseURL()}/api/v1/jobs/${jobId}`, {
      headers: headers,
    });
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }
    const data = (await response.json()) as Job;

    return data;
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching Requests:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};

export const RunAdhocJob = async (
  jobId: string,
  headerData?: any,
): Promise<void> => {
  try {
    const headers = GetAuthHeaders();

    for (const [key, value] of Object.entries(headerData || {})) {
      headers.append(key, value as string);
    }

    const response = await fetch(
      `${GetBaseURL()}/api/v1/jobs/${jobId}/execute`,
      {
        headers: headers,
        method: "POST",
      },
    );
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }
    return;
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching Requests:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};

export const CreateJob = async (job: Job, headerData?: any): Promise<Job> => {
  try {
    const headers = GetAuthHeaders();

    for (const [key, value] of Object.entries(headerData || {})) {
      headers.append(key, value as string);
    }

    headers.append("Content-Type", "application/json");

    const response = await fetch(`${GetBaseURL()}/api/v1/jobs/`, {
      headers: headers,
      method: "POST",
      body: JSON.stringify(job),
    });
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }
    const data = (await response.json()) as Job;

    return data;
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching Requests:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};

export const UpdateJob = async (job: Job, headerData?: any): Promise<Job> => {
  return PatchJob(
    job,
    {
      operation: "update",
      path: "/job",
      value: job,
    } as Operation,
    headerData,
  );
};

export const PauseJob = async (job: Job, headerData?: any): Promise<Job> => {
  return PatchJob(
    job,
    {
      operation: "update",
      path: "/status",
      value: "PAUSED",
    } as Operation,
    headerData,
  );
};

export const ResumeJob = async (job: Job, headerData?: any): Promise<Job> => {
  return PatchJob(
    job,
    {
      operation: "update",
      path: "/status",
      value: "RUNNING",
    } as Operation,
    headerData,
  );
};

export const PatchJob = async (
  job: Job,
  operation: Operation,
  headerData?: any,
): Promise<Job> => {
  try {
    const headers = GetAuthHeaders();

    for (const [key, value] of Object.entries(headerData || {})) {
      headers.append(key, value as string);
    }

    headers.append("Content-Type", "application/json");

    const response = await fetch(`${GetBaseURL()}/api/v1/jobs/${job.id}`, {
      headers: headers,
      method: "PATCH",
      body: JSON.stringify({
        operations: [operation],
      }),
    });
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }
    const data = (await response.json()) as Job;

    return data;
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching Requests:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};

export const DeleteJob = async (job: Job, headerData?: any) => {
  try {
    const headers = GetAuthHeaders();

    for (const [key, value] of Object.entries(headerData || {})) {
      headers.append(key, value as string);
    }

    const response = await fetch(`${GetBaseURL()}/api/v1/jobs/${job.id}`, {
      headers: headers,
      method: "DELETE",
    });
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }

    return;
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching Requests:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};

export const ImportJobs = async (
  jobs: Job[],
  headerData?: any,
): Promise<void> => {
  try {
    const headers = GetAuthHeaders();

    for (const [key, value] of Object.entries(headerData || {})) {
      headers.append(key, value as string);
    }
    headers.append("Content-Type", "application/json");

    const response = await fetch(`${GetBaseURL()}/api/v1/import/jobs/`, {
      headers: headers,
      method: "POST",
      body: JSON.stringify(jobs),
    });
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }

    return;
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error importing Jobs:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};

export const ExportJobs = async (headerData?: any): Promise<Blob> => {
  try {
    const headers = GetAuthHeaders();

    for (const [key, value] of Object.entries(headerData || {})) {
      headers.append(key, value as string);
    }

    const response = await fetch(`${GetBaseURL()}/api/v1/export/jobs/`, {
      headers: headers,
      method: "POST",
    });

    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }
    const blob = await response.blob();

    const url = window.URL.createObjectURL(blob);
    const sanitizedTimestamp = new Date()
      .toISOString()
      .split(".")[0]
      .replace(/:/g, "-");
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `JobExport_${sanitizedTimestamp}.json`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);

    return blob;
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching Jobs:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};
