import axios from 'axios';
import camelcaseKeys from 'camelcase-keys';
import {
  USER_LOGIN_BEGIN,
  USER_LOGIN_SUCCESS,
  USER_LOGIN_FAILURE,
} from '../constants/ActionTypes';
import { defaultErrorHandler } from '.';

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

export function basicLogin(username, password, rememberMe = false) {
  return async dispatch => {
    dispatch(userLoginBegin());

    const payload = { username, password };
    return axios
      .post('/api/v1/tokens', JSON.stringify(payload))
      .then(res => {
        if (rememberMe) {
          console.log('I should store the refresh token');
        }
        const normalizedData = camelcaseKeys(res.data);
        const actionPayload = { isGuest: false, data: normalizedData };
        dispatch(userLoginSuccess(actionPayload));
        return normalizedData;
      })
      .catch(e => defaultErrorHandler(e, dispatch, userLoginFailure));
  };
}
