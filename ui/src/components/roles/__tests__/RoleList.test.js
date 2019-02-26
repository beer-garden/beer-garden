import React from "react";
import { shallow } from "enzyme";
import { RoleList } from "../RoleList";
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";
import Typography from "@material-ui/core/Typography";

const setup = overrideProps => {
  const props = Object.assign(
    {
      classes: {},
      roles: [
        {
          name: "role1",
          id: 1,
          permissions: ["perm1"],
        },
        {
          name: "role2",
          id: 2,
          permissions: ["perm2"],
        },
      ],
      match: {
        url: "/advanced/roles",
      },
    },
    overrideProps,
  );
  const list = shallow(<RoleList {...props} />);
  return {
    list,
    props,
  };
};

describe("<RoleList />", () => {
  describe("render", () => {
    it("should render the correct number of roles", () => {
      const { list } = setup();
      expect(list.find(ListItem)).toHaveLength(2);
    });

    it("should setup the links correctly", () => {
      const { list } = setup({
        roles: [{ name: "foo", id: 1, permissions: [] }],
      });
      expect(list.find(ListItem)).toHaveLength(1);
      expect(list.find(ListItem).prop("to")).toEqual("/advanced/roles/foo");
    });

    it("should not render a list if there are no items", () => {
      const { list } = setup({ roles: [] });
      expect(list.find(List)).toHaveLength(0);
      expect(list.find(Typography)).toHaveLength(1);
    });
  });
});
