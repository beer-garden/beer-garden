import React from "react";
import { shallow } from "enzyme";
import { IconButton, Menu } from "@material-ui/core";
import Brightness3 from "@material-ui/icons/Brightness3";
import Brightness5 from "@material-ui/icons/Brightness5";
import { UserIcon } from "../UserIcon";

const setup = overrideProps => {
  const props = Object.assign(
    {
      themeName: "light",
      setUserTheme: jest.fn(),
      logout: jest.fn(),
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
