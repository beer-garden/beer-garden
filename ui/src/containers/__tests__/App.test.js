import React from "react";
import { App } from "../App";
import { shallow } from "enzyme";
import { Route } from "react-router-dom";
import layout from "../../components/layout";
import AuthRoute from "../auth/AuthRoute";

const setup = overrideProps => {
  const props = Object.assign(
    {
      config: {
        authEnabled: true,
        applicationName: "Beer Garden",
      },
      auth: { isAuthenticated: true, userData: {} },
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
  test("render layout and routes", () => {
    const { app } = setup();
    expect(app.find(layout)).toHaveLength(1);
    expect(app.find(Route)).toHaveLength(1);
    expect(app.find(AuthRoute).length).toBeGreaterThan(0);
  });
});
