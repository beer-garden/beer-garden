import authReducer from "../auth";
import * as types from "../../constants/ActionTypes";

describe("auth reducer", () => {
  it("should return the initial state", () => {
    expect(authReducer(undefined, {})).toEqual({
      userData: {},
      isAuthenticated: false,
      isGuest: false,
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
          isGuest: false,
          userLoading: false,
          userError: null,
        },
        {
          type: types.USER_LOGIN_BEGIN,
        },
      ),
    ).toEqual({
      userData: {},
      isAuthenticated: false,
      isGuest: false,
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
          payload: { isGuest: false, data: "dataFromServer" },
        },
      ),
    ).toEqual({
      userData: "dataFromServer",
      userLoading: false,
      isAuthenticated: true,
      isGuest: false,
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
      isGuest: false,
      userLoading: false,
      userError: error,
    });
  });
});
