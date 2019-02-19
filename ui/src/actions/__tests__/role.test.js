import configureMockStore from "redux-mock-store";
import thunk from "redux-thunk";
import camelcaseKeys from "camelcase-keys";
import { fetchRoles, createRole } from "../role";
import * as types from "../../constants/ActionTypes";
import axios from "axios";
import MockAdapter from "axios-mock-adapter";

const middlewares = [thunk];
const mockStore = configureMockStore(middlewares);
const serverResponse = [
  {
    permissions: [
      "bg-command-read",
      "bg-event-read",
      "bg-instance-read",
      "bg-job-read",
      "bg-queue-read",
      "bg-request-read",
      "bg-system-read",
    ],
    name: "bg-readonly",
    id: "5c4e1bc591e42613a679bcb5",
    description: "Allows only standard read actions",
    roles: [],
  },
  {
    permissions: [
      "bg-command-read",
      "bg-event-read",
      "bg-instance-read",
      "bg-job-read",
      "bg-queue-read",
      "bg-request-read",
      "bg-system-read",
      "bg-request-create",
    ],
    name: "bg-operator",
    id: "5c4e1bc591e42613a679bcb6",
    description: "Standard Beergarden user role",
    roles: [],
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
  const url = "/api/v1/roles";
  if (networkError) {
    fetchMock.onGet(url).networkError();
    fetchMock.onPost(url).networkError();
  } else if (serverError) {
    fetchMock.onGet(url).reply(status, { message: "Error from server" });
    fetchMock.onPost(url).reply(status, { message: "Error from server" });
  } else {
    fetchMock.onGet(url).reply(200, serverResponse);
    fetchMock.onPost(url).reply(201, serverResponse[0]);
  }

  const store = mockStore({ roleReducer: initialState });
  return {
    store,
  };
};

describe("role actions", () => {
  afterEach(() => {
    fetchMock.reset();
  });

  it("should trigger the correct actions on fetching roles success", () => {
    const { store } = setup();

    const expectedResponse = camelcaseKeys(serverResponse);

    const expectedActions = [
      { type: types.FETCH_ROLES_BEGIN },
      {
        type: types.FETCH_ROLES_SUCCESS,
        payload: { roles: expectedResponse },
      },
    ];
    return store.dispatch(fetchRoles()).then(() => {
      expect(store.getActions()).toEqual(expectedActions);
    });
  });

  it("should trigger the correct actions on fetcing roles failure", () => {
    const { store } = setup({}, true, false);
    const expectedActions = [
      { type: types.FETCH_ROLES_BEGIN },
      {
        type: types.FETCH_ROLES_FAILURE,
        payload: { error: Error("Error from server") },
      },
    ];
    return store.dispatch(fetchRoles()).then(() => {
      expect(store.getActions()).toEqual(expectedActions);
    });
  });

  it("should trigger the correct actions on create role success", () => {
    const { store } = setup();
    const expectedActions = [
      { type: types.CREATE_ROLE_BEGIN },
      { type: types.CREATE_ROLE_SUCCESS, payload: { role: serverResponse[0] } },
    ];
    return store
      .dispatch(createRole("name", "description", ["perm1", "perm2"]))
      .then(() => {
        expect(store.getActions()).toEqual(expectedActions);
      });
  });

  it("should trigger the correct actions on create role failure", () => {
    const { store } = setup({}, true);
    const expectedActions = [
      { type: types.CREATE_ROLE_BEGIN },
      {
        type: types.CREATE_ROLE_FAILURE,
        payload: { error: Error("Error from server") },
      },
    ];
    return store
      .dispatch(createRole("name", "description", ["perm1", "perm2"]))
      .then(() => {
        expect(store.getActions()).toEqual(expectedActions);
      });
  });
});
