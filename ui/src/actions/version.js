import axios from "axios";
import camelcaseKeys from "camelcase-keys";
import {
  FETCH_VERSION_BEGIN,
  FETCH_VERSION_FAILURE,
  FETCH_VERSION_SUCCESS,
} from "../constants/ActionTypes";
import { defaultErrorHandler } from ".";
import { isEmpty } from "../utils";

export const fetchVersionBegin = () => ({
  type: FETCH_VERSION_BEGIN,
});

export const fetchVersionSuccess = version => ({
  type: FETCH_VERSION_SUCCESS,
  payload: { version },
});

export const fetchVersionFailure = error => ({
  type: FETCH_VERSION_FAILURE,
  payload: { error },
});

export function fetchVersion() {
  return dispatch => {
    dispatch(fetchVersionBegin());

    return axios
      .get("/version")
      .then(response => {
        const normalizedData = camelcaseKeys(response.data);
        dispatch(fetchVersionSuccess(normalizedData));
        return normalizedData;
      })
      .catch(e => defaultErrorHandler(e, dispatch, fetchVersionFailure));
  };
}

export const loadVersion = () => (dispatch, getState) => {
  const versionData = getState().versionReducer.version;
  if (!isEmpty(versionData)) {
    return null;
  }

  return dispatch(fetchVersion());
};
