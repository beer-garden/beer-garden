import configureMockStore from "redux-mock-store";
import thunk from "redux-thunk";
import camelcaseKeys from "camelcase-keys";
import {
  fetchRoles,
  createRole,
  updateRole,
  deleteRole,
  getRole,
} from "../role";
import * as types from "../../constants/ActionTypes";
import axios from "axios";
import MockAdapter from "axios-mock-adapter";
import { flushPromises } from "../../testHelpers";

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
    id: "roleId",
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
  const state = Object.assign({ roles: [] }, initialState);
  const url = "/api/v1/roles";
  const idUrl = "/api/v1/roles/roleId";
  if (networkError) {
    fetchMock.onAny(url).networkError();
    fetchMock.onAny(idUrl).networkError();
  } else if (serverError) {
    fetchMock.onAny(url).reply(status, { message: "Error from server" });
    fetchMock.onAny(idUrl).reply(status, { message: "Error from server" });
  } else {
    fetchMock.onGet(url).reply(200, serverResponse);
    fetchMock.onPost(url).reply(201, serverResponse[0]);
    fetchMock.onDelete(idUrl).reply(200, null);
    fetchMock.onPatch(idUrl).reply(200, serverResponse[1]);
  }

  const store = mockStore({ roleReducer: state });
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

  describe("updateRole", () => {
    it("should trigger the correct actions on success", () => {
      const { store } = setup();
      const expectedActions = [
        { type: types.UPDATE_ROLE_BEGIN },
        {
          type: types.UPDATE_ROLE_SUCCESS,
          payload: { role: serverResponse[1] },
        },
      ];
      const role = camelcaseKeys(serverResponse[1]);
      return store.dispatch(updateRole(role, role)).then(() => {
        expect(store.getActions()).toEqual(expectedActions);
      });
    });

    it("should trigger the correct actions on failure", () => {
      const { store } = setup({}, true);
      const expectedActions = [
        { type: types.UPDATE_ROLE_BEGIN },
        {
          type: types.UPDATE_ROLE_FAILURE,
          payload: { error: new Error("Error from server") },
        },
      ];
      const role = camelcaseKeys(serverResponse[1]);
      return store.dispatch(updateRole(role, role)).then(() => {
        expect(store.getActions()).toEqual(expectedActions);
      });
    });

    it("should create the operations for a new description", () => {
      const { store } = setup();
      const prevRole = camelcaseKeys(serverResponse[1]);
      const newRole = { ...prevRole };
      newRole["description"] = "newDescription";
      return store.dispatch(updateRole(prevRole, newRole)).then(() => {
        const history = fetchMock.history;
        const operations = JSON.parse(history.patch[0].data).operations;

        expect(operations.length).toEqual(1);
        expect(operations[0]).toEqual({
          operation: "update",
          path: "/description",
          value: "newDescription",
        });
      });
    });

    it("should create operations for new permissions", () => {
      const { store } = setup();
      const prevRole = camelcaseKeys(serverResponse[1]);
      const newRole = { ...prevRole };
      newRole["permissions"] = ["bg-all"];
      return store.dispatch(updateRole(prevRole, newRole)).then(() => {
        const history = fetchMock.history;
        const operations = JSON.parse(history.patch[0].data).operations;

        expect(operations.length).toEqual(1);
        expect(operations[0]).toEqual({
          operation: "set",
          path: "/permissions",
          value: ["bg-all"],
        });
      });
    });

    it("should not generate any operations if nothing new is set", () => {
      const { store } = setup();
      const prevRole = camelcaseKeys(serverResponse[1]);
      return store.dispatch(updateRole(prevRole, prevRole)).then(() => {
        const history = fetchMock.history;
        const operations = JSON.parse(history.patch[0].data).operations;
        expect(operations.length).toEqual(0);
      });
    });
  });

  describe("deleteRole", () => {
    it("should trigger the correct actions on success", () => {
      const { store } = setup();
      const expectedActions = [
        { type: types.DELETE_ROLE_BEGIN },
        { type: types.DELETE_ROLE_SUCCESS, payload: "roleId" },
      ];
      return store.dispatch(deleteRole("roleId")).then(() => {
        expect(store.getActions()).toEqual(expectedActions);
      });
    });

    it("should trigger the correct actions on failure", () => {
      const { store } = setup({}, true, false);
      const expectedActions = [
        { type: types.DELETE_ROLE_BEGIN },
        {
          type: types.DELETE_ROLE_FAILURE,
          payload: { error: Error("Error from server") },
        },
      ];
      return store.dispatch(deleteRole("roleId")).then(() => {
        expect(store.getActions()).toEqual(expectedActions);
      });
    });
  });

  describe("getRole", () => {
    it("should trigger the right actions when already loaded", () => {
      const { store } = setup({ roles: camelcaseKeys(serverResponse) });
      const expectedActions = [
        { type: types.FETCH_ROLE_BEGIN },
        {
          type: types.FETCH_ROLE_SUCCESS,
          payload: { role: camelcaseKeys(serverResponse[1]) },
        },
      ];
      store.dispatch(getRole(serverResponse[1]["name"]));
      expect(store.getActions()).toEqual(expectedActions);
    });

    it("should trigger the right actions when loaded and name does not exist", () => {
      const { store } = setup({ roles: camelcaseKeys(serverResponse) });
      const expectedActions = [
        { type: types.FETCH_ROLE_BEGIN },
        {
          type: types.FETCH_ROLE_FAILURE,
          payload: { error: new Error("Invalid role name") },
        },
      ];
      store.dispatch(getRole("INVALID NAME"));
      expect(store.getActions()).toEqual(expectedActions);
    });

    it("should trigger the right actions when not loaded and exists", async () => {
      const { store } = setup();
      const roles = camelcaseKeys(serverResponse);
      const expectedActions = [
        { type: types.FETCH_ROLE_BEGIN },
        { type: types.FETCH_ROLES_BEGIN },
        {
          type: types.FETCH_ROLES_SUCCESS,
          payload: { roles },
        },
        {
          type: types.FETCH_ROLE_FAILURE,
          payload: { error: new Error("Invalid role name") },
        },
      ];
      store.dispatch(getRole("INVALID ROLE NAME"));
      await flushPromises();
      expect(store.getActions()).toEqual(expectedActions);
    });
  });
});
