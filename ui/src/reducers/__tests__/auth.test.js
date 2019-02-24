import authReducer from "../auth";
import * as types from "../../constants/ActionTypes";

describe("auth reducer", () => {
  it("should return the initial state", () => {
    expect(authReducer(undefined, {})).toEqual({
      userData: {},
      isAuthenticated: false,
      isAnonymous: false,
      isProtected: false,
      userLoading: false,
      userError: null,
    });
  });

  it("should handle USER_LOGIN_BEGIN", () => {
    expect(
      authReducer(
        {
          userData: "oldData",
          isAuthenticated: true,
          isAnonymous: false,
          isProtected: false,
          userLoading: false,
          userError: null,
        },
        {
          type: types.USER_LOGIN_BEGIN,
        },
      ),
    ).toEqual({
      userData: {},
      isAuthenticated: true,
      isAnonymous: false,
      isProtected: false,
      userLoading: true,
      userError: null,
    });
  });

  it("should handle USER_LOGIN_SUCCESS", () => {
    expect(
      authReducer(
        {},
        {
          type: types.USER_LOGIN_SUCCESS,
          payload: { data: { username: "someUser" } },
        },
      ),
    ).toEqual({
      userData: { username: "someUser" },
      isProtected: false,
      isAnonymous: false,
      userLoading: false,
      isAuthenticated: true,
      userError: null,
    });
  });

  it("should set isProtected for the admin user", () => {
    const action = {
      type: types.USER_LOGIN_SUCCESS,
      payload: { data: { username: "admin" } },
    };
    const newState = authReducer({}, action);
    expect(newState.isProtected).toBe(true);
    expect(newState.isAnonymous).toBe(false);
  });

  it("should set isProtected and isAnonymous for the anon user", () => {
    const action = {
      type: types.USER_LOGIN_SUCCESS,
      payload: { data: { username: "anonymous" } },
    };
    const newState = authReducer({}, action);
    expect(newState.isProtected).toBe(true);
    expect(newState.isAnonymous).toBe(true);
  });

  it("should handle USER_LOGIN_FAILURE", () => {
    const error = new Error("errorMessage");
    expect(
      authReducer(
        {},
        {
          type: types.USER_LOGIN_FAILURE,
          payload: { error: error },
        },
      ),
    ).toEqual({
      userData: {},
      isProtected: false,
      isAnonymous: false,
      isAuthenticated: false,
      userLoading: false,
      userError: error,
    });
  });

  it("should handle USER_LOGOUT_BEGIN", () => {
    expect(authReducer({}, { type: types.USER_LOGOUT_BEGIN })).toEqual({
      userLoading: true,
    });
  });

  it("should handle USER_LOGOUT_FAILURE", () => {
    const error = new Error("error");
    expect(
      authReducer({}, { type: types.USER_LOGOUT_FAILURE, payload: { error } }),
    ).toEqual({
      userLoading: false,
      userError: error,
    });
  });

  it("should handle USER_LOGOUT_SUCCESS", () => {
    expect(authReducer({}, { type: types.USER_LOGOUT_SUCCESS })).toEqual({
      userData: {},
      isAuthenticated: false,
      isAnonymous: false,
      isProtected: false,
      userLoading: false,
      userError: null,
    });
  });
});
