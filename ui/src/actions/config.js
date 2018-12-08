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

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export function fetchConfig() {
  return async dispatch => {
    dispatch(fetchConfigBegin());

    console.log('fetching config...');
    console.log('Imitating some server load...');
    await sleep(1000);
    return fetch('/config')
      .then(handleErrors)
      .then(res => res.json())
      .then(json => {
        const normalizedData = camelcaseKeys(json);
        dispatch(fetchConfigSuccess(normalizedData));
        return normalizedData;
      })
      .catch(error => dispatch(fetchConfigFailure(error)));
  };
}

export const loadConfig = () => (dispatch, getState) => {
  const configData = getState().config;
  if (configData) {
    return null;
  }

  return dispatch(fetchConfig());
};

function handleErrors(response) {
  if (!response.ok) {
    throw Error(response.statusText);
  }
  return response;
}
