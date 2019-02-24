import React from "react";
import { shallow } from "enzyme";
import { Typography, IconButton, Menu } from "@material-ui/core";
import Brightness3 from "@material-ui/icons/Brightness3";
import Brightness5 from "@material-ui/icons/Brightness5";
import { UserIcon } from "../UserIcon";

const setup = overrideProps => {
  const props = Object.assign(
    {
      isAuthenticated: true,
      isAnonymous: false,
      authEnabled: true,
      themeName: "light",
      setUserTheme: jest.fn(),
      logout: jest.fn(),
      classes: {},
      username: "someuser",
    },
    overrideProps,
  );
  const userIcon = shallow(<UserIcon {...props} />);
  return {
    userIcon,
    props,
  };
};

describe("<UserIcon />", () => {
  describe("render", () => {
    test("smoke test", () => {
      const { userIcon } = setup();
      expect(userIcon.find(IconButton)).toHaveLength(1);
      expect(userIcon.find(Menu)).toHaveLength(1);
    });

    test("render correct icon for light theme", () => {
      const { userIcon } = setup({ themeName: "light" });
      userIcon.find(IconButton).simulate("click", { currentTarget: "target" });
      expect(userIcon.find(Brightness3)).toHaveLength(1);
    });

    test("render correct icon for dark theme", () => {
      const { userIcon } = setup({ themeName: "dark" });
      userIcon.find(IconButton).simulate("click", { currentTarget: "target" });
      expect(userIcon.find(Brightness5)).toHaveLength(1);
    });

    test("No signout if auth is not enabled", () => {
      const { userIcon } = setup({ authEnabled: false });
      expect(userIcon.find("#signoutMenuItem")).toHaveLength(0);
    });

    test("No signout if not authenticated", () => {
      const { userIcon } = setup({ isAuthenticated: false });
      expect(userIcon.find("#signoutMenuItem")).toHaveLength(0);
    });

    test("should render change password if the user can", () => {
      const { userIcon } = setup();
      expect(userIcon.find("#changePassMenuItem")).toHaveLength(1);
    });

    test("should not render change password if anonymous", () => {
      const { userIcon } = setup({ isAnonymous: true });
      expect(userIcon.find("#changePassMenuItem")).toHaveLength(0);
    });

    test("username", () => {
      const { userIcon } = setup({ isAuthenticated: false });
      expect(
        userIcon
          .find(Typography)
          .dive()
          .dive()
          .text(),
      ).toEqual(" someuser");
    });
  });

  test("Toggle user settings", () => {
    const { userIcon } = setup();
    expect(userIcon.state("anchorEl")).toBeNull();
    userIcon.find(IconButton).simulate("click", { currentTarget: "target" });
    expect(userIcon.state("anchorEl")).toEqual("target");
    userIcon.instance().handleClose();
    expect(userIcon.state("anchorEl")).toBeNull();
  });

  test("Toggle theme", () => {
    const { userIcon, props } = setup();
    userIcon.find("#themeMenuItem").simulate("click");
    expect(props.setUserTheme).toHaveBeenCalled();
  });

  test("Signout click", () => {
    const { userIcon, props } = setup();
    userIcon.find("#signoutMenuItem").simulate("click");
    expect(props.logout).toHaveBeenCalled();
  });
});
