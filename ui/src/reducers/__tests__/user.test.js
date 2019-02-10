import userReducer from "../user";
import * as types from "../../constants/ActionTypes";

const setupState = overrideState => {
  const state = Object.assign(
    {
      users: [],
      usersLoading: true,
      usersError: null,
    },
    overrideState,
  );
  return state;
};

describe("user reducer", () => {
  it("should return the initial state", () => {
    expect(userReducer(undefined, {})).toEqual({
      users: [],
      usersLoading: false,
      usersError: null,
    });
  });

  it("should handle FETCH_USERS_BEGIN", () => {
    const initialState = setupState({
      usersLoading: false,
      usersError: "previousError",
    });
    const action = { type: types.FETCH_USERS_BEGIN };
    const newState = userReducer(initialState, action);
    expect(newState).toEqual({
      users: [],
      usersLoading: true,
      usersError: null,
    });
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
    expect(newState).toEqual({
      users: ["user1"],
      usersLoading: false,
      usersError: null,
    });
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
    expect(newState).toEqual({
      users: [],
      usersLoading: false,
      usersError: new Error("someError"),
    });
  });
});
