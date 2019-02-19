import configureMockStore from "redux-mock-store";
import thunk from "redux-thunk";
import camelcaseKeys from "camelcase-keys";
import {
  createUser,
  fetchUsers,
  fetchUser,
  deleteUser,
  getUser,
} from "../user";
import * as types from "../../constants/ActionTypes";
import axios from "axios";
import MockAdapter from "axios-mock-adapter";

const middlewares = [thunk];
const mockStore = configureMockStore(middlewares);
const serverResponse = [
  {
    roles: [
      {
        name: "bg-admin",
        roles: [],
        permissions: ["bg-all"],
        description: "Allows all actions",
        id: "5c4e1bc591e42613a679bcb8",
      },
    ],
    permissions: ["bg-all"],
    preferences: { auto_change: true, changed: false },
    username: "admin",
    id: "5c4e1bc691e42613a679bcba",
  },
  {
    roles: [
      {
        name: "bg-anonymous",
        roles: [],
        permissions: [
          "bg-command-read",
          "bg-event-read",
          "bg-instance-read",
          "bg-job-read",
          "bg-queue-read",
          "bg-request-read",
          "bg-system-read",
        ],
        description: "Special role used for non-authenticated users",
        id: "5c4e1bc591e42613a679bcb7",
      },
    ],
    permissions: [
      "bg-instance-read",
      "bg-request-read",
      "bg-event-read",
      "bg-system-read",
      "bg-job-read",
      "bg-queue-read",
      "bg-command-read",
    ],
    preferences: {},
    username: "anonymous",
    id: "5c4e1bc691e42613a679bcbb",
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
  const url = "/api/v1/users";
  const singleUrl = "/api/v1/users/username";
  const idUrl = "/api/v1/users/userId";
  if (networkError) {
    fetchMock.onGet(url).networkError();
    fetchMock.onGet(singleUrl).networkError();
    fetchMock.onDelete(idUrl).networkError();
    fetchMock.onPost(url).networkError();
  } else if (serverError) {
    fetchMock.onGet(url).reply(status, { message: "Error from server" });
    fetchMock.onGet(singleUrl).reply(status, { message: "Error from server" });
    fetchMock.onDelete(idUrl).reply(status, { message: "Error from server" });
    fetchMock.onPost(url).reply(status, { message: "Error from server" });
  } else {
    fetchMock.onGet(url).reply(200, serverResponse);
    fetchMock.onGet(singleUrl).reply(200, serverResponse[0]);
    fetchMock.onDelete(idUrl).reply(204, null);
    fetchMock.onPost(url).reply(201, serverResponse[0]);
  }

  const store = mockStore({ userReducer: initialState });
  return {
    store,
  };
};

describe("user actions", () => {
  afterEach(() => {
    fetchMock.reset();
  });

  it("should create a FETCH_USERS_SUCCESS when fetching users is done", () => {
    const { store } = setup();

    const expectedResponse = camelcaseKeys(serverResponse);

    const expectedActions = [
      { type: types.FETCH_USERS_BEGIN },
      {
        type: types.FETCH_USERS_SUCCESS,
        payload: { users: expectedResponse },
      },
    ];
    return store.dispatch(fetchUsers()).then(() => {
      expect(store.getActions()).toEqual(expectedActions);
    });
  });

  it("should create a failed action if the fetch fails", () => {
    const { store } = setup({}, true, false);
    const expectedActions = [
      { type: types.FETCH_USERS_BEGIN },
      {
        type: types.FETCH_USERS_FAILURE,
        payload: { error: Error("Error from server") },
      },
    ];
    return store.dispatch(fetchUsers()).then(() => {
      expect(store.getActions()).toEqual(expectedActions);
    });
  });

  it("should trigger the correct actions on fetch", () => {
    const { store } = setup();
    const expectedResponse = camelcaseKeys(serverResponse[0]);
    const expectedActions = [
      { type: types.FETCH_USER_BEGIN },
      {
        type: types.FETCH_USER_SUCCESS,
        payload: { user: expectedResponse },
      },
    ];
    return store.dispatch(fetchUser("username")).then(() => {
      expect(store.getActions()).toEqual(expectedActions);
    });
  });

  it("should trigger the correct actions on fetchUser failure", () => {
    const { store } = setup({}, true, false);
    const expectedActions = [
      { type: types.FETCH_USER_BEGIN },
      {
        type: types.FETCH_USER_FAILURE,
        payload: { error: Error("Error from server") },
      },
    ];
    return store.dispatch(fetchUser("username")).then(() => {
      expect(store.getActions()).toEqual(expectedActions);
    });
  });

  it("should not trigger any actions on getUser if the user already exists", () => {
    const expectedUser = { username: "username", foo: "bar" };
    const { store } = setup({ users: [expectedUser] });
    const expectedAction = {
      type: types.FETCH_USER_SUCCESS,
      payload: { user: expectedUser },
    };
    expect(store.dispatch(getUser("username"))).toEqual(expectedAction);
  });

  it("should trigger begin/success if getUser returns nothing", () => {
    const { store } = setup({ users: [] });
    const expectedResponse = camelcaseKeys(serverResponse[0]);
    const expectedActions = [
      { type: types.FETCH_USER_BEGIN },
      {
        type: types.FETCH_USER_SUCCESS,
        payload: { user: expectedResponse },
      },
    ];
    return store.dispatch(getUser("username")).then(() => {
      expect(store.getActions()).toEqual(expectedActions);
    });
  });

  it("should trigger the correct actions on delete user success", () => {
    const { store } = setup();
    const expectedActions = [
      { type: types.DELETE_USER_BEGIN },
      { type: types.DELETE_USER_SUCCESS, payload: "userId" },
    ];
    return store.dispatch(deleteUser("userId")).then(() => {
      expect(store.getActions()).toEqual(expectedActions);
    });
  });

  it("should trigger the correct actions on delete user failure", () => {
    const { store } = setup({}, true, false);
    const expectedActions = [
      { type: types.DELETE_USER_BEGIN },
      {
        type: types.DELETE_USER_FAILURE,
        payload: { error: Error("Error from server") },
      },
    ];
    return store.dispatch(deleteUser("userId")).then(() => {
      expect(store.getActions()).toEqual(expectedActions);
    });
  });

  it("should trigger the correct actions on create user success", () => {
    const { store } = setup();
    const expectedActions = [
      { type: types.CREATE_USER_BEGIN },
      { type: types.CREATE_USER_SUCCESS, payload: { user: serverResponse[0] } },
    ];
    return store
      .dispatch(createUser("username", "password", ["role1", "role2"]))
      .then(() => {
        expect(store.getActions()).toEqual(expectedActions);
      });
  });

  it("should trigger the correct actions on create user failure", () => {
    const { store } = setup({}, true);
    const expectedActions = [
      { type: types.CREATE_USER_BEGIN },
      {
        type: types.CREATE_USER_FAILURE,
        payload: { error: Error("Error from server") },
      },
    ];
    return store
      .dispatch(createUser("username", "password", ["role1", "role2"]))
      .then(() => {
        expect(store.getActions()).toEqual(expectedActions);
      });
  });
});
