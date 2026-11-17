import { Role } from "../models/brewtils-types";
import { GetAuthHeaders } from "./token_service";
import { GetBaseURL } from "./util_service";

export const GetRole = async (roleId: string): Promise<Role> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  const fetch_url = `${GetBaseURL()}/api/v1/roles/${roleId}`;
  const response = await fetch(fetch_url, {
    headers: headers,
    method: "GET",
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
  const data = (await response.json()) as Role;
  return data;
};

export const DeleteRole = async (roleId: string): Promise<void> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  const fetch_url = `${GetBaseURL()}/api/v1/roles/${roleId}`;
  const response = await fetch(fetch_url, {
    headers: headers,
    method: "DELETE",
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
};

export const EditRole = async (role: Role): Promise<Role> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  const fetch_url = `${GetBaseURL()}/api/v1/roles/${role.id}`;
  const response = await fetch(fetch_url, {
    headers: headers,
    method: "PATCH",
    body: JSON.stringify({
      operations: [
        {
          operation: "update_role",
          path: "",
          value: role,
        },
      ],
    }),
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
  const data = (await response.json()) as Role;
  return data;
};

export const GetRoles = async (): Promise<Role[]> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  const fetch_url = `${GetBaseURL()}/api/v1/roles/`;
  const response = await fetch(fetch_url, {
    headers: headers,
    method: "GET",
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
  const data = (await response.json()) as Role[];
  return data;
};

export const Rescan = async (): Promise<void> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  const response = await fetch(`${GetBaseURL()}/api/v1/roles/`, {
    headers: headers,
    method: "PATCH",
    body: JSON.stringify({
      operations: [
        {
          operation: "rescan",
        },
      ],
    }),
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
};

export const CreateRole = async (newRole: Role): Promise<Role> => {
  const headers = GetAuthHeaders();
  headers.append("Content-Type", "application/json");
  const response = await fetch(`${GetBaseURL()}/api/v1/roles/`, {
    headers: headers,
    method: "POST",
    body: JSON.stringify(newRole),
  });
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }
  const data = (await response.json()) as Role;
  return data;
};
