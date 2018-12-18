import axios from 'axios';
import camelcaseKeys from 'camelcase-keys';
import {
  FETCH_CONFIG_BEGIN,
  FETCH_CONFIG_FAILURE,
  FETCH_CONFIG_SUCCESS,
} from '../constants/ActionTypes';

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
      .get('/config')
      .then(response => {
        const normalizedData = camelcaseKeys(response.data);
        dispatch(fetchConfigSuccess(normalizedData));
        return normalizedData;
      })
      .catch(error => {
        if (
          error.response &&
          error.response.data &&
          error.response.data.message
        ) {
          const newError = Error(error.response.data.message);
          dispatch(fetchConfigFailure(newError));
        } else {
          dispatch(fetchConfigFailure(error));
        }
      });
  };
}

export const loadConfig = () => (dispatch, getState) => {
  const configData = getState().config;
  if (configData && Object.getOwnPropertyNames(configData).length > 0) {
    return null;
  }

  return dispatch(fetchConfig());
};
