import roleReducer from "../role";
import * as types from "../../constants/ActionTypes";

const setupState = overrideState => {
  return Object.assign(
    {
      deleteRoleLoading: false,
      deleteRoleError: null,
      roles: [],
      rolesLoading: false,
      rolesError: null,
      roleCreateLoading: false,
      selectedRole: {},
      roleCreateError: null,
      roleLoading: false,
      roleError: null,
      updateRoleLoading: false,
      updateRoleError: null,
    },
    overrideState,
  );
};

describe("role reducer", () => {
  it("should return the initial state", () => {
    expect(roleReducer(undefined, {})).toEqual({
      deleteRoleLoading: false,
      deleteRoleError: null,
      roles: [],
      rolesLoading: false,
      rolesError: null,
      roleCreateLoading: false,
      selectedRole: {},
      roleCreateError: null,
      roleLoading: false,
      roleError: null,
      updateRoleLoading: false,
      updateRoleError: null,
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
    expect(newState.selectedRole).toEqual("role1");
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

  it("should handle DELETE_ROLE_BEGIN", () => {
    const initialState = setupState({
      deleteRoleLoading: false,
      deleteRoleError: "previous error",
    });
    const action = {
      type: types.DELETE_ROLE_BEGIN,
    };
    const newState = roleReducer(initialState, action);
    expect(newState.deleteRoleLoading).toBe(true);
    expect(newState.deleteRoleError).toBeNull();
  });

  it("should handle DELETE_ROLE_SUCCESS when loaded", () => {
    const initialState = setupState({
      roles: [{ id: "roleId" }],
      deleteRoleLoading: true,
      deleteRoleError: null,
    });
    const action = {
      type: types.DELETE_ROLE_SUCCESS,
      payload: "roleId",
    };
    const newState = roleReducer(initialState, action);
    expect(newState.deleteRoleLoading).toBe(false);
    expect(newState.deleteRoleError).toBeNull();
    expect(newState.roles).toEqual([]);
  });

  it("should handle DELETE_ROLE_SUCCESS when not loaded", () => {
    const initialState = setupState({
      roles: [],
      deleteRoleLoading: true,
      deleteRoleError: null,
    });
    const action = {
      type: types.DELETE_ROLE_SUCCESS,
      payload: "roleId",
    };
    const newState = roleReducer(initialState, action);
    expect(newState.deleteRoleLoading).toBe(false);
    expect(newState.deleteRoleError).toBeNull();
    expect(newState.roles).toEqual([]);
  });

  it("should handle DELETE_ROLE_FAILURE", () => {
    const initialState = setupState({
      deleteRoleLoading: true,
      deleteRoleError: null,
    });
    const action = {
      type: types.DELETE_ROLE_FAILURE,
      payload: { error: new Error("create error") },
    };
    const newState = roleReducer(initialState, action);
    expect(newState.deleteRoleLoading).toBe(false);
    expect(newState.deleteRoleError).not.toBeNull();
  });

  it("should handle UPDATE_ROLE_BEGIN", () => {
    const initialState = setupState({
      updateRoleLoading: false,
      updateRoleError: "previous error",
    });
    const action = {
      type: types.UPDATE_ROLE_BEGIN,
    };
    const newState = roleReducer(initialState, action);
    expect(newState.updateRoleLoading).toBe(true);
    expect(newState.updateRoleError).toBeNull();
  });

  it("should handle UPDATE_ROLE_SUCCESS when loaded", () => {
    const initialState = setupState({
      roles: [{ id: "roleId", name: "newName" }],
      updateRoleLoading: true,
      updateRoleError: null,
    });
    const action = {
      type: types.UPDATE_ROLE_SUCCESS,
      payload: { id: "roleId", name: "newName" },
    };
    const newState = roleReducer(initialState, action);
    expect(newState.updateRoleLoading).toBe(false);
    expect(newState.updateRoleError).toBeNull();
    expect(newState.roles).toEqual([{ id: "roleId", name: "newName" }]);
  });

  it("should handle UPDATE_ROLE_SUCCESS when not loaded", () => {
    const initialState = setupState({
      roles: [],
      updateRoleLoading: true,
      updateRoleError: null,
    });
    const action = {
      type: types.UPDATE_ROLE_SUCCESS,
      payload: { id: "roleId", name: "newName" },
    };
    const newState = roleReducer(initialState, action);
    expect(newState.updateRoleLoading).toBe(false);
    expect(newState.updateRoleError).toBeNull();
    expect(newState.roles).toEqual([]);
  });

  it("should handle UPDATE_ROLE_FAILURE", () => {
    const initialState = setupState({
      updateRoleLoading: true,
      updateRoleError: null,
    });
    const action = {
      type: types.UPDATE_ROLE_FAILURE,
      payload: { error: new Error("update error") },
    };
    const newState = roleReducer(initialState, action);
    expect(newState.updateRoleLoading).toBe(false);
    expect(newState.updateRoleError).not.toBeNull();
  });

  it("should handle FETCH_ROLE_BEGIN", () => {
    const initialState = setupState({
      roleLoading: false,
      roleError: "previousError",
    });
    const action = { type: types.FETCH_ROLE_BEGIN };
    const newState = roleReducer(initialState, action);
    expect(newState.roleLoading).toBe(true);
    expect(newState.roleError).toBeNull();
  });

  it("should handle FETCH_ROLE_SUCCESS", () => {
    const initialState = setupState({
      roleLoading: true,
      roleError: "previousError",
    });
    const action = {
      type: types.FETCH_ROLE_SUCCESS,
      payload: { role: "role1" },
    };
    const newState = roleReducer(initialState, action);
    expect(newState.selectedRole).toEqual("role1");
    expect(newState.roleLoading).toBe(false);
    expect(newState.roleError).toBeNull();
  });

  it("should handle FETCH_ROLE_FAILURE", () => {
    const initialState = setupState({
      roleLoading: true,
    });
    const action = {
      type: types.FETCH_ROLE_FAILURE,
      payload: { error: new Error("someError") },
    };
    const newState = roleReducer(initialState, action);
    expect(newState.selectedRole).toEqual({});
    expect(newState.roleLoading).toBe(false);
    expect(newState.roleError).not.toBeNull();
  });
});
