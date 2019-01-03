import authReducer from "../auth";
import * as types from "../../constants/ActionTypes";

describe("auth reducer", () => {
  it("should return the initial state", () => {
    expect(authReducer(undefined, {})).toEqual({
      userData: {},
      isAuthenticated: false,
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
          payload: { data: "dataFromServer" },
        },
      ),
    ).toEqual({
      userData: "dataFromServer",
      userLoading: false,
      isAuthenticated: true,
      userError: null,
    });
  });

  it("should handle USER_LOGIN_FAILURE", () => {
    const error = new Error("errorMessagej");
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
      userLoading: false,
      userError: null,
    });
  });
});
