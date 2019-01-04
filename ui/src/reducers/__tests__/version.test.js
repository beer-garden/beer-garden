import versionReducer from "../version";
import * as types from "../../constants/ActionTypes";

describe("version reducer", () => {
  it("should return the initial state", () => {
    expect(versionReducer(undefined, {})).toEqual({
      version: {},
      versionLoading: true,
      versionError: null,
    });
  });

  it("should handle FETCH_VERSION_BEGIN", () => {
    expect(
      versionReducer(
        { version: {}, versionError: "someError" },
        {
          type: types.FETCH_VERSION_BEGIN,
        },
      ),
    ).toEqual({
      version: {},
      versionLoading: true,
      versionError: null,
    });
  });

  it("should handle FETCH_VERSION_SUCCESS", () => {
    expect(
      versionReducer(
        { version: {}, versionError: "someError", versionLoading: true },
        {
          type: types.FETCH_VERSION_SUCCESS,
          payload: { version: "versionPayload" },
        },
      ),
    ).toEqual({
      version: "versionPayload",
      versionLoading: false,
      versionError: null,
    });
  });

  it("should handle FETCH_VERSION_FAILURE", () => {
    expect(
      versionReducer(
        { version: {}, versionError: null, versionLoading: true },
        {
          type: types.FETCH_VERSION_FAILURE,
          payload: { error: new Error("some error") },
        },
      ),
    ).toEqual({
      version: {},
      versionLoading: false,
      versionError: new Error("some error"),
    });
  });
});
