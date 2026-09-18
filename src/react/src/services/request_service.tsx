import { v4 as uuidv4 } from "uuid";

import { Request } from "../models/brewtils-types";
import { RequestCommand } from "../models/models";
import { GetAuthHeaders } from "./token_service";
import { GetBaseURL } from "./util_service";

export const GetRequestList = async (
  headerData?: any,
): Promise<[Request[], Headers]> => {
  try {
    const headers = GetAuthHeaders();
    if (headerData) {
      for (const [key, value] of Object.entries(headerData)) {
        headers.append(key, value as string);
      }
    } else {
      headerData = {};
    }

    let queryString = "";

    if (headerData) {
      // queryString = new URLSearchParams(headerData).toString();
      const searchParams = new URLSearchParams();
      for (const [key, value] of Object.entries(headerData)) {
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
      `${GetBaseURL()}/api/v1/requests?${queryString}`,
      {
        headers: headers,
      },
    );
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }
    const data = (await response.json()) as Request[];
    const responseHeaders = response.headers;
    return [data, responseHeaders];
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching Requests:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};
export const GetRequest = async (
  requestId: string,
  headerData?: any,
  queryData?: any,
): Promise<Request> => {
  try {
    const headers = GetAuthHeaders();
    for (const [key, value] of Object.entries(headerData)) {
      headers.append(key, value as string);
    }

    let queryString = "";

    if (queryData) {
      const searchParams = new URLSearchParams();
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
      `${GetBaseURL()}/api/v1/requests/${requestId}?${queryString}`,
      {
        headers: headers,
      },
    );
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }
    const data = (await response.json()) as Request;

    return data;
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching Requests:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};

export const PostRequest = async (
  request: Request,
  headerData?: any,
  waitForCompletion?: boolean,
): Promise<Request> => {
  try {
    const headers = GetAuthHeaders();
    if (
      request.target_garden &&
      encodeURI(request.target_garden) == request.target_garden
    ) {
      headers.append("Target-Garden", request.target_garden);
    }
    if (
      request.source_garden &&
      encodeURI(request.source_garden) == request.source_garden
    ) {
      headers.append("Source-Garden", request.source_garden);
    }

    for (const [key, value] of Object.entries(headerData || {})) {
      headers.append(key, value as string);
    }

    let sessionUUID = localStorage.getItem("sessionUUID");
    if (!sessionUUID) {
      sessionUUID = uuidv4();
      localStorage.setItem("sessionUUID", sessionUUID);
    }

    request.metadata = request.metadata
      ? { ...request.metadata, ...{ sessionUUID: sessionUUID } }
      : { sessionUUID: sessionUUID };

    if (waitForCompletion === null || waitForCompletion === undefined) {
      waitForCompletion = false;
    }

    // Check if any parameters are a file, then use FormData instead of JSON
    const hasFileParameter = request.parameters
      ? Object.values(request.parameters).some((param) => param instanceof File)
      : false;

    if (hasFileParameter) {
      const formData = new FormData();

      const copyRequest = { ...request };
      const parametersWithoutFiles: any = {};

      for (const [key, value] of Object.entries(request.parameters || {})) {
        if (!(value instanceof File)) {
          parametersWithoutFiles[key] = value;
        }
      }
      copyRequest.parameters = parametersWithoutFiles;
      formData.append("request", JSON.stringify(copyRequest));

      for (const [key, value] of Object.entries(request.parameters || {})) {
        if (value instanceof File) {
          formData.append(key, value);
        }
      }

      const response = await fetch(
        `${GetBaseURL()}/api/v1/requests?blocking=${waitForCompletion}`,
        {
          headers: headers,
          method: "POST",
          body: formData,
        },
      );
      if (!response.ok) {
        // Handle non-OK responses (e.g., 404, 500)
        throw new Error(`HTTP error: Status ${response.status}`);
      }
      const data = (await response.json()) as Request;
      return data;
    }

    headers.append("Content-Type", "application/json");
    const response = await fetch(
      `${GetBaseURL()}/api/v1/requests?blocking=${waitForCompletion}`,
      {
        headers: headers,
        method: "POST",
        body: JSON.stringify(request),
      },
    );
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }
    const data = (await response.json()) as Request;

    // const storedRequests = localStorage.getItem("currentRequests");
    // if (storedRequests) {
    //   let parsedRequests = JSON.parse(storedRequests) as Array<Request>;

    //   parsedRequests.push(data);
    //   localStorage.setItem("currentRequests", JSON.stringify(parsedRequests));
    // } else {
    //   localStorage.setItem("currentRequests", JSON.stringify([data]));
    // }

    return data;
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching Requests:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};

export const DeleteRequest = async (request: Request, headerData?: any) => {
  try {
    const headers = GetAuthHeaders();

    for (const [key, value] of Object.entries(headerData || {})) {
      headers.append(key, value as string);
    }

    const response = await fetch(
      `${GetBaseURL()}/api/v1/requests?id=${request.id}`,
      {
        headers: headers,
        method: "DELETE",
      },
    );
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }

    return;
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching Requests:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};

export const DeleteRequests = async (deleteParams?: any) => {
  try {
    let queryString = "";
    const headers = GetAuthHeaders();
    const searchParams = new URLSearchParams();
    for (const [key, value] of Object.entries(deleteParams)) {
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

    const response = await fetch(
      `${GetBaseURL()}/api/v1/requests?${queryString}`,
      {
        headers: headers,
        method: "DELETE",
      },
    );

    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }

    return;
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching Requests:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};

export const CancelRequest = async (
  request: Request,
  headerData?: any,
): Promise<Request> => {
  try {
    const headers = GetAuthHeaders();

    headers.append("Content-Type", "application/json");

    for (const [key, value] of Object.entries(headerData || {})) {
      headers.append(key, value as string);
    }

    const response = await fetch(
      `${GetBaseURL()}/api/v1/requests/${request.id}`,
      {
        headers: headers,
        method: "PATCH",
        body: JSON.stringify({
          operation: "replace",
          path: "/status",
          value: "CANCELED",
        }),
      },
    );
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }

    const data = (await response.json()) as Request;
    return data;
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching Requests:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};

export const GetRequestProjections = async (
  request: Request,
  checkRequests: number = 1,
  checkDepth: number = 10,
  targetAmount: number = 5,
): Promise<RequestCommand[]> => {
  const sessionUUID = localStorage.getItem("sessionUUID");

  if (!sessionUUID) {
    return [];
  }

  // Get the last time this request was ran
  const lastRunQueryHeaders = {
    length: checkRequests,
    start: 0,
    include: [
      "id",
      "status",
      "created_at",
      "command",
      "instance_name",
      "system",
      "system_version",
      "namespace",
    ],
    query: [
      JSON.stringify({ field_name: "id", modifier: "ne", value: request.id }),
      JSON.stringify({ field_name: "status", modifier: "", value: "SUCCESS" }),
      JSON.stringify({
        field_name: "created_at",
        modifier: "lt",
        value: new Date(request.created_at)
          .toISOString()
          .substring(0, 19)
          .replace("T", " "),
      }),
      JSON.stringify({
        field_name: "command",
        modifier: "",
        value: request.command,
      }),
      JSON.stringify({
        field_name: "system",
        modifier: "",
        value: request.system,
      }),
      JSON.stringify({
        field_name: "system_version",
        modifier: "",
        value: request.system_version,
      }),
      JSON.stringify({
        field_name: "instance_name",
        modifier: "",
        value: request.instance_name,
      }),
      JSON.stringify({
        field_name: "namespace",
        modifier: "",
        value: request.namespace,
      }),
      JSON.stringify({
        field_name: "metadata__sessionUUID",
        modifier: "",
        value: sessionUUID,
      }),
    ],
  };

  const [lastRanHistory] = await GetRequestList(lastRunQueryHeaders);
  // Query 15 minute window after the request was completed by user and return 5 most recent requests in that window.

  if (lastRanHistory.length === 0) {
    return [];
  }
  const requestProjections = [] as RequestCommand[];

  for (const lastRun of lastRanHistory) {
    let maxCreatedAt = new Date(lastRun.created_at);
    maxCreatedAt.setMinutes(maxCreatedAt.getMinutes() + 15);

    if (new Date() < maxCreatedAt) {
      maxCreatedAt = new Date();
    } else if (maxCreatedAt > new Date(request.created_at)) {
      maxCreatedAt = new Date(request.created_at);
    }

    const nextRunQueryHeaders = {
      length: checkDepth,
      start: 0,
      include: [
        "id",
        "command",
        "instance_name",
        "system",
        "system_version",
        "namespace",
      ],
      query: [
        JSON.stringify({ field_name: "id", modifier: "ne", value: request.id }),
        JSON.stringify({
          field_name: "status",
          modifier: "",
          value: "SUCCESS",
        }),
        JSON.stringify({
          field_name: "created_at",
          modifier: "gt",
          value: new Date(lastRun.created_at)
            .toISOString()
            .substring(0, 19)
            .replace("T", " "),
        }),
        JSON.stringify({
          field_name: "created_at",
          modifier: "lt",
          value: maxCreatedAt.toISOString().substring(0, 19).replace("T", " "),
        }),
        JSON.stringify({
          field_name: "metadata__sessionUUID",
          modifier: "",
          value: sessionUUID,
        }),
      ],
    };

    const [nextRanHistory] = await GetRequestList(nextRunQueryHeaders);

    if (nextRanHistory && nextRanHistory.length > 0) {
      for (const req of nextRanHistory) {
        let unique = true;
        if (
          request.command === req.command &&
          request.instance_name === req.instance_name &&
          request.system === req.system &&
          request.system_version === req.system_version &&
          request.namespace === req.namespace
        ) {
          unique = false;
        }
        if (unique) {
          for (const projection of requestProjections) {
            if (
              projection.command === req.command &&
              projection.instance === req.instance_name &&
              projection.systemName === req.system &&
              projection.version === req.system_version &&
              projection.namespace === req.namespace
            ) {
              unique = false;
              break;
            }
          }
        }
        if (unique) {
          requestProjections.push({
            command: req.command,
            instance: req.instance_name,
            systemName: req.system,
            version: req.system_version,
            namespace: req.namespace,
          } as RequestCommand);

          if (requestProjections.length === targetAmount) {
            return requestProjections;
          }
        }
      }
    }
  }

  return requestProjections;
};
