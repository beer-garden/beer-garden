import { SET_USER_THEME } from "../constants/ActionTypes";
import { THEMES } from "../constants/themes";

const getInitialState = () => {
  let themeName = localStorage.getItem("themeName", "light");
  if (!THEMES.hasOwnProperty(themeName)) {
    themeName = "light";
  }
  localStorage.setItem("themeName", themeName);
  return {
    themeName,
    theme: THEMES[themeName],
  };
};

export default function themeReducer(state = getInitialState(), action) {
  switch (action.type) {
    case SET_USER_THEME:
      localStorage.setItem("themeName", action.payload);
      return { themeName: action.payload, theme: THEMES[action.payload] };
    default:
      return state;
  }
}
