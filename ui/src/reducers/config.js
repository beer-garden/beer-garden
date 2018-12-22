import {
  FETCH_CONFIG_BEGIN,
  FETCH_CONFIG_SUCCESS,
  FETCH_CONFIG_FAILURE,
} from "../constants/ActionTypes";

const initialState = {
  config: {},
  configLoading: true,
  configError: null,
};

export default function configReducer(state = initialState, action) {
  switch (action.type) {
    case FETCH_CONFIG_BEGIN:
      // Do not reset the error. This call only happens once at application
      // configuration loading. Because of that, if an error occurs, we retry
      // and don't want to unset the last error since the app simply cannot
      // load if no configuration is returned.
      return {
        ...state,
        configLoading: true,
      };

    case FETCH_CONFIG_SUCCESS:
      return {
        ...state,
        configLoading: false,
        configError: null,
        config: action.payload.config,
      };

    case FETCH_CONFIG_FAILURE:
      return {
        ...state,
        configLoading: false,
        configError: action.payload.error,
        config: {},
      };

    default:
      return state;
  }
}
