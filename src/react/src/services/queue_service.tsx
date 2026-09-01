import { Queue } from "../models/brewtils-types";
import { GetAuthHeaders } from "./token_service";
import { GetBaseURL } from "./util_service";

export const ClearAllQueues = async (gardenName?: string): Promise<void> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  let fetch_url = `${GetBaseURL()}/api/v1/queues`;
  if (gardenName) {
    fetch_url = `${GetBaseURL()}/api/v1/queues?garden_name=${encodeURIComponent(gardenName)}`;
    if (encodeURIComponent(gardenName) === gardenName) {
      headers.append("Target-Garden", gardenName);
    }
  }
  const response = await fetch(fetch_url, {
    headers: headers,
    method: "DELETE",
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
};

export const ClearQueue = async (queueName: string): Promise<void> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  const response = await fetch(`${GetBaseURL()}/api/v1/queues/${queueName}`, {
    headers: headers,
    method: "DELETE",
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
};

export const GetInstanceQueues = async (
  instanceId: string | undefined,
): Promise<Queue[]> => {
  if (!instanceId) {
    return [] as Queue[];
  }
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  const response = await fetch(
    `${GetBaseURL()}/api/v1/instances/${instanceId}/queues`,
    {
      headers: headers,
      method: "GET",
    },
  );
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
  const data = (await response.json()) as Queue[];
  return data;
};
