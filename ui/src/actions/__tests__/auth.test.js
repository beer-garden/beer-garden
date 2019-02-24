import configureMockStore from "redux-mock-store";
import thunk from "redux-thunk";
import { basicLogin, logout, loadUserData } from "../auth";
import * as types from "../../constants/ActionTypes";
import axios from "axios";
import MockAdapter from "axios-mock-adapter";

const middlewares = [thunk];
const mockStore = configureMockStore(middlewares);
const fetchMock = new MockAdapter(axios);
const encodedToken =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c";
const decodedToken = { iat: 1516239022, name: "John Doe", sub: "1234567890" };
const serverResponse = {
  token: encodedToken,
  refresh: "refreshHash",
};

const basicAuthSetup = (
  initialState,
  serverError = false,
  networkError = false,
  errorCode = 500,
  headers = {},
) => {
  Object.assign({}, initialState);
  const url = "/api/v1/tokens";
  if (networkError) {
    fetchMock.onAny(url).networkError();
  } else if (serverError) {
    fetchMock.onAny(url).reply(errorCode, { message: "Error from server" });
  } else {
    fetchMock.onAny(url).reply(200, serverResponse, headers);
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
          payload: { data: { user: decodedToken, pwChangeRequired: false } },
        },
      ];
      return store.dispatch(basicLogin("username", "password")).then(() => {
        expect(store.getActions()).toEqual(expectedActions);
      });
    });

    test("it creates the expected actions on failure", () => {
      const { store } = basicAuthSetup({}, true);

      return store.dispatch(basicLogin("username", "password")).then(() => {
        const actions = store.getActions();
        expect(actions).toHaveLength(2);
        expect(actions[0].type).toEqual(types.USER_LOGIN_BEGIN);
        expect(actions[1].type).toEqual(types.USER_LOGIN_FAILURE);
      });
    });

    it("should set pwChangeRequired if the header is set", () => {
      const { store } = basicAuthSetup({}, false, false, null, {
        change_password_required: "true",
      });

      const expectedActions = [
        { type: types.USER_LOGIN_BEGIN },
        {
          type: types.USER_LOGIN_SUCCESS,
          payload: { data: { user: decodedToken, pwChangeRequired: true } },
        },
      ];
      return store.dispatch(basicLogin("username", "password")).then(() => {
        expect(store.getActions()).toEqual(expectedActions);
      });
    });
  });

  describe("loadUserData", () => {
    test("it creates the expected actions on success", () => {
      const { store } = basicAuthSetup();

      const expectedActions = [
        { type: types.USER_LOGIN_BEGIN },
        {
          type: types.USER_LOGIN_SUCCESS,
          payload: { data: { user: decodedToken, pwChangeRequired: false } },
        },
      ];
      return store.dispatch(loadUserData()).then(() => {
        expect(store.getActions()).toEqual(expectedActions);
      });
    });

    test("it creates the expected actions on failure", () => {
      const { store } = basicAuthSetup({}, true);

      return store.dispatch(loadUserData()).then(() => {
        const actions = store.getActions();
        expect(actions).toHaveLength(2);
        expect(actions[0].type).toEqual(types.USER_LOGIN_BEGIN);
        expect(actions[1].type).toEqual(types.USER_LOGIN_FAILURE);
      });
    });

    test("it creates only a single aciton on a 401", () => {
      const { store } = basicAuthSetup({}, true, false, 401);

      return store.dispatch(loadUserData()).then(() => {
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
      return store.dispatch(logout()).then(() => {
        const actions = store.getActions();
        expect(actions).toHaveLength(2);
        expect(actions[0].type).toEqual(types.USER_LOGOUT_BEGIN);
        expect(actions[1].type).toEqual(types.USER_LOGOUT_SUCCESS);
      });
    });

    test("it creates the expeced actions on failure", () => {
      const { store } = basicAuthSetup({}, true);

      return store.dispatch(logout()).then(() => {
        const actions = store.getActions();
        expect(actions).toHaveLength(2);
        expect(actions[0].type).toEqual(types.USER_LOGOUT_BEGIN);
        expect(actions[1].type).toEqual(types.USER_LOGOUT_FAILURE);
      });
    });
  });
});
