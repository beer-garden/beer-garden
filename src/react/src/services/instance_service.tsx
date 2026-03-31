import { Instance, System } from "../models/brewtils-types";
import { GetAuthHeaders } from "./token_service";
import { GetBaseURL } from "./util_service";

export const StartInstance = async (
  instance: Instance,
  system: System,
): Promise<void> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  if (
    system.garden_name &&
    encodeURIComponent(system.garden_name) === system.garden_name
  ) {
    headers.append("Target-Garden", system.garden_name);
  }
  const response = await fetch(
    `${GetBaseURL()}/api/v1/instances/${instance.id}`,
    {
      headers: headers,
      method: "PATCH",
      body: JSON.stringify({
        operations: [
          {
            operation: "start",
          },
        ],
      }),
    },
  );
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
};

export const StopInstance = async (
  instance: Instance,
  system: System,
): Promise<void> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  if (
    system.garden_name &&
    encodeURIComponent(system.garden_name) === system.garden_name
  ) {
    headers.append("Target-Garden", system.garden_name);
  }
  const response = await fetch(
    `${GetBaseURL()}/api/v1/instances/${instance.id}`,
    {
      headers: headers,
      method: "PATCH",
      body: JSON.stringify({
        operations: [
          {
            operation: "stop",
          },
        ],
      }),
    },
  );
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
};

export const GetInstanceLogs = async (
  instance: Instance,
  timeout: number,
  startLine: number,
  endLine: number | null,
): Promise<[Instance, Headers]> => {
  try {
    const params = new URLSearchParams({
      start_line: startLine.toString(),
      timeout: timeout.toString(),
    });
    if (endLine != null) {
      params.append("end_line", endLine.toString());
    }

    const response = await fetch(
      `${GetBaseURL()}/api/v1/instances/${instance.id}/logs/?${params.toString()}`,
    );
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }
    const data = (await response.json()) as Instance;
    const responseHeaders = response.headers;

    return [data, responseHeaders];
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching Requests:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};
