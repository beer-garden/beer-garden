import axios from "axios";
import camelcaseKeys from "camelcase-keys";
import {
  FETCH_USERS_BEGIN,
  FETCH_USERS_SUCCESS,
  FETCH_USERS_FAILURE,
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

export function fetchUsers() {
  return async dispatch => {
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
