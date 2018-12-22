import { SET_USER_THEME } from "../constants/ActionTypes";

export const setUserTheme = name => ({
  type: SET_USER_THEME,
  payload: name,
});
