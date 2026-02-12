import { Instance, System } from "../models/brewtils-types";

export const StartInstance = async (
  instance: Instance,
  system: System,
): Promise<void> => {
  try {
    const headers = new Headers();
    headers.append("Content-Type", "application/json");
    if (system.garden_name) {
      headers.append("Target-Garden", system.garden_name);
    }
    const response = await fetch("api/v1/instances/" + instance.id, {
      headers: headers,
      method: "PATCH",
      body: JSON.stringify({
        operations: [
          {
            operation: "start",
          },
        ],
      }),
    });
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }
  } catch (error) {
    // Handle network errors or the error thrown above
    throw error; // Re-throw to be handled by the component/hook
  }
};

export const StopInstance = async (
  instance: Instance,
  system: System,
): Promise<void> => {
  try {
    const headers = new Headers();
    headers.append("Content-Type", "application/json");
    if (system.garden_name) {
      headers.append("Target-Garden", system.garden_name);
    }
    const response = await fetch("api/v1/instances/" + instance.id, {
      headers: headers,
      method: "PATCH",
      body: JSON.stringify({
        operations: [
          {
            operation: "stop",
          },
        ],
      }),
    });
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }
  } catch (error) {
    // Handle network errors or the error thrown above
    throw error; // Re-throw to be handled by the component/hook
  }
};
