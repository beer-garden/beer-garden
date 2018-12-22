import axios from "axios";
import camelcaseKeys from "camelcase-keys";
import {
  FETCH_SYSTEMS_BEGIN,
  FETCH_SYSTEMS_SUCCESS,
  FETCH_SYSTEMS_FAILURE,
} from "../constants/ActionTypes";
import { defaultErrorHandler } from ".";

export const fetchSystemsBegin = () => ({
  type: FETCH_SYSTEMS_BEGIN,
});

export const fetchSystemsSuccess = data => ({
  type: FETCH_SYSTEMS_SUCCESS,
  payload: { systems: data },
});

export const fetchSystemsFailure = error => ({
  type: FETCH_SYSTEMS_FAILURE,
  payload: { error },
});

export function fetchSystems() {
  return async dispatch => {
    dispatch(fetchSystemsBegin());

    return axios
      .get("/api/v1/systems")
      .then(res => {
        const normalizedData = camelcaseKeys(res.data);
        dispatch(fetchSystemsSuccess(normalizedData));
        return normalizedData;
      })
      .catch(e => defaultErrorHandler(e, dispatch, fetchSystemsFailure));
  };
}
