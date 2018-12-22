import themeReducer from "../theme";
import { THEMES } from "../../constants/themes.js";
import * as types from "../../constants/ActionTypes";

describe("theme reducer", () => {
  it("should return light theme by default", () => {
    expect(themeReducer(undefined, {})).toEqual({
      themeName: "light",
      theme: THEMES["light"],
    });
  });

  it("should default to light if something weird is set", () => {
    localStorage.setItem("themeName", "INVALID");
    expect(themeReducer(undefined, {})).toEqual({
      themeName: "light",
      theme: THEMES["light"],
    });
  });

  it("should handle SET_USER_THEME", () => {
    const newState = themeReducer(undefined, {
      type: types.SET_USER_THEME,
      payload: "dark",
    });
    expect(localStorage.setItem).toHaveBeenCalledWith("themeName", "dark");
    expect(newState.themeName).toEqual("dark");
  });
});
