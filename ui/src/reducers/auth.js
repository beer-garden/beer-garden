import {
  USER_LOGIN_BEGIN,
  USER_LOGIN_SUCCESS,
  USER_LOGIN_FAILURE,
  USER_LOGOUT_BEGIN,
  USER_LOGOUT_SUCCESS,
  USER_LOGOUT_FAILURE,
  UPDATE_USER_SUCCESS,
} from "../constants/ActionTypes";
import { PROTECTED_USERS } from "../constants/auth";
import { getCookie, deleteCookie } from "../utils";

const REFRESH_COOKIE_NAME = "refresh_id";
const sessionCookie = getCookie(REFRESH_COOKIE_NAME);

const initialState = {
  userData: {},
  isAuthenticated: sessionCookie ? true : false,
  isAnonymous: false,
  isProtected: false,
  userLoading: false,
  userError: null,
  pwChangeRequired: false,
};

export default function authReducer(state = initialState, action) {
  switch (action.type) {
    case USER_LOGIN_BEGIN:
      return {
        ...state,
        userData: {},
        isProtected: false,
        isAnonymous: false,
        userLoading: true,
        userError: null,
      };
    case USER_LOGIN_SUCCESS:
      const username = action.payload.data.user.username;
      return {
        ...state,
        userLoading: false,
        isAuthenticated: true,
        isProtected: PROTECTED_USERS.indexOf(username) !== -1,
        isAnonymous: username === "anonymous",
        userError: null,
        userData: action.payload.data.user,
        pwChangeRequired: action.payload.data.pwChangeRequired,
      };
    case USER_LOGIN_FAILURE:
      deleteCookie(REFRESH_COOKIE_NAME);
      return {
        ...state,
        userData: {},
        isProtected: false,
        isAnonymous: false,
        isAuthenticated: false,
        userLoading: false,
        userError: action.payload.error,
      };
    case USER_LOGOUT_BEGIN:
      return {
        ...state,
        userLoading: true,
      };
    case USER_LOGOUT_FAILURE:
      return {
        ...state,
        userLoading: false,
        userError: action.payload.error,
      };
    case USER_LOGOUT_SUCCESS:
      return {
        ...state,
        userData: {},
        isProtected: false,
        isAnonymous: false,
        isAuthenticated: false,
        userLoading: false,
        userError: null,
      };

    case UPDATE_USER_SUCCESS:
      if (state.pwChangeRequired) {
        return {
          ...state,
          pwChangeRequired: false,
        };
      } else {
        return state;
      }

    default:
      return state;
  }
}
