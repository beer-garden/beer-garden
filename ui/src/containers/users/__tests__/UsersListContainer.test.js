import React from "react";
import { shallow } from "enzyme";
import { UsersListContainer } from "../UsersListContainer";
import {
  USER_CREATE,
  ROLE_READ,
  ROLE_CREATE,
} from "../../../constants/permissions";
import Typography from "@material-ui/core/Typography";
import Spinner from "../../../components/layout/Spinner";
import UserList from "../../../components/users/UserList";
import UserListHeader from "../../../components/users/UserListHeader";

const setup = (propOverrides, permissions = null) => {
  permissions = permissions
    ? permissions
    : [USER_CREATE, ROLE_CREATE, ROLE_READ];
  const props = Object.assign(
    {
      classes: {},
      match: {
        url: "/advanced/users",
      },
      currentUser: {
        username: "user2",
        permissions: permissions,
      },
      users: [{ username: "user1" }, { username: "user2" }],
      usersLoading: false,
      usersError: null,
      fetchUsers: jest.fn(),
    },
    propOverrides,
  );

  const container = shallow(<UsersListContainer {...props} />);
  return {
    props,
    container,
  };
};

describe("<UsersListContainer />", () => {
  describe("componentDidMount", () => {
    it("should call fetchUsers", () => {
      const {
        props: { fetchUsers },
      } = setup();
      expect(fetchUsers).toHaveBeenCalled();
    });
  });

  describe("filterUsers", () => {
    it("should filter users based on username", () => {
      const { container } = setup();
      container.instance().changeFilter({ target: { value: "1" } });
      container.update();
      expect(container.find(UserList).prop("users")).toHaveLength(1);
    });
  });

  describe("render", () => {
    it("should display a spinner while loading", () => {
      const { container } = setup({ usersLoading: true });
      expect(container.find(Spinner)).toHaveLength(1);
    });

    it("should display an error if one exists", () => {
      const { container } = setup({ usersError: new Error("error") });
      expect(container.find(Typography)).toHaveLength(1);
    });

    it("should display <UserList /> and <UserListHeader /> if it is not loading/errored", () => {
      const { container } = setup();
      expect(container.find(UserListHeader)).toHaveLength(1);
      expect(container.find(UserList)).toHaveLength(1);
    });

    it("should not allow users to add if they cannot succeed", () => {
      const { container } = setup({}, []);
      expect(container.find(UserListHeader).prop("canAdd")).toBe(false);
    });
  });
});
