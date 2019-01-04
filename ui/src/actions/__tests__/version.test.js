import versionureMockStore from "redux-mock-store";
import thunk from "redux-thunk";
import camelcaseKeys from "camelcase-keys";
import { loadVersion } from "../version";
import * as types from "../../constants/ActionTypes";
import axios from "axios";
import MockAdapter from "axios-mock-adapter";

const middlewares = [thunk];
const mockStore = versionureMockStore(middlewares);
const serverResponse = {
  brew_view_version: "3.0.0",
  bartender_version: "3.0.0",
  current_api_version: "v1",
  supported_api_verisons: ["v1"],
};
const fetchMock = new MockAdapter(axios);

const setup = (initialState, serverError = false, networkError = false) => {
  const state = Object.assign({}, initialState);
  const url = "/version";
  if (networkError) {
    fetchMock.onGet(url).networkError();
  } else if (serverError) {
    fetchMock.onGet(url).reply(500, { message: "Error from server" });
  } else {
    fetchMock.onGet(url).reply(200, serverResponse);
  }

  const store = mockStore({ versionReducer: state });
  return {
    store,
  };
};

describe("version actions", () => {
  afterEach(() => {
    fetchMock.reset();
  });

  test("it creates FETCH_VERSION_SUCCESS when fetching version is done", () => {
    const { store } = setup();

    const expectedResult = camelcaseKeys(serverResponse);

    const expectedActions = [
      { type: types.FETCH_VERSION_BEGIN },
      {
        type: types.FETCH_VERSION_SUCCESS,
        payload: { version: expectedResult },
      },
    ];
    return store.dispatch(loadVersion()).then(() => {
      expect(store.getActions()).toEqual(expectedActions);
    });
  });

  test("it should not create an action if the version already exists", () => {
    const { store } = setup({ version: "alreadyLoaded" });
    expect(store.dispatch(loadVersion())).toBe(null);
  });

  test("it should create an action if the version is an empty object", () => {
    const { store } = setup({ version: {} });
    const expectedResult = camelcaseKeys(serverResponse);

    const expectedActions = [
      { type: types.FETCH_VERSION_BEGIN },
      {
        type: types.FETCH_VERSION_SUCCESS,
        payload: { version: expectedResult },
      },
    ];
    return store.dispatch(loadVersion()).then(() => {
      expect(store.getActions()).toEqual(expectedActions);
    });
  });

  test("it should create a failed action if the fetch fails", () => {
    const { store } = setup({}, true, false);
    const expectedActions = [
      { type: types.FETCH_VERSION_BEGIN },
      {
        type: types.FETCH_VERSION_FAILURE,
        payload: { error: Error("Error from server") },
      },
    ];
    return store.dispatch(loadVersion()).then(() => {
      expect(store.getActions()).toEqual(expectedActions);
    });
  });

  test("it should handle network failures gracefully", () => {
    const { store } = setup({}, false, true);
    return store.dispatch(loadVersion()).then(() => {
      const actions = store.getActions();
      expect(actions).toHaveLength(2);
      expect(actions[0].type).toEqual(types.FETCH_VERSION_BEGIN);
      expect(actions[1].type).toEqual(types.FETCH_VERSION_FAILURE);
      expect(actions[1].payload.error).toHaveProperty("message");
    });
  });
});
