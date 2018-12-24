import React from "react";
import { App } from "../App";
import { shallow } from "enzyme";
import { Redirect } from "react-router-dom";
import layout from "../../components/layout";

const setup = overrideProps => {
  const props = Object.assign(
    {
      config: {
        authEnabled: true,
        applicationName: "Beer Garden",
      },
      auth: { isAuthenticated: true },
      setUserTheme: jest.fn(),
      logout: jest.fn(),
      themeName: "light",
    },
    overrideProps,
  );

  const app = shallow(<App {...props} />);
  return {
    app,
    props,
  };
};

describe("<App />", () => {
  test("redirect if not authenticated", () => {
    const { app } = setup({ auth: { isAuthenticated: false } });
    expect(app.find(Redirect)).toHaveLength(1);
  });

  test("render layout if authenticated", () => {
    const { app } = setup();
    expect(app.find(layout)).toHaveLength(1);
  });
});
