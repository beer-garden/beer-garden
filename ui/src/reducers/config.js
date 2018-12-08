import {
  FETCH_CONFIG_BEGIN,
  FETCH_CONFIG_SUCCESS,
  FETCH_CONFIG_FAILURE,
} from '../constants/ActionTypes';

const initialState = {
  config: {},
  configLoading: false,
  configError: null,
};

export default function configReducer(state = initialState, action) {
  switch (action.type) {
    case FETCH_CONFIG_BEGIN:
      // Mark the state as loading so we can show a spinner or something
      // Also reset any errors. We're starting fresh.
      return {
        ...state,
        configLoading: true,
      };

    case FETCH_CONFIG_SUCCESS:
      // All done: set loading "false"
      // Also replace the items with ones from the server
      return {
        ...state,
        configLoading: false,
        configError: null,
        config: action.payload.config,
      };

    case FETCH_CONFIG_FAILURE:
      // The request failed, but it did stop, so set loading to "false"
      // Save the error, and we can display it somewhere.
      console.log('something went wrong...');
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
