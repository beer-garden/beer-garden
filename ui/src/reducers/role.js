import {
  CREATE_ROLE_BEGIN,
  CREATE_ROLE_SUCCESS,
  CREATE_ROLE_FAILURE,
  DELETE_ROLE_BEGIN,
  DELETE_ROLE_SUCCESS,
  DELETE_ROLE_FAILURE,
  FETCH_ROLE_BEGIN,
  FETCH_ROLE_SUCCESS,
  FETCH_ROLE_FAILURE,
  FETCH_ROLES_BEGIN,
  FETCH_ROLES_SUCCESS,
  FETCH_ROLES_FAILURE,
  UPDATE_ROLE_BEGIN,
  UPDATE_ROLE_SUCCESS,
  UPDATE_ROLE_FAILURE,
} from "../constants/ActionTypes";
import { removeIfExists, updateIfExists } from "../utils";

const initialState = {
  deleteRoleLoading: false,
  deleteRoleError: null,
  roles: [],
  rolesLoading: false,
  rolesError: null,
  roleCreateLoading: false,
  roleCreateError: null,
  selectedRole: {},
  roleLoading: false,
  roleError: null,
  updateRoleLoading: false,
  updateRoleError: null,
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
        selectedRole: action.payload.role,
      };

    case CREATE_ROLE_FAILURE:
      return {
        ...state,
        roleCreateLoading: false,
        roleCreateError: action.payload.error,
      };

    case DELETE_ROLE_BEGIN:
      return {
        ...state,
        deleteRoleError: null,
        deleteRoleLoading: true,
      };

    case DELETE_ROLE_SUCCESS:
      return {
        ...state,
        roles: removeIfExists(state.roles, action.payload),
        deleteRoleError: null,
        deleteRoleLoading: false,
      };

    case DELETE_ROLE_FAILURE:
      return {
        ...state,
        deleteRoleError: action.payload.error,
        deleteRoleLoading: false,
      };

    case FETCH_ROLE_BEGIN:
      return {
        ...state,
        roleError: null,
        roleLoading: true,
      };

    case FETCH_ROLE_SUCCESS:
      return {
        ...state,
        roleLoading: false,
        roleError: null,
        selectedRole: action.payload.role,
      };

    case FETCH_ROLE_FAILURE:
      return {
        ...state,
        roleLoading: false,
        roleError: action.payload.error,
        selectedRole: {},
      };

    case UPDATE_ROLE_BEGIN:
      return {
        ...state,
        updateRoleError: null,
        updateRoleLoading: true,
      };

    case UPDATE_ROLE_SUCCESS:
      return {
        ...state,
        roles: updateIfExists(state.roles, action.payload),
        updateRoleError: null,
        updateRoleLoading: false,
      };

    case UPDATE_ROLE_FAILURE:
      return {
        ...state,
        updateRoleError: action.payload.error,
        updateRoleLoading: false,
      };

    default:
      return state;
  }
}
