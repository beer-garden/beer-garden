import React from "react";
import { shallow } from "enzyme";
import { RoleInfo } from "../RoleInfo";
import Typography from "@material-ui/core/Typography";
import PermissionList from "../PermissionList";
import { ROLE_CREATE } from "../../../constants/permissions";

const setup = overrideProps => {
  const props = Object.assign(
    {
      classes: {},
      role: {
        name: "name",
        description: "description",
        permissions: [ROLE_CREATE],
      },
    },
    overrideProps,
  );
  const info = shallow(<RoleInfo {...props} />);
  return {
    info,
    props,
  };
};

describe("<RoleInfo />", () => {
  describe("render", () => {
    it("should render everything", () => {
      const { info } = setup();
      expect(info.find(Typography)).toHaveLength(2);
      expect(info.find(PermissionList)).toHaveLength(1);
    });
  });
});
