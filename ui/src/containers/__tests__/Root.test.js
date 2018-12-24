import React from "react";
import { Root } from "../Root";
import { shallow } from "enzyme";
import { Route, Switch } from "react-router-dom";
import App from "../App";
import LoginDashboard from "../auth/LoginDashboard";
import Spinner from "../../components/layout/Spinner";
import ErrorRetryDialog from "../../components/layout/ErrorRetryDialog";

const setup = propOverrides => {
  const props = Object.assign(
    {
      loadConfig: jest.fn(),
      config: { authEnabled: false },
      configLoading: false,
      configError: null,
      theme: {},
    },
    propOverrides,
  );

  const wrapper = shallow(<Root {...props} />);
  return {
    props,
    wrapper,
  };
};

describe("<Root />", () => {
  test("render", () => {
    const { wrapper } = setup();
    const swtch = wrapper.find(Switch);
    expect(swtch).toHaveLength(1);
    const routes = swtch.find(Route);
    expect(routes).toHaveLength(2);
    expect(routes.at(1).prop("component")).toEqual(App);
    expect(routes.at(0).prop("component")).toEqual(LoginDashboard);
  });

  test("Render <Spinner /> while loading", () => {
    const { wrapper } = setup({ configLoading: true });
    expect(wrapper.find(Spinner)).toHaveLength(1);
  });

  test("render <ErrorRetryDialog/> if an error occurs", () => {
    const { wrapper } = setup({ configError: new Error("message") });
    expect(wrapper.find(ErrorRetryDialog)).toHaveLength(1);
  });

  test("render <ErrorRetryDialog /> if loading after an error", () => {
    const { wrapper } = setup({
      configLoading: true,
      configError: new Error("message"),
    });
    expect(wrapper.find(Spinner)).toHaveLength(0);
    expect(wrapper.find(ErrorRetryDialog)).toHaveLength(1);
  });
});
