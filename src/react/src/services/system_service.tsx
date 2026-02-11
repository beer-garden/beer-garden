import { Garden, System } from "../models/brewtils-types";

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

    const response = await fetch(`/api/v1/systems?${queryString}`, {
      headers: headers,
    });
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

export const Rescan = async (gardenName?: string): Promise<void> => {
  try {
    const headers = new Headers();
    headers.append("Content-Type", "application/json");
    let fetch_url = "api/v1/systems";
    if (gardenName) {
      headers.append("Target-Garden", gardenName);
      fetch_url =
        "api/v1/systems?garden_name=" + encodeURIComponent(gardenName);
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
    console.log(response);
    // const data = (await response.json()) as Request;
    // return data;
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching Systems:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};
