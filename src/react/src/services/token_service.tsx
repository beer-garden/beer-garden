import { jwtDecode } from "jwt-decode";

import { GetBaseURL } from "./util_service";

export const UserLogin = async (
  username: string,
  password: string,
  headerData?: any,
) => {
  try {
    const headers = new Headers();

    headers.append("Content-Type", "application/json");

    for (const [key, value] of Object.entries(headerData || {})) {
      headers.append(key, value as string);
    }

    const response = await fetch(`${GetBaseURL()}/api/v1/token`, {
      headers: headers,
      method: "POST",
      body: JSON.stringify({
        username: username,
        password: password,
      }),
    });
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }
    const data = await response.json();

    if (data.refresh) {
      SetRefresh(data.refresh);
    }
    if (data.access) {
      SetToken(data.access);
    }
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error Logging in User:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};

export const DoRefresh = async (headerData?: any) => {
  try {
    const headers = GetAuthHeaders();

    headers.append("Content-Type", "application/json");

    for (const [key, value] of Object.entries(headerData || {})) {
      headers.append(key, value as string);
    }

    const response = await fetch(`${GetBaseURL()}/api/v1/token/refresh`, {
      headers: headers,
      method: "POST",
      body: JSON.stringify({ refresh: GetRefresh() }),
    });
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      ClearRefresh().catch((error) => {
        console.error("Error Clearing Refresh Token:", error);
      });
      ClearToken();
      throw new Error(`HTTP error: Status ${response.status}`);
    }
    const data = await response.json();

    if (data.refresh) {
      SetRefresh(data.refresh);
    }
    if (data.access) {
      SetToken(data.access);
    }
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error Logging in User:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};

const SetRefresh = (refresh: string) => {
  localStorage.setItem("refresh", refresh);
};

const GetRefresh = () => {
  return localStorage.getItem("refresh");
};

export const ClearRefresh = async () => {
  const refresh = GetRefresh();
  if (refresh) {
    localStorage.removeItem("refresh");

    const headers = GetAuthHeaders();

    headers.append("Content-Type", "application/json");

    const response = await fetch(`${GetBaseURL()}/api/v1/token/revoke`, {
      headers: headers,
      method: "POST",
      body: JSON.stringify({ refresh: refresh }),
    });

    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }
  }
};

export const preemptiveRefresh = () => {
  const token = GetToken();

  if (token) {
    const exp = jwtDecode(token).exp;
    if (exp) {
      const expDate = new Date(exp * 1000);
      const curDate = new Date();

      const diffInMilliseconds = Math.abs(
        expDate.getTime() - curDate.getTime(),
      );

      // Convert milliseconds to minutes: 1000ms/s * 60s/min = 60000ms/min
      const diffInMinutes = Math.floor(diffInMilliseconds / 60000);

      if (diffInMinutes <= 2) {
        DoRefresh(GetRefresh()).catch((error) => {
          console.error("Error Getting Refresh Token:", error);
        });
      }
    }
  }
};

const SetToken = (token: string) => {
  localStorage.setItem("token", token);
};

export const GetToken = (): string | null => {
  return localStorage.getItem("token");
};

export const ClearToken = () => {
  localStorage.removeItem("token");
};

export const GetAuthHeaders = () => {
  const headers = new Headers();
  const token = GetToken();
  if (token) {
    headers.append("Authorization", `Bearer ${token}`);
  }
  return headers;
};

export const RevokeToken = async (username: string) => {
  const headers = GetAuthHeaders();

  const response = await fetch(`${GetBaseURL()}/api/v1/token/${username}`, {
    headers: headers,
    method: "DELETE",
  });

  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
};
