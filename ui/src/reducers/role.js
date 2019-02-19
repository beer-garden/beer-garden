import {
  CREATE_ROLE_BEGIN,
  CREATE_ROLE_SUCCESS,
  CREATE_ROLE_FAILURE,
  FETCH_ROLES_BEGIN,
  FETCH_ROLES_SUCCESS,
  FETCH_ROLES_FAILURE,
} from "../constants/ActionTypes";

const initialState = {
  roles: [],
  rolesLoading: false,
  rolesError: null,
  roleCreateLoading: false,
  roleCreateError: null,
};

export default function roleReducer(state = initialState, action) {
  switch (action.type) {
    case FETCH_ROLES_BEGIN:
      return {
        ...state,
        rolesError: null,
        rolesLoading: true,
      };

    case FETCH_ROLES_SUCCESS:
      return {
        ...state,
        rolesLoading: false,
        rolesError: null,
        roles: action.payload.roles,
      };

    case FETCH_ROLES_FAILURE:
      return {
        ...state,
        rolesLoading: false,
        rolesError: action.payload.error,
        roles: [],
      };

    case CREATE_ROLE_BEGIN:
      return {
        ...state,
        roleCreateLoading: true,
        roleCreateError: null,
      };

    case CREATE_ROLE_SUCCESS:
      return {
        ...state,
        roleCreateLoading: false,
        roleCreateError: null,
        roles: [...state.roles, action.payload.role],
      };

    case CREATE_ROLE_FAILURE:
      return {
        ...state,
        roleCreateLoading: false,
        roleCreateError: action.payload.error,
      };

    default:
      return state;
  }
}
