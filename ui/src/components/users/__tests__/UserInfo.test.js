import React from "react";
import { shallow } from "enzyme";
import { UserInfo } from "../UserInfo";
import Typography from "@material-ui/core/Typography";
import RoleRow from "../RoleRow";
import PermissionList from "../PermissionList";

const setup = overrideProps => {
  const props = Object.assign(
    {
      classes: {},
      user: {
        username: "username",
        roles: ["role1", "role2"],
        permissions: [],
      },
    },
    overrideProps,
  );
  const info = shallow(<UserInfo {...props} />);
  return {
    info,
    props,
  };
};

describe("<UserInfo />", () => {
  describe("render", () => {
    it("should render everything", () => {
      const { info } = setup();
      expect(info.find(Typography)).toHaveLength(1);
      expect(info.find(RoleRow)).toHaveLength(1);
      expect(info.find(PermissionList)).toHaveLength(1);
    });
  });
});
