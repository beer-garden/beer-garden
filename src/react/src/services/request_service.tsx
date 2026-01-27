import { Request } from "../models/brewtils-types";
import { v4 as uuidv4 } from "uuid";

export const GetRequestList = async (
  headerData?: any,
): Promise<[Request[], Headers]> => {
  try {
    const fetchHeaders = new Headers();
    if (headerData) {
      for (const [key, value] of Object.entries(headerData)) {
        fetchHeaders.append(key, value as string);
      }
    } else {
      headerData = {};
    }

    let queryString = "";

    if (headerData) {
      // queryString = new URLSearchParams(headerData).toString();
      let searchParams = new URLSearchParams();
      for (const [key, value] of Object.entries(headerData)) {
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

    const response = await fetch(`/api/v1/requests?${queryString}`);
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
  headerData: any,
): Promise<Request> => {
  try {
    const headers = new Headers();
    for (const [key, value] of Object.entries(headerData)) {
      headers.append(key, value as string);
    }

    const response = await fetch(`/api/v1/requests/${requestId}`, {
      headers: headers,
    });
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
    const headers = new Headers();

    for (const [key, value] of Object.entries(headerData || {})) {
      headers.append(key, value as string);
    }

    headers.append("Content-Type", "application/json");

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

    const response = await fetch(
      "/api/v1/requests?blocking=" + waitForCompletion,
      {
        // headers: {
        //   'Content-Type': 'application/json' // *specify the content type
        // },
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
    const headers = new Headers();

    for (const [key, value] of Object.entries(headerData || {})) {
      headers.append(key, value as string);
    }

    const response = await fetch("/api/v1/requests?id=" + request.id, {
      // headers: {
      //   'Content-Type': 'application/json' // *specify the content type
      // },
      headers: headers,
      method: "DELETE",
    });
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

export const WatchRequest = (
  request: Request,
  setRequest: (request: Request) => void,
) => {
  const eventUrl =
    (window.location.protocol === "https:" ? "wss://" : "ws://") +
    window.location.host +
    "/" +
    `api/v1/socket/events/`;
  const current = new WebSocket("ws://localhost:2337/api/v1/socket/events/");

  current.onmessage = (e: any) => {
    const message = JSON.parse(e.data);

    if (message.payload_type === "Request") {
      if (message.payload.id && message.payload.id === request.id) {
        setRequest(message.payload as Request);
        if (!["CREATED", "IN_PROGRESS"].includes(message.payload.status)) {
          current.close();
        }
      }
    }
  };

  return current;
};
