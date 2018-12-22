import configureMockStore from "redux-mock-store";
import thunk from "redux-thunk";
import camelcaseKeys from "camelcase-keys";
import { loadConfig } from "../config";
import * as types from "../../constants/ActionTypes";
import axios from "axios";
import MockAdapter from "axios-mock-adapter";

const middlewares = [thunk];
const mockStore = configureMockStore(middlewares);
const serverConfig = {
  allow_unsafe_templates: false,
  application_name: "Beer Garden",
  amq_admin_port: 15672,
  amq_host: "rabbitmq",
  amq_port: 5672,
  amq_virtual_host: "/",
  backend_host: "bartender",
  backend_port: 9090,
  icon_default: "fa-beer",
  debug_mode: false,
  url_prefix: "/",
  metrics_url: "http://localhost:3000",
  auth_enabled: false,
};
const fetchMock = new MockAdapter(axios);

const setup = (initialState, serverError = false, networkError = false) => {
  Object.assign({}, initialState);
  const url = "/config";
  if (networkError) {
    fetchMock.onGet(url).networkError();
  } else if (serverError) {
    fetchMock.onGet(url).reply(500, { message: "Error from server" });
  } else {
    fetchMock.onGet(url).reply(200, serverConfig);
  }

  const store = mockStore(initialState);
  return {
    store,
  };
};

describe("async actions", () => {
  afterEach(() => {
    fetchMock.reset();
  });

  test("it creates FETCH_CONFIG_SUCCESS when fetching config is done", () => {
    const { store } = setup();

    const expectedConfig = camelcaseKeys(serverConfig);

    const expectedActions = [
      { type: types.FETCH_CONFIG_BEGIN },
      { type: types.FETCH_CONFIG_SUCCESS, payload: { config: expectedConfig } },
    ];
    return store.dispatch(loadConfig()).then(() => {
      expect(store.getActions()).toEqual(expectedActions);
    });
  });

  test("it should not create an action if the config already exists", () => {
    const { store } = setup({ config: "alreadyLoaded" });
    expect(store.dispatch(loadConfig())).toBe(null);
  });

  test("it should create an action if the config is an empty object", () => {
    const { store } = setup({ config: {} });
    const expectedConfig = camelcaseKeys(serverConfig);

    const expectedActions = [
      { type: types.FETCH_CONFIG_BEGIN },
      { type: types.FETCH_CONFIG_SUCCESS, payload: { config: expectedConfig } },
    ];
    return store.dispatch(loadConfig()).then(() => {
      expect(store.getActions()).toEqual(expectedActions);
    });
  });

  test("it should create a failed action if the fetch fails", () => {
    const { store } = setup({}, true, false);
    const expectedActions = [
      { type: types.FETCH_CONFIG_BEGIN },
      {
        type: types.FETCH_CONFIG_FAILURE,
        payload: { error: Error("Error from server") },
      },
    ];
    return store.dispatch(loadConfig()).then(() => {
      expect(store.getActions()).toEqual(expectedActions);
    });
  });

  test("it should handle network failures gracefully", () => {
    const { store } = setup({}, false, true);
    return store.dispatch(loadConfig()).then(() => {
      const actions = store.getActions();
      expect(actions).toHaveLength(2);
      expect(actions[0].type).toEqual(types.FETCH_CONFIG_BEGIN);
      expect(actions[1].type).toEqual(types.FETCH_CONFIG_FAILURE);
      expect(actions[1].payload.error).toHaveProperty("message");
    });
  });
});
