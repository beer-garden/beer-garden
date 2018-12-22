import {
  USER_LOGIN_BEGIN,
  USER_LOGIN_SUCCESS,
  USER_LOGIN_FAILURE,
} from "../constants/ActionTypes";

const cookies = document.cookie.split("; ");
const sessionCookie = cookies.find(item => item.startsWith("refresh_id="));
const isGuest = localStorage.getItem("loggedInAsGuest") || false;

const initialState = {
  userData: {},
  isAuthenticated: sessionCookie ? true : false,
  isGuest: isGuest,
  userLoading: false,
  userError: null,
};

export default function authReducer(state = initialState, action) {
  switch (action.type) {
    case USER_LOGIN_BEGIN:
      return {
        ...state,
        userData: {},
        isAuthenticated: false,
        isGuest: false,
        userLoading: true,
        userError: null,
      };
    case USER_LOGIN_SUCCESS:
      return {
        ...state,
        userLoading: false,
        isAuthenticated: true,
        isGuest: action.payload.isGuest,
        userError: null,
        userData: action.payload.data,
      };
    case USER_LOGIN_FAILURE:
      return {
        ...state,
        userData: {},
        isAuthenticated: false,
        isGuest: false,
        userLoading: false,
        userError: action.payload.error,
      };
    default:
      return state;
  }
}
