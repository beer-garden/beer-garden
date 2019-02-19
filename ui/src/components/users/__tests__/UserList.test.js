import React from "react";
import { shallow } from "enzyme";
import { UserList } from "../UserList";
import ListItem from "@material-ui/core/ListItem";
import Typography from "@material-ui/core/Typography";
import RoleRow from "../RoleRow";
import PermissionList from "../PermissionList";

const setup = overrideProps => {
  const props = Object.assign(
    {
      classes: {},
      users: [
        {
          username: "user1",
          id: 1,
          roles: ["role1"],
        },
        {
          username: "user2",
          id: 2,
          roles: ["role2"],
        },
      ],
      match: {
        url: "/advanced/users",
      },
    },
    overrideProps,
  );
  const list = shallow(<UserList {...props} />);
  return {
    list,
    props,
  };
};

describe("<UserList />", () => {
  describe("render", () => {
    it("should render the correct number of users", () => {
      const { list } = setup();
      expect(list.find(ListItem)).toHaveLength(2);
    });

    it("should setup the links correctly", () => {
      const { list } = setup({
        users: [{ username: "foo", id: 1, roles: [] }],
      });
      expect(list.find(ListItem)).toHaveLength(1);
      expect(list.find(ListItem).prop("to")).toEqual("/advanced/users/foo");
    });
  });
});
