import { Garden, Patch } from "../models/brewtils-types";
import { Config } from "../models/models";
import { GetAuthHeaders } from "./token_service";
import { GetBaseURL } from "./util_service";

export const GetGarden = async (
  garden_name: string,
  headerData?: any,
): Promise<Garden> => {
  try {
    const headers = GetAuthHeaders();
    if (headerData) {
      for (const [key, value] of Object.entries(headerData)) {
        headers.append(key, value as string);
      }
    }

    const response = await fetch(
      `${GetBaseURL()}/api/v1/gardens/${encodeURIComponent(garden_name)}`,
      {
        headers: headers,
      },
    );
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }
    const data = (await response.json()) as Garden;
    return data;
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching Requests:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};

export const PatchGarden = async (
  patch: Patch,
  garden_name?: string,
  headerData?: any,
): Promise<any> => {
  try {
    const headers = GetAuthHeaders();
    headers.append("Content-Type", "application/json");
    if (headerData) {
      for (const [key, value] of Object.entries(headerData)) {
        headers.append(key, value as string);
      }
    }

    const response = await fetch(
      `${GetBaseURL()}/api/v1/gardens${garden_name ? "/" + encodeURIComponent(garden_name) : ""}`,
      {
        headers: headers,
        body: JSON.stringify(patch),
        method: "PATCH",
      },
    );
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching Requests:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};

export const DeleteGarden = async (
  garden_name: string,
  headerData?: any,
): Promise<any> => {
  try {
    const headers = GetAuthHeaders();
    if (headerData) {
      for (const [key, value] of Object.entries(headerData)) {
        headers.append(key, value as string);
      }
    }

    const response = await fetch(
      `${GetBaseURL()}/api/v1/gardens/${encodeURIComponent(garden_name)}`,
      {
        headers: headers,
        method: "DELETE",
      },
    );
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching Requests:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};

export const GetRootGarden = async (
  config: Config,
  headerData?: any,
): Promise<Garden> => {
  if (config?.garden_name) {
    return GetGarden(config.garden_name, headerData);
  }
  throw new Error("Root garden not defined in config");
};

export const GetGardenList = async (
  headerData?: any,
): Promise<Array<Garden>> => {
  try {
    const headers = GetAuthHeaders();
    if (headerData) {
      for (const [key, value] of Object.entries(headerData)) {
        headers.append(key, value as string);
      }
    }

    const response = await fetch(`${GetBaseURL()}/api/v1/gardens/`, {
      headers: headers,
    });
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }
    const data = (await response.json()) as Array<Garden>;
    return data;
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching Requests:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};

export const SyncGarden = async (garden_name?: string): Promise<Garden> => {
  return PatchGarden(
    { operation: "sync", path: "", value: "" },
    garden_name,
    garden_name && encodeURI(garden_name) == garden_name
      ? { "Target-Garden": garden_name }
      : undefined,
  );
};

export const RescanGarden = async (garden_name?: string): Promise<Garden> => {
  return PatchGarden(
    { operation: "rescan", path: "", value: "" },
    garden_name,
    garden_name && encodeURI(garden_name) == garden_name
      ? { "Target-Garden": garden_name }
      : undefined,
  );
};

export const SyncUsersGarden = async (garden_name: string): Promise<Garden> => {
  return PatchGarden(
    { operation: "sync_users", path: "", value: "" },
    garden_name,
    encodeURI(garden_name) == garden_name
      ? { "Target-Garden": garden_name }
      : undefined,
  );
};

export const UpdateApiGarden = async (
  garden_name: string,
  status: string,
  api: string,
  type: string,
): Promise<Garden> => {
  return PatchGarden(
    {
      operation: "connection",
      path: "",
      value: {
        status: status,
        api: api,
        connection_type: type,
      },
    },
    garden_name,
  );
};
