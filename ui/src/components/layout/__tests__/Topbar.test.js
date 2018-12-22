import React from "react";
import { shallow } from "enzyme";
import { AppBar, IconButton, MenuItem } from "@material-ui/core";
import { Topbar } from "../Topbar";

const setup = overrideProps => {
  const props = Object.assign(
    {
      appName: "Beer Garden",
      themeName: "light",
      isAuthenticated: true,
      classes: { appBar: "appBarClassName" },
      setUserTheme: jest.fn(),
    },
    overrideProps,
  );
  const wrapper = shallow(<Topbar {...props} />);
  return {
    wrapper,
    props,
  };
};

describe("Topbar Component", () => {
  test("render", () => {
    const { wrapper } = setup();
    expect(wrapper.find(AppBar)).toHaveLength(1);
  });

  test("Toggle user settings", () => {
    const { wrapper } = setup();
    expect(wrapper.state("anchorEl")).toBeNull();
    wrapper.find(IconButton).simulate("click", { currentTarget: "target" });
    expect(wrapper.state("anchorEl")).toEqual("target");
    wrapper.instance().handleClose();
    expect(wrapper.state("anchorEl")).toBeNull();
  });

  test("Toggle theme", () => {
    const { wrapper, props } = setup();
    wrapper.find(MenuItem).simulate("click");
    expect(props.setUserTheme).toHaveBeenCalled();
  });
});
