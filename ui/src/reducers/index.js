import { combineReducers } from "redux";
import configReducer from "./config";
import authReducer from "./auth";
import systemReducer from "./system";
import themeReducer from "./theme";
import versionReducer from "./version";

export default combineReducers({
  configReducer,
  authReducer,
  systemReducer,
  themeReducer,
  versionReducer,
});
