import axios from "axios";
import camelcaseKeys from "camelcase-keys";
import isEqual from "lodash.isequal";
import {
  CREATE_ROLE_BEGIN,
  CREATE_ROLE_SUCCESS,
  CREATE_ROLE_FAILURE,
  FETCH_ROLE_BEGIN,
  FETCH_ROLE_SUCCESS,
  FETCH_ROLE_FAILURE,
  FETCH_ROLES_BEGIN,
  FETCH_ROLES_SUCCESS,
  FETCH_ROLES_FAILURE,
  DELETE_ROLE_BEGIN,
  DELETE_ROLE_SUCCESS,
  DELETE_ROLE_FAILURE,
  UPDATE_ROLE_BEGIN,
  UPDATE_ROLE_SUCCESS,
  UPDATE_ROLE_FAILURE,
} from "../constants/ActionTypes";
import { defaultErrorHandler } from "./index";

export const fetchRolesBegin = () => ({
  type: FETCH_ROLES_BEGIN,
});

export const fetchRolesSuccess = data => ({
  type: FETCH_ROLES_SUCCESS,
  payload: { roles: data },
});

export const fetchRolesFailure = error => ({
  type: FETCH_ROLES_FAILURE,
  payload: { error },
});

export const createRoleBegin = () => ({
  type: CREATE_ROLE_BEGIN,
});

export const createRoleSuccess = data => ({
  type: CREATE_ROLE_SUCCESS,
  payload: { role: data },
});

export const createRoleFailure = error => ({
  type: CREATE_ROLE_FAILURE,
  payload: { error },
});

export const deleteRoleBegin = () => ({
  type: DELETE_ROLE_BEGIN,
});

export const deleteRoleSuccess = id => ({
  type: DELETE_ROLE_SUCCESS,
  payload: id,
});

export const deleteRoleFailure = error => ({
  type: DELETE_ROLE_FAILURE,
  payload: { error },
});

export const fetchRoleBegin = () => ({
  type: FETCH_ROLE_BEGIN,
});

export const fetchRoleSuccess = data => ({
  type: FETCH_ROLE_SUCCESS,
  payload: { role: data },
});

export const fetchRoleFailure = error => ({
  type: FETCH_ROLE_FAILURE,
  payload: { error },
});

export const updateRoleBegin = () => ({
  type: UPDATE_ROLE_BEGIN,
});

export const updateRoleSuccess = data => ({
  type: UPDATE_ROLE_SUCCESS,
  payload: { role: data },
});

export const updateRoleFailure = error => ({
  type: UPDATE_ROLE_FAILURE,
  payload: { error },
});

export function fetchRoles() {
  return dispatch => {
    dispatch(fetchRolesBegin());

    return axios
      .get("/api/v1/roles")
      .then(res => {
        const normalizedData = camelcaseKeys(res.data);
        dispatch(fetchRolesSuccess(normalizedData));
        return normalizedData;
      })
      .catch(e => defaultErrorHandler(e, dispatch, fetchRolesFailure));
  };
}

export function createRole(name, description, permissions) {
  return dispatch => {
    dispatch(createRoleBegin());

    return axios
      .post("/api/v1/roles", { name, description, permissions })
      .then(res => {
        const normalizedData = camelcaseKeys(res.data);
        dispatch(createRoleSuccess(normalizedData));
        return normalizedData;
      })
      .catch(e => defaultErrorHandler(e, dispatch, createRoleFailure));
  };
}

export function getRole(name) {
  return (dispatch, getState) => {
    dispatch(fetchRoleBegin());
    const roles = getState().roleReducer.roles;
    if (roles.length > 0) {
      const role = roles.find(r => r.name === name);
      if (role) {
        return dispatch(fetchRoleSuccess(role));
      } else {
        return dispatch(fetchRoleFailure(new Error("Invalid role name")));
      }
    }

    return dispatch(fetchRoles()).then(() => {
      const roles = getState().roleReducer.roles;
      const role = roles.find(r => r.name === name);
      if (role) {
        return dispatch(fetchRoleSuccess(role));
      } else {
        return dispatch(fetchRoleFailure(new Error("Invalid role name")));
      }
    });
  };
}

export function deleteRole(roleId) {
  return dispatch => {
    dispatch(deleteRoleBegin());

    return axios
      .delete(`/api/v1/roles/${roleId}`)
      .then(() => {
        dispatch(deleteRoleSuccess(roleId));
        return roleId;
      })
      .catch(e => defaultErrorHandler(e, dispatch, deleteRoleFailure));
  };
}

export function updateRole(prevRole, newRole) {
  return dispatch => {
    const operations = generateUpdateOperations(prevRole, newRole);
    dispatch(updateRoleBegin());

    return axios
      .patch(`/api/v1/roles/${prevRole.id}`, { operations })
      .then(res => {
        const normalizedData = camelcaseKeys(res.data);
        dispatch(updateRoleSuccess(normalizedData));
        return normalizedData;
      })
      .catch(e => defaultErrorHandler(e, dispatch, updateRoleFailure));
  };
}

function generateUpdateOperations(prevRole, newRole) {
  const operations = [];
  if (newRole.description !== prevRole.description) {
    operations.push({
      operation: "update",
      path: "/description",
      value: newRole.description,
    });
  }

  if (!isEqual(prevRole.permissions, newRole.permissions)) {
    operations.push({
      operation: "set",
      path: "/permissions",
      value: newRole.permissions,
    });
  }

  return operations;
}
