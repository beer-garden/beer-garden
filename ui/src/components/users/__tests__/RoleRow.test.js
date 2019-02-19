import React from "react";
import { shallow } from "enzyme";
import { RoleRow } from "../RoleRow";
import Chip from "@material-ui/core/Chip";
import Tooltip from "@material-ui/core/Tooltip";

const setup = overrideProps => {
  const props = Object.assign(
    {
      classes: {},
      handleInheritRoleClick: jest.fn(),
      selectedRoles: [
        { name: "role1", description: "role1 description" },
        { name: "role2" },
      ],
      handleRoleClick: jest.fn(),
    },
    overrideProps,
  );
  const row = shallow(<RoleRow {...props} />);
  return {
    row,
    props,
  };
};

describe("<RoleRow />", () => {
  describe("render", () => {
    it("should render a chip per role", () => {
      const { row } = setup();
      expect(row.find(Chip)).toHaveLength(2);
    });

    it("should render a single chip even if no role is selected", () => {
      const { row } = setup({ selectedRoles: [] });
      expect(row.find(Chip)).toHaveLength(1);
    });

    it("should render tooltips for roles", () => {
      const { row } = setup();
      const tooltips = row.find(Tooltip);
      expect(tooltips).toHaveLength(2);
      expect(
        row
          .find(Tooltip)
          .findWhere(node => node.key() === "role1")
          .prop("title"),
      ).toEqual("role1 description");
      expect(
        row
          .find(Tooltip)
          .findWhere(node => node.key() === "role2")
          .prop("title"),
      ).toEqual("No description provided");
    });
  });
});
