import React from "react";
import { Layout } from "../index";
import { shallow } from "enzyme";
import Topbar from "../Topbar";
import Sidebar from "../Sidebar";

const setup = overrideProps => {
  const props = Object.assign(
    {
      classes: {},
      appName: "Beer Garden",
      themeName: "light",
      isAuthenticated: true,
      setUserTheme: jest.fn(),
      logout: jest.fn(),
    },
    overrideProps,
  );

  const layout = shallow(<Layout {...props} />);
  return {
    layout,
    props,
  };
};

describe("<Layout />", () => {
  test("render", () => {
    const { layout } = setup();
    expect(layout.find(Topbar)).toHaveLength(1);
    expect(layout.find(Sidebar)).toHaveLength(1);
    expect(layout.find("main")).toHaveLength(1);
  });
});
