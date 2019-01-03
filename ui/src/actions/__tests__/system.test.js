import configureMockStore from "redux-mock-store";
import thunk from "redux-thunk";
import camelcaseKeys from "camelcase-keys";
import { fetchSystems } from "../system";
import * as types from "../../constants/ActionTypes";
import axios from "axios";
import MockAdapter from "axios-mock-adapter";

const middlewares = [thunk];
const mockStore = configureMockStore(middlewares);
const serverResponse = [
  {
    version: "1.0.0.dev0",
    max_instances: 1,
    metadata: {},
    instances: [],
    commands: [],
    icon_name: null,
    display_name: null,
    description: "Client that echos things",
    name: "echo",
    id: "5c2bc85891e4266cbd5dccee",
  },
];
const fetchMock = new MockAdapter(axios);

const setup = (
  initialState,
  serverError = false,
  networkError = false,
  status = 500,
) => {
  Object.assign({}, initialState);
  const url = "/api/v1/systems";
  if (networkError) {
    fetchMock.onGet(url).networkError();
  } else if (serverError) {
    fetchMock.onGet(url).reply(status, { message: "Error from server" });
  } else {
    fetchMock.onGet(url).reply(200, serverResponse);
  }

  const store = mockStore(initialState);
  return {
    store,
  };
};

describe("system actions", () => {
  afterEach(() => {
    fetchMock.reset();
  });

  test("it creates FETCH_SYSTEMS_SUCCESS when fetching systems is done", () => {
    const { store } = setup();

    const expectedResponse = camelcaseKeys(serverResponse);

    const expectedActions = [
      { type: types.FETCH_SYSTEMS_BEGIN },
      {
        type: types.FETCH_SYSTEMS_SUCCESS,
        payload: { systems: expectedResponse },
      },
    ];
    return store.dispatch(fetchSystems()).then(() => {
      expect(store.getActions()).toEqual(expectedActions);
    });
  });

  test("it should create a failed action if the fetch fails", () => {
    const { store } = setup({}, true, false);
    const expectedActions = [
      { type: types.FETCH_SYSTEMS_BEGIN },
      {
        type: types.FETCH_SYSTEMS_FAILURE,
        payload: { error: Error("Error from server") },
      },
    ];
    return store.dispatch(fetchSystems()).then(() => {
      expect(store.getActions()).toEqual(expectedActions);
    });
  });

  test("it should create different errors for a 401", () => {
    const { store } = setup({}, true, false, 401);
    const expectedActions = [
      { type: types.FETCH_SYSTEMS_BEGIN },
      {
        type: types.USER_LOGIN_FAILURE,
        payload: { error: Error("Error from server") },
      },
      {
        type: types.FETCH_SYSTEMS_FAILURE,
        payload: { error: Error("Error from server") },
      },
    ];
    return store.dispatch(fetchSystems()).then(() => {
      expect(store.getActions()).toEqual(expectedActions);
    });
  });
});
