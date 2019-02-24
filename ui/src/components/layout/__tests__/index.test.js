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
      isAnonymous: false,
      authEnabled: true,
      setUserTheme: jest.fn(),
      logout: jest.fn(),
      username: null,
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
  test("render authenticated", () => {
    const { layout } = setup();
    expect(layout.find(Topbar)).toHaveLength(1);
    expect(layout.find(Sidebar)).toHaveLength(1);
    expect(layout.find("main")).toHaveLength(1);
  });

  test("render unauthenticated", () => {
    const { layout } = setup({ isAuthenticated: false });
    expect(layout.find(Sidebar)).toHaveLength(0);
  });

  test("render no auth", () => {
    const { layout } = setup({ authEnabled: false });
    expect(layout.find(Sidebar)).toHaveLength(1);
  });
});
