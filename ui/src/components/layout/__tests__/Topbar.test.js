import React from "react";
import { shallow } from "enzyme";
import { AppBar, IconButton } from "@material-ui/core";
import { Topbar } from "../Topbar";
import UserIcon from "../UserIcon";

const setup = overrideProps => {
  const props = Object.assign(
    {
      appName: "Beer Garden",
      themeName: "light",
      isAuthenticated: true,
      authEnabled: true,
      classes: { appBar: "appBarClassName" },
      setUserTheme: jest.fn(),
      logout: jest.fn(),
      toggleDrawer: jest.fn(),
      username: null,
    },
    overrideProps,
  );
  const topbar = shallow(<Topbar {...props} />);
  return {
    topbar,
    props,
  };
};

describe("<Topbar />", () => {
  describe("render", () => {
    test("basic", () => {
      const { topbar } = setup();
      expect(topbar.find(AppBar)).toHaveLength(1);
      expect(topbar.find(UserIcon)).toHaveLength(1);
      expect(topbar.find(IconButton)).toHaveLength(1);
    });
  });
});
