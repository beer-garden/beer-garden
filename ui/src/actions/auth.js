import axios from "axios";
import camelcaseKeys from "camelcase-keys";
import {
  USER_LOGIN_BEGIN,
  USER_LOGIN_SUCCESS,
  USER_LOGIN_FAILURE,
  USER_LOGOUT_BEGIN,
  USER_LOGOUT_SUCCESS,
  USER_LOGOUT_FAILURE,
} from "../constants/ActionTypes";
import jwtDecode from "jwt-decode";
import { defaultErrorHandler } from ".";

export const userLoginBegin = () => ({
  type: USER_LOGIN_BEGIN,
});

export const userLoginSuccess = data => ({
  type: USER_LOGIN_SUCCESS,
  payload: data,
});

export const userLoginFailure = error => ({
  type: USER_LOGIN_FAILURE,
  payload: { error },
});

export const userLogoutBegin = () => ({
  type: USER_LOGOUT_BEGIN,
});

export const userLogoutSuccess = () => ({
  type: USER_LOGOUT_SUCCESS,
});

export const userLogoutFailure = error => ({
  type: USER_LOGOUT_FAILURE,
  payload: { error },
});

export function logout() {
  return async dispatch => {
    dispatch(userLogoutBegin());

    return axios
      .delete("/api/v1/tokens")
      .then(() => dispatch(userLogoutSuccess()))
      .catch(e => defaultErrorHandler(e, dispatch, userLogoutFailure));
  };
}

export function basicLogin(username, password) {
  return async dispatch => {
    dispatch(userLoginBegin());

    const payload = { username, password, remember_me: true };
    return axios
      .post("/api/v1/tokens", JSON.stringify(payload))
      .then(res => {
        const normalizedData = camelcaseKeys(res.data);
        const userData = jwtDecode(normalizedData["token"]);
        dispatch(userLoginSuccess({ data: userData }));
        return normalizedData;
      })
      .catch(e => defaultErrorHandler(e, dispatch, userLoginFailure));
  };
}

export function loadUserData() {
  return async dispatch => {
    dispatch(userLoginBegin());

    return axios
      .get("/api/v1/tokens")
      .then(res => {
        const normalizedData = camelcaseKeys(res.data);
        const userData = jwtDecode(normalizedData["token"]);
        dispatch(userLoginSuccess({ data: userData }));
        return normalizedData;
      })
      .catch(e => defaultErrorHandler(e, dispatch, userLoginFailure));
  };
}
