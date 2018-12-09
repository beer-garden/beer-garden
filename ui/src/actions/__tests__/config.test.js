import configureMockStore from 'redux-mock-store';
import thunk from 'redux-thunk';
import camelcaseKeys from 'camelcase-keys';
import * as actions from '../config';
import * as types from '../../constants/ActionTypes';
import fetchMock from 'fetch-mock';

const middlewares = [thunk];
const mockStore = configureMockStore(middlewares);
const serverConfig = {
  allow_unsafe_templates: false,
  application_name: 'Beer Garden',
  amq_admin_port: 15672,
  amq_host: 'rabbitmq',
  amq_port: 5672,
  amq_virtual_host: '/',
  backend_host: 'bartender',
  backend_port: 9090,
  icon_default: 'fa-beer',
  debug_mode: false,
  url_prefix: '/',
  metrics_url: 'http://localhost:3000',
  auth_enabled: false,
};

const setup = (initialState, succeeds = true) => {
  let response;
  Object.assign({}, initialState);
  if (succeeds) {
    response = {
      body: serverConfig,
      headers: { 'content-type': 'application/json' },
    };
  } else {
    response = 500;
  }
  fetchMock.mock('/config', response);
  const store = mockStore(initialState);
  return {
    store,
    response,
  };
};

describe('async actions', () => {
  afterEach(() => {
    fetchMock.restore();
  });

  test('it creates FETCH_CONFIG_SUCCESS when fetching config is done', () => {
    const { store } = setup();

    const expectedConfig = camelcaseKeys(serverConfig);

    const expectedActions = [
      { type: types.FETCH_CONFIG_BEGIN },
      { type: types.FETCH_CONFIG_SUCCESS, payload: { config: expectedConfig } },
    ];
    return store.dispatch(actions.loadConfig()).then(() => {
      expect(store.getActions()).toEqual(expectedActions);
    });
  });

  test('it should not create an action if the config already exists', () => {
    const { store } = setup({ config: 'alreadyLoaded' });
    expect(store.dispatch(actions.loadConfig())).toBe(null);
  });

  test('it should create an action if the config is an empty object', () => {
    const { store } = setup({ config: {} });
    const expectedConfig = camelcaseKeys(serverConfig);

    const expectedActions = [
      { type: types.FETCH_CONFIG_BEGIN },
      { type: types.FETCH_CONFIG_SUCCESS, payload: { config: expectedConfig } },
    ];
    return store.dispatch(actions.loadConfig()).then(() => {
      expect(store.getActions()).toEqual(expectedActions);
    });
  });

  test('it should create a failed action if the fetch fails', () => {
    const { store } = setup({}, false);
    const expectedActions = [
      { type: types.FETCH_CONFIG_BEGIN },
      {
        type: types.FETCH_CONFIG_FAILURE,
        payload: { error: Error('Internal Server Error') },
      },
    ];
    return store.dispatch(actions.loadConfig()).then(() => {
      expect(store.getActions()).toEqual(expectedActions);
    });
  });
});
