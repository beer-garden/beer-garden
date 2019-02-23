import configureMockStore from "redux-mock-store";
import thunk from "redux-thunk";
import camelcaseKeys from "camelcase-keys";
import {
  createUser,
  fetchUsers,
  fetchUser,
  deleteUser,
  getUser,
  updateUser,
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
    id: "userId",
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
    fetchMock.onAny(url).networkError();
    fetchMock.onAny(singleUrl).networkError();
    fetchMock.onAny(idUrl).networkError();
  } else if (serverError) {
    fetchMock.onAny(url).reply(status, { message: "Error from server" });
    fetchMock.onAny(singleUrl).reply(status, { message: "Error from server" });
    fetchMock.onAny(idUrl).reply(status, { message: "Error from server" });
  } else {
    fetchMock.onGet(url).reply(200, serverResponse);
    fetchMock.onGet(singleUrl).reply(200, serverResponse[0]);
    fetchMock.onDelete(idUrl).reply(204, null);
    fetchMock.onPost(url).reply(201, serverResponse[0]);
    fetchMock.onPatch(idUrl).reply(200, serverResponse[1]);
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

  describe("updateUser", () => {
    it("should trigger the correct actions on success", () => {
      const { store } = setup();
      const expectedActions = [
        { type: types.UPDATE_USER_BEGIN },
        {
          type: types.UPDATE_USER_SUCCESS,
          payload: { user: serverResponse[1] },
        },
      ];
      const user = camelcaseKeys(serverResponse[1]);
      return store.dispatch(updateUser(user, user)).then(() => {
        expect(store.getActions()).toEqual(expectedActions);
      });
    });

    it("should trigger the correct actions on failure", () => {
      const { store } = setup({}, true);
      const expectedActions = [
        { type: types.UPDATE_USER_BEGIN },
        {
          type: types.UPDATE_USER_FAILURE,
          payload: { error: new Error("Error from server") },
        },
      ];
      const user = camelcaseKeys(serverResponse[1]);
      return store.dispatch(updateUser(user, user)).then(() => {
        expect(store.getActions()).toEqual(expectedActions);
      });
    });

    it("should create the operations for a new username", () => {
      const { store } = setup();
      const prevUser = camelcaseKeys(serverResponse[1]);
      const newUser = { ...prevUser };
      newUser["username"] = "newUsername";
      return store.dispatch(updateUser(prevUser, newUser)).then(() => {
        const history = fetchMock.history;
        const operations = JSON.parse(history.patch[0].data).operations;

        expect(operations.length).toEqual(1);
        expect(operations[0]).toEqual({
          operation: "update",
          path: "/username",
          value: "newUsername",
        });
      });
    });

    it("should create operations for a new password", () => {
      const { store } = setup();
      const prevUser = camelcaseKeys(serverResponse[1]);
      const newUser = { ...prevUser };
      newUser["password"] = "newPassword";
      return store.dispatch(updateUser(prevUser, newUser)).then(() => {
        const history = fetchMock.history;
        const operations = JSON.parse(history.patch[0].data).operations;

        expect(operations.length).toEqual(1);
        expect(operations[0]).toEqual({
          operation: "update",
          path: "/password",
          value: "newPassword",
        });
      });
    });

    it("should create operations for new roles", () => {
      const { store } = setup();
      const prevUser = camelcaseKeys(serverResponse[1]);
      const newUser = { ...prevUser };
      newUser["roles"] = ["bg-admin", "bg-operator", "bg-plugin"];
      return store.dispatch(updateUser(prevUser, newUser)).then(() => {
        const history = fetchMock.history;
        const operations = JSON.parse(history.patch[0].data).operations;

        expect(operations.length).toEqual(1);
        expect(operations[0]).toEqual({
          operation: "set",
          path: "/roles",
          value: ["bg-admin", "bg-operator", "bg-plugin"],
        });
      });
    });

    it("should create a different operation for a user changing their current password", () => {
      const { store } = setup();
      const prevUser = camelcaseKeys(serverResponse[1]);
      const newUser = { ...prevUser };
      newUser["currentPassword"] = "currentPassword";
      newUser["password"] = "newPassword";
      return store.dispatch(updateUser(prevUser, newUser)).then(() => {
        const history = fetchMock.history;
        const operations = JSON.parse(history.patch[0].data).operations;

        expect(operations.length).toEqual(1);
        expect(operations[0]).toEqual({
          operation: "update",
          path: "/password",
          value: {
            current_password: "currentPassword",
            new_password: "newPassword",
          },
        });
      });
    });

    it("should not generate any operations if nothing is set", () => {
      const { store } = setup();
      const prevUser = camelcaseKeys(serverResponse[1]);
      return store.dispatch(updateUser(prevUser, {})).then(() => {
        const history = fetchMock.history;
        const operations = JSON.parse(history.patch[0].data).operations;
        expect(operations.length).toEqual(0);
      });
    });

    it("should not generate any operations if nothing has changed", () => {
      const { store } = setup();
      const prevUser = camelcaseKeys(serverResponse[1]);
      const newUser = { ...prevUser };
      return store.dispatch(updateUser(prevUser, newUser)).then(() => {
        const history = fetchMock.history;
        const operations = JSON.parse(history.patch[0].data).operations;
        expect(operations.length).toEqual(0);
      });
    });
  });
});
