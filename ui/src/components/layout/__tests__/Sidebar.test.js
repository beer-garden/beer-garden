import React from "react";
import { ListItem } from "@material-ui/core";
import { shallow } from "enzyme";
import { Drawer } from "@material-ui/core";
import { Sidebar } from "../Sidebar";

const setup = overrideProps => {
  const props = Object.assign(
    {
      classes: {},
      location: { pathname: "/" },
      mobileOpen: false,
      toggleDrawer: jest.fn(),
    },
    overrideProps,
  );

  const sidebar = shallow(<Sidebar {...props} />);
  return {
    sidebar,
    props,
  };
};

describe("Sidebar Component", () => {
  describe("render", () => {
    test("smoke", () => {
      const { sidebar } = setup();
      // One for mobile, one for non-mobile.
      expect(sidebar.find(Drawer)).toHaveLength(2);
    });

    test("selected routes", () => {
      const { sidebar } = setup({ location: { pathname: "/commands" } });
      const systemLink = sidebar
        .find(ListItem)
        .filter("#systemsSBLink")
        .first();
      const commandLink = sidebar
        .find(ListItem)
        .filter("#commandsSBLink")
        .first();
      expect(systemLink.prop("selected")).toBe(false);
      expect(commandLink.prop("selected")).toBe(true);
    });

    test("select systems if the route is /", () => {
      const { sidebar } = setup({ location: { pathname: "/" } });
      const systemLink = sidebar
        .find(ListItem)
        .filter("#systemsSBLink")
        .first();
      expect(systemLink.prop("selected")).toBe(true);
    });
  });
});
