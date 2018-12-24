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
      expect(sidebar.find(Drawer)).toHaveLength(1);
    });

    test("selected routes", () => {
      const { sidebar } = setup({ location: { pathname: "/commands" } });
      const systemLink = sidebar.find(ListItem).filter("#systemsSBLink");
      const commandLink = sidebar.find(ListItem).filter("#commandsSBLink");
      expect(systemLink.prop("selected")).toBe(false);
      expect(commandLink.prop("selected")).toBe(true);
    });
  });
});
