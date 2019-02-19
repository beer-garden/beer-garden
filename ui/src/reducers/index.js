import { combineReducers } from "redux";
import authReducer from "./auth";
import configReducer from "./config";
import roleReducer from "./role";
import systemReducer from "./system";
import themeReducer from "./theme";
import userReducer from "./user";
import versionReducer from "./version";

export default combineReducers({
  authReducer,
  configReducer,
  roleReducer,
  systemReducer,
  themeReducer,
  userReducer,
  versionReducer,
});
