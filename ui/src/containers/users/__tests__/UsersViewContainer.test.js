import React from "react";
import { shallow } from "enzyme";
import { UsersViewContainer } from "../UsersViewContainer";
import { USER_UPDATE, USER_DELETE } from "../../../constants/permissions";
import { flushPromises } from "../../../testHelpers";
import Dialog from "@material-ui/core/Dialog";
import Typography from "@material-ui/core/Typography";
import Spinner from "../../../components/layout/Spinner";
import UserInfo from "../../../components/users/UserInfo";
import UsersFormContainer from "../UsersFormContainer";

const setup = (propOverrides, stateOverrides = {}) => {
  const props = Object.assign(
    {
      location: { pathname: "/advanced/users/userId" },
      match: {
        params: { username: "user1" },
      },
      selectedUser: {
        username: "user1",
        id: 1,
        roles: [{ name: "bg-admin" }],
      },
      currentUser: {
        username: "user2",
        permissions: [USER_UPDATE, USER_DELETE],
      },
      userLoading: false,
      userError: null,
      getUser: jest.fn(),
      deleteUser: jest.fn().mockResolvedValue(true),
      deleteUserError: null,
      deleteUserLoading: false,
      updateUserError: null,
      updateUserLoading: false,
      updateUser: jest.fn().mockResolvedValue({}),
    },
    propOverrides,
  );

  const container = shallow(<UsersViewContainer {...props} />);
  container.setState(stateOverrides);
  return {
    props,
    container,
  };
};

describe("<UsersViewContainer />", () => {
  describe("componentDidMount", () => {
    it("should call get user based on the url", () => {
      const {
        props: { getUser },
      } = setup();
      expect(getUser).toHaveBeenCalled();
      expect(getUser).toHaveBeenCalledWith("user1");
    });
  });

  describe("deleteUser", () => {
    it("should call delete with the selected user id", () => {
      const {
        props: { deleteUser },
        container,
      } = setup();
      container.instance().deleteUser();
      expect(deleteUser).toHaveBeenCalled();
      expect(deleteUser).toHaveBeenCalledWith(1);
    });

    it("should set redirect to true if the delete was successful", async () => {
      const { container } = setup();
      container.instance().deleteUser();
      await flushPromises();
      return expect(container.state().redirect).toBe(true);
    });

    it("should not redirect if there was an error", async () => {
      const { container } = setup({ deleteUserError: new Error("some error") });
      container.instance().deleteUser();
      await flushPromises();
      return expect(container.state().redirect).toBe(false);
    });

    it("should set showConfirmDialog to false", async () => {
      const { container } = setup({}, { showConfirmDialog: true });
      container.instance().deleteUser();
      await flushPromises();
      return expect(container.state().showConfirmDialog).toBe(false);
    });
  });

  describe("deleteUserDialog", () => {
    it("should call deleteUser like normal for a regular delete", async () => {
      const {
        container,
        props: { deleteUser },
      } = setup({}, {});
      container.instance().deleteUserDialog();
      await flushPromises();
      expect(deleteUser).toHaveBeenCalled();
    });

    it("should not call deleteUser if user is a protected user", async () => {
      const {
        container,
        props: { deleteUser },
      } = setup({
        selectedUser: { username: "admin", permissions: [], id: 1 },
      });
      container.instance().deleteUserDialog();
      await flushPromises();
      expect(deleteUser).not.toHaveBeenCalled();
      expect(container.state().showConfirmDialog).toBe(true);
    });

    it("should not call deleteUser if the selectedUser and currentUser are the same", async () => {
      const {
        container,
        props: { deleteUser },
      } = setup({
        selectedUser: { username: "foo", permissions: [], id: 1 },
        currentUser: { username: "foo", permissions: [] },
      });
      container.instance().deleteUserDialog();
      await flushPromises();
      expect(deleteUser).not.toHaveBeenCalled();
      expect(container.state().showConfirmDialog).toBe(true);
    });
  });

  describe("handleUpdate", () => {
    it("should not call updateUser if there is no need", async () => {
      const {
        container,
        props: { selectedUser, updateUser },
      } = setup();

      container
        .instance()
        .handleUpdate(
          selectedUser.username,
          "",
          selectedUser.roles.map(r => r.name),
        );
      await flushPromises();
      return expect(updateUser).not.toHaveBeenCalled();
    });

    it("should toggleEdit after the user saves", async () => {
      const {
        container,
        props: { selectedUser },
      } = setup({}, { editing: true });

      container
        .instance()
        .handleUpdate(
          selectedUser.username,
          "",
          selectedUser.roles.map(r => r.name),
        );
      await flushPromises();
      expect(container.state().editing).toBe(false);
    });

    it("should call updateUser", async () => {
      const {
        container,
        props: { updateUser },
      } = setup();
      container
        .instance()
        .handleUpdate("newUsername", "newPassword", ["newrole1", "newrole2"]);
      await flushPromises();
      expect(updateUser).toHaveBeenCalled();
      expect(updateUser).toHaveBeenCalledWith(
        { id: 1, username: "user1", roles: ["bg-admin"] },
        {
          username: "newUsername",
          password: "newPassword",
          roles: ["newrole1", "newrole2"],
        },
      );
    });

    it("should not toggle editing if updateUser fails", async () => {
      const { container } = setup(
        { updateUserError: new Error("some error") },
        { editing: true },
      );
      container
        .instance()
        .handleUpdate("newUsername", "newPassword", ["newrole1", "newrole2"]);
      await flushPromises();
      expect(container.state().editing).toBe(true);
    });
  });

  describe("render", () => {
    it("should display a spinner while loading", () => {
      const { container } = setup({ userLoading: true });
      expect(container.find(Spinner)).toHaveLength(1);
    });

    it("should display an error if one exists", () => {
      const { container } = setup({ userError: new Error("error") });
      expect(container.find(Typography)).toHaveLength(1);
    });

    it("should display <UserInfo /> if it is not loading/errored", () => {
      const { container } = setup();
      expect(container.find(UserInfo)).toHaveLength(1);
    });

    it("should render <UserFormContainer /> if it is editing", () => {
      const { container } = setup({}, { editing: true });
      expect(container.find(UsersFormContainer)).toHaveLength(1);
    });

    it("should render <Dialog />", () => {
      const { container } = setup();
      expect(container.find(Dialog)).toHaveLength(1);
    });
  });
});
