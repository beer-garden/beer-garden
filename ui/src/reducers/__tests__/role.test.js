import roleReducer from "../role";
import * as types from "../../constants/ActionTypes";

const setupState = overrideState => {
  return Object.assign(
    {
      roles: [],
      rolesLoading: true,
      rolesError: null,
      roleCreateLoading: false,
      roleCreateError: null,
    },
    overrideState,
  );
};

describe("role reducer", () => {
  it("should return the initial state", () => {
    expect(roleReducer(undefined, {})).toEqual({
      roles: [],
      rolesLoading: false,
      rolesError: null,
      roleCreateLoading: false,
      roleCreateError: null,
    });
  });

  it("should handle FETCH_ROLES_BEGIN", () => {
    const initialState = setupState({
      rolesLoading: false,
      rolesError: "previousError",
    });
    const action = { type: types.FETCH_ROLES_BEGIN };
    const newState = roleReducer(initialState, action);
    expect(newState.rolesLoading).toBe(true);
    expect(newState.rolesError).toBeNull();
  });

  it("should handle FETCH_ROLES_SUCCESS", () => {
    const initialState = setupState({
      rolesLoading: true,
      rolesError: "previousError",
    });
    const action = {
      type: types.FETCH_ROLES_SUCCESS,
      payload: { roles: ["role1"] },
    };
    const newState = roleReducer(initialState, action);
    expect(newState.roles).toEqual(["role1"]);
    expect(newState.rolesLoading).toBe(false);
    expect(newState.rolesError).toBeNull();
  });

  it("should handle FETCH_ROLES_FAILURE", () => {
    const initialState = setupState({
      rolesLoading: true,
    });
    const action = {
      type: types.FETCH_ROLES_FAILURE,
      payload: { error: new Error("someError") },
    };
    const newState = roleReducer(initialState, action);
    expect(newState.roles).toEqual([]);
    expect(newState.rolesLoading).toBe(false);
    expect(newState.rolesError).not.toBeNull();
  });

  it("should handle CREATE_ROLE_BEGIN", () => {
    const initialState = setupState({
      roleCreateLoading: false,
      roleCreateError: "previous error",
    });
    const action = {
      type: types.CREATE_ROLE_BEGIN,
    };
    const newState = roleReducer(initialState, action);
    expect(newState.roleCreateLoading).toBe(true);
    expect(newState.roleCreateError).toBeNull();
  });

  it("should handle CREATE_ROLE_SUCCESS", () => {
    const initialState = setupState({
      roles: [],
      roleCreateLoading: true,
      roleCreateError: null,
    });
    const action = {
      type: types.CREATE_ROLE_SUCCESS,
      payload: { role: "role1" },
    };
    const newState = roleReducer(initialState, action);
    expect(newState.roleCreateLoading).toBe(false);
    expect(newState.roleCreateError).toBeNull();
    expect(newState.roles).toEqual(["role1"]);
  });

  it("should handle CREATE_ROLE_FAILURE", () => {
    const initialState = setupState({
      roleCreateLoading: true,
      roleCreateError: null,
    });
    const action = {
      type: types.CREATE_ROLE_FAILURE,
      payload: { error: new Error("create error") },
    };
    const newState = roleReducer(initialState, action);
    expect(newState.roleCreateLoading).toBe(false);
    expect(newState.roleCreateError).not.toBeNull();
  });
});
