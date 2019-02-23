import {
  CREATE_USER_BEGIN,
  CREATE_USER_SUCCESS,
  CREATE_USER_FAILURE,
  FETCH_USERS_BEGIN,
  FETCH_USERS_SUCCESS,
  FETCH_USERS_FAILURE,
  FETCH_USER_BEGIN,
  FETCH_USER_SUCCESS,
  FETCH_USER_FAILURE,
  DELETE_USER_BEGIN,
  DELETE_USER_SUCCESS,
  DELETE_USER_FAILURE,
  UPDATE_USER_BEGIN,
  UPDATE_USER_SUCCESS,
  UPDATE_USER_FAILURE,
} from "../constants/ActionTypes";

const initialState = {
  users: [],
  usersLoading: false,
  usersError: null,
  selectedUser: {},
  userLoading: true,
  userError: null,
  createUserLoading: false,
  createUserError: null,
  deleteUserLoading: false,
  deleteUserError: null,
  updateUserLoading: false,
  updateUserError: null,
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

    case FETCH_USER_BEGIN:
      return {
        ...state,
        userError: null,
        userLoading: true,
        selectedUser: {},
      };

    case FETCH_USER_SUCCESS:
      return {
        ...state,
        userError: null,
        userLoading: false,
        selectedUser: action.payload.user,
      };

    case FETCH_USER_FAILURE:
      return {
        ...state,
        userError: action.payload.error,
        userLoading: false,
        selectedUser: {},
      };

    case CREATE_USER_BEGIN:
      return {
        ...state,
        createUserLoading: true,
        createUserError: null,
      };

    case CREATE_USER_SUCCESS:
      return {
        ...state,
        users: [...state.users, action.payload.user],
        createUserLoading: false,
        createUserError: null,
      };

    case CREATE_USER_FAILURE:
      return {
        ...state,
        createUserLoading: false,
        createUserError: action.payload.error,
      };

    case DELETE_USER_BEGIN:
      return {
        ...state,
        deleteUserError: null,
        deleteUserLoading: true,
      };

    case DELETE_USER_SUCCESS:
      return {
        ...state,
        users: removeIfExists(state.users, action.payload),
        deleteUserError: null,
        deleteUserLoading: false,
      };

    case DELETE_USER_FAILURE:
      return {
        ...state,
        deleteUserError: action.payload.error,
        deleteUserLoading: false,
      };

    case UPDATE_USER_BEGIN:
      return {
        ...state,
        updateUserError: null,
        updateUserLoading: true,
      };

    case UPDATE_USER_FAILURE:
      return {
        ...state,
        updateUserError: action.payload.error,
        updateUserLoading: false,
      };

    case UPDATE_USER_SUCCESS:
      return {
        ...state,
        users: updateIfExists(state.users, action.payload),
        selectedUser: action.payload.user,
        updateUserLoading: false,
        updateUserError: null,
      };

    default:
      return state;
  }
}

const updateIfExists = (users, user) => {
  const index = users.findIndex(u => u.id === user.id);
  let newUsers = [...users];
  if (index !== -1) {
    newUsers[index] = user;
  }
  return newUsers;
};

const removeIfExists = (users, id) => {
  const index = users.findIndex(u => u.id === id);
  let newUsers = [...users];
  if (index !== -1) {
    newUsers.splice(index, 1);
  }
  return newUsers;
};
