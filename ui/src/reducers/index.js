import { combineReducers } from "redux";
import configReducer from "./config";
import authReducer from "./auth";
import systemReducer from "./system";

export default combineReducers({
  configReducer,
  authReducer,
  systemReducer,
});
