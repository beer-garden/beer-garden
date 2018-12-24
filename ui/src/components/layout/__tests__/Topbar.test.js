import React from "react";
import { shallow } from "enzyme";
import { AppBar } from "@material-ui/core";
import { Topbar } from "../Topbar";
import UserIcon from "../UserIcon";

const setup = overrideProps => {
  const props = Object.assign(
    {
      appName: "Beer Garden",
      themeName: "light",
      isAuthenticated: true,
      classes: { appBar: "appBarClassName" },
      setUserTheme: jest.fn(),
      logout: jest.fn(),
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
    test("render with user", () => {
      const { topbar } = setup();
      expect(topbar.find(AppBar)).toHaveLength(1);
      expect(topbar.find(UserIcon)).toHaveLength(1);
    });

    test("render without user", () => {
      const { topbar } = setup({ isAuthenticated: false });
      expect(topbar.find(AppBar)).toHaveLength(1);
      expect(topbar.find(UserIcon)).toHaveLength(0);
    });
  });

  // test("Toggle user settings", () => {
  //   const { wrapper } = setup();
  //   expect(wrapper.state("anchorEl")).toBeNull();
  //   wrapper.find(IconButton).simulate("click", { currentTarget: "target" });
  //   expect(wrapper.state("anchorEl")).toEqual("target");
  //   wrapper.instance().handleClose();
  //   expect(wrapper.state("anchorEl")).toBeNull();
  // });

  // test("Toggle theme", () => {
  //   const { wrapper, props } = setup();
  //   wrapper.find(MenuItem).simulate("click");
  //   expect(props.setUserTheme).toHaveBeenCalled();
  // });
});
