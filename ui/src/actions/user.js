import axios from "axios";
import camelcaseKeys from "camelcase-keys";
import {
  CREATE_USER_BEGIN,
  CREATE_USER_FAILURE,
  CREATE_USER_SUCCESS,
  DELETE_USER_BEGIN,
  DELETE_USER_FAILURE,
  DELETE_USER_SUCCESS,
  FETCH_USERS_BEGIN,
  FETCH_USERS_SUCCESS,
  FETCH_USERS_FAILURE,
  FETCH_USER_BEGIN,
  FETCH_USER_SUCCESS,
  FETCH_USER_FAILURE,
} from "../constants/ActionTypes";
import { defaultErrorHandler } from "./index";

export const fetchUsersBegin = () => ({
  type: FETCH_USERS_BEGIN,
});

export const fetchUsersSuccess = data => ({
  type: FETCH_USERS_SUCCESS,
  payload: { users: data },
});

export const fetchUsersFailure = error => ({
  type: FETCH_USERS_FAILURE,
  payload: { error },
});

export const fetchUserBegin = () => ({
  type: FETCH_USER_BEGIN,
});

export const fetchUserSuccess = data => ({
  type: FETCH_USER_SUCCESS,
  payload: { user: data },
});

export const fetchUserFailure = error => ({
  type: FETCH_USER_FAILURE,
  payload: { error },
});

export const createUserBegin = () => ({
  type: CREATE_USER_BEGIN,
});

export const createUserSuccess = data => ({
  type: CREATE_USER_SUCCESS,
  payload: { user: data },
});

export const createUserFailure = error => ({
  type: CREATE_USER_FAILURE,
  payload: { error },
});

export const deleteUserBegin = () => ({
  type: DELETE_USER_BEGIN,
});

export const deleteUserSuccess = id => ({
  type: DELETE_USER_SUCCESS,
  payload: id,
});

export const deleteUserFailure = error => ({
  type: DELETE_USER_FAILURE,
  payload: { error },
});

export function fetchUser(username) {
  return dispatch => {
    dispatch(fetchUserBegin());

    return axios
      .get(`/api/v1/users/${username}`)
      .then(res => {
        const normalizedData = camelcaseKeys(res.data);
        dispatch(fetchUserSuccess(normalizedData));
        return normalizedData;
      })
      .catch(e => defaultErrorHandler(e, dispatch, fetchUserFailure));
  };
}

export const getUser = username => (dispatch, getState) => {
  const users = getState().userReducer.users;
  const user = users.find(u => u.username === username);
  if (user) {
    return dispatch(fetchUserSuccess(user));
  }
  return dispatch(fetchUser(username));
};

export function createUser(username, password, roles) {
  return dispatch => {
    dispatch(createUserBegin());

    return axios
      .post("/api/v1/users", {
        username,
        password,
        roles: roles.map(r => r.name),
      })
      .then(res => {
        const normalizedData = camelcaseKeys(res.data);
        dispatch(createUserSuccess(normalizedData));
        return normalizedData;
      })
      .catch(e => defaultErrorHandler(e, dispatch, createUserFailure));
  };
}

export function deleteUser(userId) {
  return dispatch => {
    dispatch(deleteUserBegin());

    return axios
      .delete(`/api/v1/users/${userId}`)
      .then(() => {
        dispatch(deleteUserSuccess(userId));
        return userId;
      })
      .catch(e => defaultErrorHandler(e, dispatch, deleteUserFailure));
  };
}

export function fetchUsers() {
  return dispatch => {
    dispatch(fetchUsersBegin());

    return axios
      .get("/api/v1/users")
      .then(res => {
        const normalizedData = camelcaseKeys(res.data);
        dispatch(fetchUsersSuccess(normalizedData));
        return normalizedData;
      })
      .catch(e => defaultErrorHandler(e, dispatch, fetchUsersFailure));
  };
}
