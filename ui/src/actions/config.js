import axios from "axios";
import camelcaseKeys from "camelcase-keys";
import {
  FETCH_CONFIG_BEGIN,
  FETCH_CONFIG_FAILURE,
  FETCH_CONFIG_SUCCESS,
} from "../constants/ActionTypes";
import { isEmpty } from "../utils";
import { defaultErrorHandler } from ".";

export const fetchConfigBegin = () => ({
  type: FETCH_CONFIG_BEGIN,
});

export const fetchConfigSuccess = config => ({
  type: FETCH_CONFIG_SUCCESS,
  payload: { config },
});

export const fetchConfigFailure = error => ({
  type: FETCH_CONFIG_FAILURE,
  payload: { error },
});

export function fetchConfig() {
  return async dispatch => {
    dispatch(fetchConfigBegin());

    return axios
      .get("/config")
      .then(response => {
        const normalizedData = camelcaseKeys(response.data);
        dispatch(fetchConfigSuccess(normalizedData));
        return normalizedData;
      })
      .catch(e => defaultErrorHandler(e, dispatch, fetchConfigFailure));
  };
}

export const loadConfig = () => (dispatch, getState) => {
  const configData = getState().configReducer.config;
  if (!isEmpty(configData)) {
    return null;
  }

  return dispatch(fetchConfig());
};
