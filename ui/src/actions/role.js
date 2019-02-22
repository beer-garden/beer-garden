import axios from "axios";
import camelcaseKeys from "camelcase-keys";
import {
  CREATE_ROLE_BEGIN,
  CREATE_ROLE_SUCCESS,
  CREATE_ROLE_FAILURE,
  FETCH_ROLES_BEGIN,
  FETCH_ROLES_SUCCESS,
  FETCH_ROLES_FAILURE,
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
