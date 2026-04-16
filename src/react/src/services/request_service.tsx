import { v4 as uuidv4 } from "uuid";

import { Request } from "../models/brewtils-types";
import HttpError from "../types/errors";
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
      throw new HttpError(
        `HTTP error: Status ${response.status}`,
        response.status,
      );
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
  headerData: any,
): Promise<Request> => {
  try {
    const headers = GetAuthHeaders();
    for (const [key, value] of Object.entries(headerData)) {
      headers.append(key, value as string);
    }

    const response = await fetch(
      `${GetBaseURL()}/api/v1/requests/${requestId}`,
      {
        headers: headers,
      },
    );
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new HttpError(
        `HTTP error: Status ${response.status}`,
        response.status,
      );
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
