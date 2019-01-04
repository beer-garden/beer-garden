import React from "react";
import { ListItem } from "@material-ui/core";
import { AdvancedIndex } from "../";
import { shallow } from "enzyme";

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
    test("render correct links when auth disabled", () => {
      const { index } = setup();
      const listItems = index.find(ListItem);
      expect(listItems).toHaveLength(3);

      expect(listItems.filter("#aboutLink")).toHaveLength(1);
      expect(listItems.filter("#sysMgmtLink")).toHaveLength(1);
      expect(listItems.filter("#qMgmtLink")).toHaveLength(1);
    });

    test("render user management if auth enabled and user can see", () => {
      const { index } = setup({
        authEnabled: true,
        userData: { permissions: ["bg-user-read"] },
      });
      const listItems = index.find(ListItem);
      expect(listItems).toHaveLength(4);

      expect(listItems.filter("#usrMgmtLink")).toHaveLength(1);
    });
  });
});
