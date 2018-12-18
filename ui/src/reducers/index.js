import { combineReducers } from 'redux';
import configReducer from './config';
import authReducer from './auth';

export default combineReducers({
  configReducer,
  authReducer,
});
