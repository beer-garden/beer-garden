import React from "react";
import { ListItem } from "@material-ui/core";
import { AdvancedIndex } from "../";
import { shallow } from "enzyme";
import { ROLE_READ } from "../../../constants/permissions";

const setup = overrideProps => {
  const props = Object.assign(
    {
      authEnabled: false,
      userData: {},
      match: { url: "/advanced" },
    },
    overrideProps,
  );
  const index = shallow(<AdvancedIndex {...props} />);
  return {
    index,
    props,
  };
};

describe("<AdvancedIndex />", () => {
  describe("render", () => {
    it("should render correct links when auth disabled", () => {
      const { index } = setup();
      const listItems = index.find(ListItem);
      expect(listItems).toHaveLength(3);

      expect(listItems.filter("#aboutLink")).toHaveLength(1);
      expect(listItems.filter("#sysMgmtLink")).toHaveLength(1);
      expect(listItems.filter("#qMgmtLink")).toHaveLength(1);
    });

    it("should render user management if auth enabled and user can see", () => {
      const { index } = setup({
        authEnabled: true,
        userData: { permissions: ["bg-user-read"] },
      });
      const listItems = index.find(ListItem);
      expect(listItems).toHaveLength(4);

      expect(listItems.filter("#usrMgmtLink")).toHaveLength(1);
    });

    it("should render role management if auth enabled and the user can", () => {
      const { index } = setup({
        authEnabled: true,
        userData: { permissions: [ROLE_READ] },
      });
      const listItems = index.find(ListItem);
      expect(listItems).toHaveLength(4);

      expect(listItems.filter("#roleMgmtLink")).toHaveLength(1);
    });
  });
});
