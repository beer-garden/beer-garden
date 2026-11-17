import { Runner } from "../models/brewtils-types";
import { GetAuthHeaders } from "./token_service";
import { GetBaseURL } from "./util_service";

export const GetRunner = async (
  runnerId: string,
  headerData?: any,
): Promise<Runner> => {
  try {
    const headers = GetAuthHeaders();
    for (const [key, value] of Object.entries(headerData)) {
      headers.append(key, value as string);
    }

    const response = await fetch(
      `${GetBaseURL()}/api/vbeta/runners/${runnerId}`,
      {
        headers: headers,
      },
    );
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }
    const data = (await response.json()) as Runner;

    return data;
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching Runner:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};

export const GetRunnerList = async (
  headerData?: any,
): Promise<Array<Runner>> => {
  try {
    const headers = GetAuthHeaders();
    if (headerData) {
      for (const [key, value] of Object.entries(headerData)) {
        headers.append(key, value as string);
      }
    }

    const response = await fetch(`${GetBaseURL()}/api/vbeta/runners/`, {
      headers: headers,
    });
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }
    const data = (await response.json()) as Array<Runner>;

    return data;
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching Runner:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};

export const StartRunner = async (runner: Runner): Promise<void> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");

  const response = await fetch(
    `${GetBaseURL()}/api/vbeta/runners/${runner.id}`,
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

export const StopRunner = async (runner: Runner): Promise<void> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");

  const response = await fetch(
    `${GetBaseURL()}/api/vbeta/runners/${runner.id}`,
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

export const RemoveRunner = async (runner: Runner): Promise<void> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");

  const response = await fetch(
    `${GetBaseURL()}/api/vbeta/runners/${runner.id}`,
    {
      headers: headers,
      method: "DELETE",
    },
  );

  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
};

export const ReloadRunner = async (path: string): Promise<void> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");

  const response = await fetch(`${GetBaseURL()}/api/vbeta/runners/`, {
    headers: headers,
    method: "PATCH",
    body: JSON.stringify({
      operations: [
        {
          operation: "reload",
          path: path,
        },
      ],
    }),
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
};
