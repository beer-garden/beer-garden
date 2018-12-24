import configureMockStore from "redux-mock-store";
import thunk from "redux-thunk";
import { basicLogin, logout } from "../auth";
import * as types from "../../constants/ActionTypes";
import axios from "axios";
import MockAdapter from "axios-mock-adapter";

const middlewares = [thunk];
const mockStore = configureMockStore(middlewares);
const fetchMock = new MockAdapter(axios);
const serverResponse = {
  token: "tokenHash",
  refresh: "refreshHash",
};

const basicAuthSetup = (
  initialState,
  serverError = false,
  networkError = false,
) => {
  Object.assign({}, initialState);
  const url = "/api/v1/tokens";
  if (networkError) {
    fetchMock.onPost(url).networkError();
    fetchMock.onDelete(url).networkError();
  } else if (serverError) {
    fetchMock.onPost(url).reply(500, { message: "Error from server" });
    fetchMock.onDelete(url).reply(500, { message: "Error from server" });
  } else {
    fetchMock.onPost(url).reply(200, serverResponse);
    fetchMock.onDelete(url).reply(200, {});
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

  describe("basicLogin", () => {
    test("it creates the expected actions on success", () => {
      const { store } = basicAuthSetup();

      const expectedActions = [
        { type: types.USER_LOGIN_BEGIN },
        {
          type: types.USER_LOGIN_SUCCESS,
          payload: { data: serverResponse, isGuest: false },
        },
      ];
      store.dispatch(basicLogin("username", "password")).then(() => {
        expect(store.getActions()).toEqual(expectedActions);
      });
    });

    test("it creates the expected actions on failure", () => {
      const { store } = basicAuthSetup({}, true);

      store.dispatch(basicLogin("username", "password")).then(() => {
        const actions = store.getActions();
        expect(actions).toHaveLength(2);
        expect(actions[0].type).toEqual(types.USER_LOGIN_BEGIN);
        expect(actions[1].type).toEqual(types.USER_LOGIN_FAILURE);
      });
    });
  });

  describe("logout", () => {
    test("it creates the expected actions on success", () => {
      const { store } = basicAuthSetup();
      store.dispatch(logout()).then(() => {
        const actions = store.getActions();
        expect(actions).toHaveLength(2);
        expect(actions[0].type).toEqual(types.USER_LOGOUT_BEGIN);
        expect(actions[1].type).toEqual(types.USER_LOGOUT_SUCCESS);
      });
    });

    test("it creates the expeced actions on failure", () => {
      const { store } = basicAuthSetup({}, true);

      store.dispatch(logout()).then(() => {
        const actions = store.getActions();
        expect(actions).toHaveLength(2);
        expect(actions[0].type).toEqual(types.USER_LOGOUT_BEGIN);
        expect(actions[1].type).toEqual(types.USER_LOGOUT_FAILURE);
      });
    });
  });
});
