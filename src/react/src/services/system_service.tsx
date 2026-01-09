import { Garden, System } from "../models/brewtils-types";

export const GetSystemList = async (
  queryData?: any,
  headerData?: any,
): Promise<System[]> => {
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
      let searchParams = new URLSearchParams();
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
