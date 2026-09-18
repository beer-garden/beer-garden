import { compare, validate } from "compare-versions";

import { Garden, System } from "../models/brewtils-types";
import { GetAuthHeaders } from "./token_service";
import { GetBaseURL } from "./util_service";

export const ClearSystemsCache = (): void => {
  sessionStorage.removeItem("systems");
};

export const GetSystem = async (
  systemId: string,
  headerData: any,
): Promise<System> => {
  try {
    const headers = GetAuthHeaders();
    for (const [key, value] of Object.entries(headerData)) {
      headers.append(key, value as string);
    }

    const response = await fetch(`${GetBaseURL()}/api/v1/systems/${systemId}`, {
      headers: headers,
    });
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }
    const data = (await response.json()) as System;

    return data;
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching System:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};

export const GetSystemList = async (
  queryData?: any,
  headerData?: any,
): Promise<System[]> => {
  if (
    (queryData === null || queryData === undefined) &&
    (headerData === null || headerData === undefined)
  ) {
    const storedValue = sessionStorage.getItem("systems");

    if (storedValue !== null) {
      return JSON.parse(storedValue) as Array<System>;
    }
  }
  try {
    const headers = GetAuthHeaders();
    if (headerData) {
      for (const [key, value] of Object.entries(headerData)) {
        headers.append(key, value as string);
      }
    }
    let queryString = "";
    if (queryData) {
      // queryString = new URLSearchParams(headerData).toString();
      const searchParams = new URLSearchParams();
      for (const [key, value] of Object.entries(queryData)) {
        if (Array.isArray(value)) {
          for (const item of value) {
            searchParams.append(key, item as string);
          }
        } else {
          searchParams.append(key, value as string);
        }
      }

      queryString = searchParams.toString();
    }

    const response = await fetch(
      `${GetBaseURL()}/api/v1/systems?${queryString}`,
      {
        headers: headers,
      },
    );
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }
    const data = (await response.json()) as System[];
    if (
      (queryData === null || queryData === undefined) &&
      (headerData === null || headerData === undefined)
    ) {
      sessionStorage.setItem("systems", JSON.stringify(data));
    }
    return data;
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching Systems:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};

export const ExtractSystemsFromGardens = (
  gardens: Array<Garden>,
  systems: System[],
): System[] => {
  gardens.forEach((garden: Garden) => {
    if (garden.systems) {
      garden.systems.forEach((system: System) => {
        systems.push(system);
      });
    }
  });

  return systems;
};

export const ReloadSystem = async (system: System): Promise<void> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  if (
    system.garden_name !== undefined &&
    encodeURIComponent(system.garden_name) === system.garden_name
  ) {
    headers.append("Target-Garden", system.garden_name);
  }
  const response = await fetch(`${GetBaseURL()}/api/v1/systems/${system.id}`, {
    headers: headers,
    method: "PATCH",
    body: JSON.stringify({
      operations: [
        {
          operation: "reload",
        },
      ],
    }),
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
};

export const Rescan = async (gardenName?: string): Promise<void> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  let fetch_url = `${GetBaseURL()}api/v1/systems`;
  if (gardenName) {
    fetch_url = `${GetBaseURL()}/api/v1/systems?garden_name=${encodeURIComponent(gardenName)}`;
    if (encodeURIComponent(gardenName) === gardenName) {
      headers.append("Target-Garden", gardenName);
    }
  }
  const response = await fetch(fetch_url, {
    headers: headers,
    method: "PATCH",
    body: JSON.stringify({
      operations: [
        {
          operation: "rescan",
        },
      ],
    }),
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
};

export const DeleteSystem = async (system: System): Promise<void> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  if (
    system.garden_name !== undefined &&
    encodeURIComponent(system.garden_name) === system.garden_name
  ) {
    headers.append("Target-Garden", system.garden_name);
  }
  const response = await fetch(`${GetBaseURL()}/api/v1/systems/${system.id}`, {
    headers: headers,
    method: "DELETE",
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
};

export const ForceDeleteSystem = async (system: System): Promise<void> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  if (
    system.garden_name !== undefined &&
    encodeURIComponent(system.garden_name) === system.garden_name
  ) {
    headers.append("Target-Garden", system.garden_name);
  }
  const params = new URLSearchParams({ force: "true" }).toString();
  const response = await fetch(
    `${GetBaseURL()}/api/v1/systems/${system.id}?${params}`,
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

export const DetermineLatestSystemVersion = (
  systems: System[],
  systemName: string | undefined,
  systemNameSpace: string | undefined,
  systemVersion: string | undefined,
): System => {
  return systems
    .filter((system) => {
      return (
        (system.namespace === systemNameSpace ||
          systemNameSpace === undefined) &&
        (system.name === systemName || systemName === undefined) &&
        (system.version === systemVersion ||
          systemVersion === undefined ||
          systemVersion === "latest")
      );
    })
    .reduce((latestSystem, currentSystem) => {
      if (currentSystem.version && latestSystem.version) {
        const currentValid = validate(currentSystem.version)
          ? currentSystem.version
          : validate(currentSystem.version.replace(".dev", "-dev"))
            ? currentSystem.version.replace(".dev", "-dev")
            : undefined;
        const latestValid = validate(latestSystem.version)
          ? latestSystem.version
          : validate(latestSystem.version.replace(".dev", "-dev"))
            ? latestSystem.version.replace(".dev", "-dev")
            : undefined;

        if (currentValid === undefined && latestValid === undefined) {
          if (currentSystem.version.localeCompare(latestSystem.version) > 0) {
            return currentSystem;
          } else {
            return latestSystem;
          }
        }

        if (currentValid === undefined) {
          return latestSystem;
        }

        if (latestValid === undefined) {
          return currentSystem;
        }

        return compare(currentValid, latestValid, ">")
          ? currentSystem
          : latestSystem;
      }
      return latestSystem;
    });
};

export const CompareVersions = (versionA: string, versionB: string): number => {
  const validVersionA = validate(versionA)
    ? versionA
    : validate(versionA.replace(".dev", "-dev"))
      ? versionA.replace(".dev", "-dev")
      : undefined;
  const validVersionB = validate(versionB)
    ? versionB
    : validate(versionB.replace(".dev", "-dev"))
      ? versionB.replace(".dev", "-dev")
      : undefined;

  if (validVersionA === undefined && validVersionB === undefined) {
    if (versionA.localeCompare(versionB) > 0) {
      return 1;
    } else {
      return -1;
    }
  }

  if (validVersionA === undefined) {
    return -1;
  }

  if (validVersionB === undefined) {
    return 1;
  }

  return compare(validVersionA, validVersionB, ">") ? 1 : -1;
};
