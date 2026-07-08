import { jwtDecode } from "jwt-decode";

import { AliasUserMap, Role, User } from "../models/brewtils-types";
import { CustomJwtPayload } from "../models/models";
import { GetAuthHeaders, GetToken } from "./token_service";
import { GetBaseURL } from "./util_service";

export const GetCurrentUser = () => {
  const token = GetToken();
  if (token !== null) {
    const decode = jwtDecode<CustomJwtPayload>(token);
    if (decode.username) {
      return decode.username;
    }
  }
  return undefined;
};

export const GetCurrentRoles = (): Array<Role> | undefined => {
  const token = GetToken();
  if (token !== null) {
    const decode = jwtDecode<CustomJwtPayload>(token);
    if (decode.roles) {
      const userRoles = [] as Array<Role>;
      for (const role of decode.roles) {
        // The role can be a string or an object depending on how the token was generated
        if (typeof role === "string") {
          userRoles.push(JSON.parse(role) as Role);
        } else {
          userRoles.push(role as Role);
        }
      }
      return userRoles;
    }
  }
  return undefined;
};

export const UpdateUserTheme = async (theme: string): Promise<void> => {
  const headers = GetAuthHeaders();
  const username = GetCurrentUser();
  if (!username) {
    return;
  }
  headers.append("Content-Type", "application/json");
  const fetch_url = `${GetBaseURL()}/api/v1/users/${username}`;
  const response = await fetch(fetch_url, {
    headers: headers,
    method: "PATCH",
    body: JSON.stringify({
      operation: "set",
      path: "/preferences/theme",
      value: theme,
    }),
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
};

export const UpdateUserDarkMode = async (darkMode: boolean): Promise<void> => {
  const headers = GetAuthHeaders();
  const username = GetCurrentUser();
  if (!username) {
    return;
  }
  headers.append("Content-Type", "application/json");
  const fetch_url = `${GetBaseURL()}/api/v1/users/${username}`;
  const response = await fetch(fetch_url, {
    headers: headers,
    method: "PATCH",
    body: JSON.stringify({
      operation: "set",
      path: "/preferences/dark_mode",
      value: darkMode,
    }),
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
};

export const UpdatePowerUserMode = async (
  powerUser: boolean,
): Promise<void> => {
  const headers = GetAuthHeaders();
  const username = GetCurrentUser();
  if (!username) {
    return;
  }
  headers.append("Content-Type", "application/json");
  const fetch_url = `${GetBaseURL()}/api/v1/users/${username}`;
  const response = await fetch(fetch_url, {
    headers: headers,
    method: "PATCH",
    body: JSON.stringify({
      operation: "set",
      path: "/preferences/power_user",
      value: powerUser,
    }),
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
};

export const GetUsers = async (): Promise<Array<User>> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  const fetch_url = `${GetBaseURL()}/api/v1/users/`;
  const response = await fetch(fetch_url, {
    headers: headers,
    method: "GET",
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
  const data = (await response.json()) as User[];
  return data;
};

export const DeleteUser = async (username: string): Promise<void> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  const fetch_url = `${GetBaseURL()}/api/v1/users/${username}`;
  const response = await fetch(fetch_url, {
    headers: headers,
    method: "DELETE",
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
};

export const AdminUpdatePassword = async (
  username: string,
  newPassword: string,
): Promise<void> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  const fetch_url = `${GetBaseURL()}/api/v1/users/${username}`;
  const response = await fetch(fetch_url, {
    headers: headers,
    method: "PATCH",
    body: JSON.stringify({
      operation: "update_user_password",
      path: "",
      value: { password: newPassword },
    }),
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
};

export const UserUpdatePassword = async (
  newPassword: string,
  currentPassword: string,
): Promise<void> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  const fetch_url = `${GetBaseURL()}/api/v1/password/change/`;
  const response = await fetch(fetch_url, {
    headers: headers,
    method: "POST",
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
};

export const UpdateUserRoles = async (
  username: string,
  roles: Array<string>,
): Promise<User> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  const fetch_url = `${GetBaseURL()}/api/v1/users/${username}`;
  const response = await fetch(fetch_url, {
    headers: headers,
    method: "PATCH",
    body: JSON.stringify({
      operation: "update_roles",
      path: "",
      value: { roles: roles },
    }),
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
  const data = (await response.json()) as User;
  return data;
};

export const UpdateUserAliasMapping = async (
  username: string,
  aliasMapping: Array<AliasUserMap>,
): Promise<User> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  const fetch_url = `${GetBaseURL()}/api/v1/users/${username}`;
  const response = await fetch(fetch_url, {
    headers: headers,
    method: "PATCH",
    body: JSON.stringify({
      operation: "update_user_mappings",
      path: "",
      value: { user_alias_mapping: aliasMapping },
    }),
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
  const data = (await response.json()) as User;
  return data;
};

export const RescanUsers = async (): Promise<void> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  const fetch_url = `${GetBaseURL()}/api/v1/users/`;
  const response = await fetch(fetch_url, {
    headers: headers,
    method: "PATCH",
    body: JSON.stringify({
      operation: "rescan",
    }),
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
};

export const CreateUser = async (
  username: string,
  password: string,
): Promise<void> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  const fetch_url = `${GetBaseURL()}/api/v1/users/`;
  const response = await fetch(fetch_url, {
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
};
