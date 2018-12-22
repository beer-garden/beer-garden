import {
  FETCH_SYSTEMS_BEGIN,
  FETCH_SYSTEMS_SUCCESS,
  FETCH_SYSTEMS_FAILURE,
} from "../constants/ActionTypes";

const initialState = {
  systems: [],
  systemsLoading: true,
  systemsError: null,
  selectedSystem: null,
};

export default function systemReducer(state = initialState, action) {
  switch (action.type) {
    case FETCH_SYSTEMS_BEGIN:
      return {
        ...state,
        systemsError: null,
        systemsLoading: true,
      };

    case FETCH_SYSTEMS_SUCCESS:
      return {
        ...state,
        systemsLoading: false,
        systemsError: null,
        systems: action.payload.systems,
      };

    case FETCH_SYSTEMS_FAILURE:
      return {
        ...state,
        systemsLoading: false,
        systemsError: action.payload.error,
        systems: [],
      };

    default:
      return state;
  }
}
