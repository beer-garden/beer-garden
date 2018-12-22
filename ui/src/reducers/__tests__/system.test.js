import systemReducer from "../system";
import * as types from "../../constants/ActionTypes";

const setupState = overrideState => {
  const state = Object.assign(
    {
      systems: [],
      systemsLoading: true,
      systemsError: null,
      selectedSystem: null,
    },
    overrideState,
  );
  return state;
};

describe("system reducer", () => {
  it("should return the initial state", () => {
    expect(systemReducer(undefined, {})).toEqual({
      systems: [],
      systemsLoading: true,
      systemsError: null,
      selectedSystem: null,
    });
  });

  it("should handle FETCH_SYSTEMS_BEGIN", () => {
    const initialState = setupState({
      systemsLoading: false,
      systemsError: "previousError",
    });
    const action = { type: types.FETCH_SYSTEMS_BEGIN };
    const newState = systemReducer(initialState, action);
    expect(newState).toEqual({
      systems: [],
      systemsLoading: true,
      systemsError: null,
      selectedSystem: null,
    });
  });

  it("should handle FETCH_SYSTEMS_SUCCESS", () => {
    const initialState = setupState({
      systemsLoading: true,
      systemsError: "previousError",
    });
    const action = {
      type: types.FETCH_SYSTEMS_SUCCESS,
      payload: { systems: ["system1"] },
    };
    const newState = systemReducer(initialState, action);
    expect(newState).toEqual({
      systems: ["system1"],
      systemsLoading: false,
      systemsError: null,
      selectedSystem: null,
    });
  });

  it("should handle FETCH_SYSTEMS_FAILURE", () => {
    const initialState = setupState({
      systemsLoading: true,
    });
    const action = {
      type: types.FETCH_SYSTEMS_FAILURE,
      payload: { error: new Error("someError") },
    };
    const newState = systemReducer(initialState, action);
    expect(newState).toEqual({
      systems: [],
      systemsLoading: false,
      systemsError: new Error("someError"),
      selectedSystem: null,
    });
  });
});
