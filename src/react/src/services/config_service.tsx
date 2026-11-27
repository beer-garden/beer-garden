import { Config } from "../models/models";
import { GetBaseURL } from "./util_service";

export const GetConfig = async (): Promise<Config> => {
  try {
    const response = await fetch(`${GetBaseURL()}/config`);
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }
    const data = (await response.json()) as Config;
    return data;
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching Config:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};
