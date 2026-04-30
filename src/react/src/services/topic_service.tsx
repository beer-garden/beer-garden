import { Subscriber, Topic } from "../models/brewtils-types";
import { GetAuthHeaders } from "./token_service";
import { GetBaseURL } from "./util_service";

export const GetTopic = async (id: string): Promise<Topic> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  const fetch_url = `${GetBaseURL()}/api/v1/topics/${id}`;
  const response = await fetch(fetch_url, {
    headers: headers,
    method: "GET",
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
  const data = (await response.json()) as Topic;
  return data;
};

export const GetTopicName = async (name: string): Promise<Topic> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  const fetch_url = `${GetBaseURL()}/api/v1/topics/name/${name}`;
  const response = await fetch(fetch_url, {
    headers: headers,
    method: "GET",
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
  const data = (await response.json()) as Topic;
  return data;
};

export const CreateTopic = async (newTopic: Topic): Promise<Topic> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  const response = await fetch(`${GetBaseURL()}/api/v1/topics/`, {
    headers: headers,
    method: "POST",
    body: JSON.stringify(newTopic),
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
  const data = (await response.json()) as Topic;
  return data;
};

export const DeleteTopic = async (topicId: string): Promise<void> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  const fetch_url = `${GetBaseURL()}/api/v1/topics/${topicId}`;
  const response = await fetch(fetch_url, {
    headers: headers,
    method: "DELETE",
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
};

export const AddSubscriber = async (
  topicId: string,
  subscriber: Subscriber,
): Promise<void> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  const fetch_url = `${GetBaseURL()}/api/v1/topics/${topicId}`;
  const response = await fetch(fetch_url, {
    headers: headers,
    method: "PATCH",
    body: JSON.stringify({
      operations: [
        {
          operation: "add",
          path: "",
          value: subscriber,
        },
      ],
    }),
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
};

export const RemoveSubscriber = async (
  topicId: string,
  subscriber: Subscriber,
): Promise<void> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  const fetch_url = `${GetBaseURL()}/api/v1/topics/${topicId}`;
  const response = await fetch(fetch_url, {
    headers: headers,
    method: "PATCH",
    body: JSON.stringify({
      operations: [
        {
          operation: "remove",
          path: "",
          value: subscriber,
        },
      ],
    }),
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
};

export const SyncTopics = async (): Promise<void> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  const fetch_url = `${GetBaseURL()}/api/v1/topics`;
  const response = await fetch(fetch_url, {
    headers: headers,
    method: "PATCH",
    body: JSON.stringify({
      operations: [
        {
          operation: "sync_all_topics",
        },
      ],
    }),
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
};

export const ResetCount = async (
  topicId: string | undefined,
  subscriber?: Subscriber,
) => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  const fetch_url = `${GetBaseURL()}/api/v1/topics/${topicId}`;
  const response = await fetch(fetch_url, {
    headers: headers,
    method: "PATCH",
    body: JSON.stringify({
      operations: [
        {
          operation: "reset_count",
          path: "",
          value: subscriber,
        },
      ],
    }),
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
  const data = (await response.json()) as Topic;
  return data;
};

export const GetTopics = async (queryData?: any): Promise<Topic[]> => {
  try {
    let queryString = "";
    const headers = GetAuthHeaders();
    const searchParams = new URLSearchParams();
    if (queryData) {
      for (const [key, value] of Object.entries(queryData)) {
        if (Array.isArray(value)) {
          for (const item of value) {
            if (typeof item == "object" && item !== null) {
              searchParams.append(key, JSON.stringify(item));
            } else {
              searchParams.append(key, item as string);
            }
          }
        } else {
          searchParams.append(key, value as string);
        }
      }

      queryString = searchParams.toString();
    }

    const response = await fetch(
      `${GetBaseURL()}/api/v1/topics?${queryString}`,
      {
        headers: headers,
        method: "GET",
      },
    );
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }
    const data = (await response.json()) as Topic[];
    return data;
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching Topics:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};
