import { combineReducers } from "redux";
import authReducer from "./auth";
import configReducer from "./config";
import systemReducer from "./system";
import themeReducer from "./theme";
import userReducer from "./user";
import versionReducer from "./version";

export default combineReducers({
  authReducer,
  configReducer,
  systemReducer,
  themeReducer,
  userReducer,
  versionReducer,
});
