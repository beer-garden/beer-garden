import { jwtDecode } from "jwt-decode";

import { CustomJwtPayload } from "../models/models";
import { ChangeTheme, ClearThemes, GetBaseURL } from "./util_service";

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
      await LogoutCurrentUser();

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

export const GetRefresh = () => {
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

  if (token != null) {
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

  const decode = jwtDecode<CustomJwtPayload>(token);
  if (decode.preferences && typeof decode.preferences.theme === "string") {
    localStorage.setItem("theme_color", decode.preferences.theme);
  }
  if (decode.preferences && typeof decode.preferences.dark_mode === "boolean") {
    localStorage.setItem("theme_dark", decode.preferences.dark_mode.toString());
  }
  ChangeTheme();
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
  if (token !== null) {
    headers.append("Authorization", `Bearer ${token}`);
  }
  return headers;
};

export const RevokeToken = async (username: string) => {
  const headers = GetAuthHeaders();

  const response = await fetch(`${GetBaseURL()}/api/v1/tokens/${username}`, {
    headers: headers,
    method: "DELETE",
  });

  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
};

export const LogoutCurrentUser = async () => {
  // Logout for tokens/refresh
  if (GetToken() !== null) {
    ClearToken();
  }
  if (GetRefresh()) {
    await ClearRefresh().catch((error) => {
      console.error("Error clearing Refresh Token:", error);
    });
  }

  // Remove Gardens and Systems cached
  sessionStorage.clear();

  // Resets to default Blue/Light Mode
  ClearThemes();

  // Reset Advance User Setting
  localStorage.removeItem("user_advanced");
};
