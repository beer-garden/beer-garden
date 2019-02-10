import configureMockStore from "redux-mock-store";
import thunk from "redux-thunk";
import camelcaseKeys from "camelcase-keys";
import { fetchUsers } from "../user";
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

describe("user actions", () => {
  afterEach(() => {
    fetchMock.reset();
  });

  test("it creates FETCH_USERS_SUCCESS when fetching users is done", () => {
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

  test("it should create a failed action if the fetch fails", () => {
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
});
