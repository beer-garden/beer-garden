import configureMockStore from "redux-mock-store";
import thunk from "redux-thunk";
import { basicLogin } from "../auth";
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

const basicLoginSetup = (
  initialState,
  serverError = false,
  networkError = false,
) => {
  Object.assign({}, initialState);
  const url = "/api/v1/tokens";
  if (networkError) {
    fetchMock.onPost(url).networkError();
  } else if (serverError) {
    fetchMock.onPost(url).reply(500, { message: "Error from server" });
  } else {
    fetchMock.onPost(url).reply(200, serverResponse);
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
      const { store } = basicLoginSetup();

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
      const { store } = basicLoginSetup({}, true);

      store.dispatch(basicLogin("username", "password")).then(() => {
        const actions = store.getActions();
        expect(actions).toHaveLength(2);
        expect(actions[0].type).toEqual(types.USER_LOGIN_BEGIN);
        expect(actions[1].type).toEqual(types.USER_LOGIN_FAILURE);
      });
    });
  });
});
