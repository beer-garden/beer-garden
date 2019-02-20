import React from "react";
import { shallow } from "enzyme";
import { UsersViewContainer } from "../UsersViewContainer";
import { USER_UPDATE, USER_DELETE } from "../../../constants/permissions";
import { flushPromises } from "../../../testHelpers";
import Typography from "@material-ui/core/Typography";
import Spinner from "../../../components/layout/Spinner";
import UserInfo from "../../../components/users/UserInfo";

const setup = propOverrides => {
  const props = Object.assign(
    {
      classes: {},
      match: {
        params: { username: "user1" },
      },
      selectedUser: { username: "user1", id: 1 },
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
    },
    propOverrides,
  );

  const container = shallow(<UsersViewContainer {...props} />);
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
  });
});
