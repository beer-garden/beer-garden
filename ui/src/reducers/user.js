import {
  FETCH_USERS_BEGIN,
  FETCH_USERS_SUCCESS,
  FETCH_USERS_FAILURE,
} from "../constants/ActionTypes";

const initialState = {
  users: [],
  usersLoading: false,
  usersError: null,
};

export default function userReducer(state = initialState, action) {
  switch (action.type) {
    case FETCH_USERS_BEGIN:
      return {
        ...state,
        usersError: null,
        usersLoading: true,
      };

    case FETCH_USERS_SUCCESS:
      return {
        ...state,
        usersLoading: false,
        usersError: null,
        users: action.payload.users,
      };

    case FETCH_USERS_FAILURE:
      return {
        ...state,
        usersLoading: false,
        usersError: action.payload.error,
        users: [],
      };

    default:
      return state;
  }
}
