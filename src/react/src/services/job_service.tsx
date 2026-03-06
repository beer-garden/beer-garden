import { Job } from "../models/brewtils-types";
import { GetBaseURL } from "./util_service";

export const GetJobList = async (
  headerData?: any,
): Promise<[Job[], Headers]> => {
  try {
    const headers = new Headers();
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
    const headers = new Headers();
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

export const CreateJob = async (
  job: Job,
  headerData?: any,
): Promise<Request> => {
  try {
    const headers = new Headers();

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
    const data = (await response.json()) as Request;

    return data;
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching Requests:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};

export const UpdateJob = async (
  job: Job,
  headerData?: any,
): Promise<Request> => {
  try {
    const headers = new Headers();

    for (const [key, value] of Object.entries(headerData || {})) {
      headers.append(key, value as string);
    }

    headers.append("Content-Type", "application/json");

    const response = await fetch(`${GetBaseURL()}/api/v1/jobs/${job.id}`, {
      headers: headers,
      method: "PATCH",
      body: JSON.stringify({
        operations: [
          {
            operation: "update",
            path: "/job",
            value: job,
          },
        ],
      }),
    });
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }
    const data = (await response.json()) as Request;

    return data;
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching Requests:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};
