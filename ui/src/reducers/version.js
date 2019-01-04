import {
  FETCH_VERSION_BEGIN,
  FETCH_VERSION_SUCCESS,
  FETCH_VERSION_FAILURE,
} from "../constants/ActionTypes";

const initialState = {
  version: {},
  versionLoading: true,
  versionError: null,
};

export default function configReducer(state = initialState, action) {
  switch (action.type) {
    case FETCH_VERSION_BEGIN:
      return {
        ...state,
        versionLoading: true,
        versionError: null,
      };

    case FETCH_VERSION_SUCCESS:
      return {
        ...state,
        versionLoading: false,
        versionError: null,
        version: action.payload.version,
      };

    case FETCH_VERSION_FAILURE:
      return {
        ...state,
        versionLoading: false,
        versionError: action.payload.error,
        version: {},
      };

    default:
      return state;
  }
}
