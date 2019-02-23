import userReducer from "../user";
import * as types from "../../constants/ActionTypes";

const setupState = overrideState => {
  return Object.assign(
    {
      users: [],
      usersLoading: true,
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
    },
    overrideState,
  );
};

describe("user reducer", () => {
  it("should return the initial state", () => {
    expect(userReducer(undefined, {})).toEqual({
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
    });
  });

  it("should handle FETCH_USERS_BEGIN", () => {
    const initialState = setupState({
      usersLoading: false,
      usersError: "previousError",
    });
    const action = { type: types.FETCH_USERS_BEGIN };
    const newState = userReducer(initialState, action);
    expect(newState.users).toEqual([]);
    expect(newState.usersLoading).toBe(true);
    expect(newState.usersError).toBeNull();
  });

  it("should handle FETCH_USERS_SUCCESS", () => {
    const initialState = setupState({
      usersLoading: true,
      usersError: "previousError",
    });
    const action = {
      type: types.FETCH_USERS_SUCCESS,
      payload: { users: ["user1"] },
    };
    const newState = userReducer(initialState, action);
    expect(newState.users).toEqual(["user1"]);
    expect(newState.usersLoading).toBe(false);
    expect(newState.usersError).toBeNull();
  });

  it("should handle FETCH_USERS_FAILURE", () => {
    const initialState = setupState({
      usersLoading: true,
    });
    const action = {
      type: types.FETCH_USERS_FAILURE,
      payload: { error: new Error("someError") },
    };
    const newState = userReducer(initialState, action);
    expect(newState.users).toEqual([]);
    expect(newState.usersLoading).toBe(false);
    expect(newState.usersError).not.toBeNull();
  });

  it("should handle FETCH_USER_BEGIN", () => {
    const initialState = setupState({
      userLoading: false,
      userError: "not null",
      selectedUser: { foo: "bar" },
    });
    const action = { type: types.FETCH_USER_BEGIN };
    const newState = userReducer(initialState, action);
    expect(newState.userLoading).toBe(true);
    expect(newState.userError).toBeNull();
    expect(newState.selectedUser).toEqual({});
  });

  it("should handle FETCH_USER_SUCCESS", () => {
    const initialState = setupState({
      userLoading: true,
      userError: null,
      selectedUser: {},
    });
    const action = {
      type: types.FETCH_USER_SUCCESS,
      payload: { user: "user1" },
    };
    const newState = userReducer(initialState, action);
    expect(newState.userLoading).toBe(false);
    expect(newState.userError).toBeNull();
    expect(newState.selectedUser).toEqual("user1");
  });

  it("should handle FETCH_USER_FAILURE", () => {
    const initialState = setupState({
      userLoading: true,
      userError: null,
      selectedUser: {},
    });
    const action = {
      type: types.FETCH_USER_FAILURE,
      payload: { error: new Error("Error fetching") },
    };
    const newState = userReducer(initialState, action);
    expect(newState.userLoading).toBe(false);
    expect(newState.userError).not.toBeNull();
    expect(newState.selectedUser).toEqual({});
  });

  it("should handle CREATE_USER_BEGIN", () => {
    const initialState = setupState({
      createUserLoading: false,
      createUserError: "previous error",
    });
    const action = {
      type: types.CREATE_USER_BEGIN,
    };
    const newState = userReducer(initialState, action);
    expect(newState.createUserLoading).toBe(true);
    expect(newState.createUserError).toBeNull();
  });

  it("should handle CREATE_USER_SUCCESS", () => {
    const initialState = setupState({
      users: [],
      createUserLoading: true,
      createUserError: null,
    });
    const action = {
      type: types.CREATE_USER_SUCCESS,
      payload: { user: "user1" },
    };
    const newState = userReducer(initialState, action);
    expect(newState.createUserLoading).toBe(false);
    expect(newState.createUserError).toBeNull();
    expect(newState.users).toEqual(["user1"]);
  });

  it("should handle CREATE_USER_FAILURE", () => {
    const initialState = setupState({
      createUserLoading: true,
      createUserError: null,
    });
    const action = {
      type: types.CREATE_USER_FAILURE,
      payload: { error: new Error("create error") },
    };
    const newState = userReducer(initialState, action);
    expect(newState.createUserLoading).toBe(false);
    expect(newState.createUserError).not.toBeNull();
  });

  it("should handle DELETE_USER_BEGIN", () => {
    const initialState = setupState({
      deleteUserLoading: false,
      deleteUserError: "previous error",
    });
    const action = {
      type: types.DELETE_USER_BEGIN,
    };
    const newState = userReducer(initialState, action);
    expect(newState.deleteUserLoading).toBe(true);
    expect(newState.deleteUserError).toBeNull();
  });

  it("should handle DELETE_USER_SUCCESS when loaded", () => {
    const initialState = setupState({
      users: [{ id: "userId" }],
      deleteUserLoading: true,
      deleteUserError: null,
    });
    const action = {
      type: types.DELETE_USER_SUCCESS,
      payload: "userId",
    };
    const newState = userReducer(initialState, action);
    expect(newState.deleteUserLoading).toBe(false);
    expect(newState.deleteUserError).toBeNull();
    expect(newState.users).toEqual([]);
  });

  it("should handle DELETE_USER_SUCCESS when not loaded", () => {
    const initialState = setupState({
      users: [],
      deleteUserLoading: true,
      deleteUserError: null,
    });
    const action = {
      type: types.DELETE_USER_SUCCESS,
      payload: "userId",
    };
    const newState = userReducer(initialState, action);
    expect(newState.deleteUserLoading).toBe(false);
    expect(newState.deleteUserError).toBeNull();
    expect(newState.users).toEqual([]);
  });

  it("should handle DELETE_USER_FAILURE", () => {
    const initialState = setupState({
      deleteUserLoading: true,
      deleteUserError: null,
    });
    const action = {
      type: types.DELETE_USER_FAILURE,
      payload: { error: new Error("create error") },
    };
    const newState = userReducer(initialState, action);
    expect(newState.deleteUserLoading).toBe(false);
    expect(newState.deleteUserError).not.toBeNull();
  });

  it("should handle UPDATE_USER_BEGIN", () => {
    const initialState = setupState({
      updateUserLoading: false,
      updateUserError: "previous error",
    });
    const action = {
      type: types.UPDATE_USER_BEGIN,
    };
    const newState = userReducer(initialState, action);
    expect(newState.updateUserLoading).toBe(true);
    expect(newState.updateUserError).toBeNull();
  });

  it("should handle UPDATE_USER_SUCCESS when loaded", () => {
    const initialState = setupState({
      users: [{ id: "userId", username: "newName" }],
      updateUserLoading: true,
      updateUserError: null,
    });
    const action = {
      type: types.UPDATE_USER_SUCCESS,
      payload: { id: "userId", username: "newName" },
    };
    const newState = userReducer(initialState, action);
    expect(newState.updateUserLoading).toBe(false);
    expect(newState.updateUserError).toBeNull();
    expect(newState.users).toEqual([{ id: "userId", username: "newName" }]);
  });

  it("should handle UPDATE_USER_SUCCESS when not loaded", () => {
    const initialState = setupState({
      users: [],
      updateUserLoading: true,
      updateUserError: null,
    });
    const action = {
      type: types.UPDATE_USER_SUCCESS,
      payload: { id: "userId", username: "newName" },
    };
    const newState = userReducer(initialState, action);
    expect(newState.updateUserLoading).toBe(false);
    expect(newState.updateUserError).toBeNull();
    expect(newState.users).toEqual([]);
  });

  it("should handle UPDATE_USER_FAILURE", () => {
    const initialState = setupState({
      updateUserLoading: true,
      updateUserError: null,
    });
    const action = {
      type: types.UPDATE_USER_FAILURE,
      payload: { error: new Error("create error") },
    };
    const newState = userReducer(initialState, action);
    expect(newState.updateUserLoading).toBe(false);
    expect(newState.updateUserError).not.toBeNull();
  });
});
