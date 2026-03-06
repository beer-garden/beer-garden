import { compare, validate } from "compare-versions";

import { Garden, System } from "../models/brewtils-types";
import { GetBaseURL } from "./util_service";

export const GetSystem = async (
  systemId: string,
  headerData: any,
): Promise<System> => {
  try {
    const headers = new Headers();
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
    const headers = new Headers();
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

export const DetermineLatestSystemVersion = (
  systems: System[],
  systemName: string | null,
  systemNameSpace: string | null,
  systemVersion: string | null,
): System => {
  return systems
    .filter((system) => {
      return (
        (system.namespace === systemNameSpace || systemNameSpace === null) &&
        (system.name === systemName || systemName === null) &&
        (system.version === systemVersion ||
          systemVersion === null ||
          systemVersion === "latest")
      );
    })
    .reduce((latestSystem, currentSystem) => {
      if (currentSystem.version && latestSystem.version) {
        const currentValid = validate(currentSystem.version)
          ? currentSystem.version
          : validate(currentSystem.version.replace(".dev", "-dev"))
            ? currentSystem.version.replace(".dev", "-dev")
            : null;
        const latestValid = validate(latestSystem.version)
          ? latestSystem.version
          : validate(latestSystem.version.replace(".dev", "-dev"))
            ? latestSystem.version.replace(".dev", "-dev")
            : null;

        if (currentValid === null && latestValid === null) {
          if (currentSystem.version.localeCompare(latestSystem.version) > 0) {
            return currentSystem;
          } else {
            return latestSystem;
          }
        }

        if (currentValid === null) {
          return latestSystem;
        }

        if (latestValid === null) {
          return currentSystem;
        }

        return compare(currentValid, latestValid, ">")
          ? currentSystem
          : latestSystem;
      }
      return latestSystem;
    });
};
