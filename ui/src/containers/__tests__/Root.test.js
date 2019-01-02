import React from "react";
import { Root } from "../Root";
import { shallow } from "enzyme";
import App from "../App";
import Spinner from "../../components/layout/Spinner";
import ErrorRetryDialog from "../../components/layout/ErrorRetryDialog";
import { flushPromises } from "../../testHelpers";

const setup = propOverrides => {
  const mockLoadConfig = jest.fn();
  mockLoadConfig.mockResolvedValue({});
  const props = Object.assign(
    {
      loadConfig: mockLoadConfig,
      loadUserData: jest.fn(),
      isAuthenticated: false,
      userLoading: false,
      userData: {},
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
  describe("render", () => {
    test("<App /> when not loadin gor errored.", () => {
      const { wrapper } = setup();
      expect(wrapper.find(App)).toHaveLength(1);
    });
    test("<Spinner /> while loading", () => {
      const { wrapper } = setup({ configLoading: true });
      expect(wrapper.find(Spinner)).toHaveLength(1);
    });
    test("<ErrorRetryDialog/> if an error occurs", () => {
      const { wrapper } = setup({ configError: new Error("message") });
      expect(wrapper.find(ErrorRetryDialog)).toHaveLength(1);
    });
    test("<ErrorRetryDialog /> if loading after an error", () => {
      const { wrapper } = setup({
        configLoading: true,
        configError: new Error("message"),
      });
      expect(wrapper.find(Spinner)).toHaveLength(0);
      expect(wrapper.find(ErrorRetryDialog)).toHaveLength(1);
    });
  });

  describe("componentDidMount", () => {
    test("only load config if auth is not enabled.", () => {
      const { props } = setup({ config: { authEnabled: false } });
      return flushPromises().then(() => {
        expect(props.loadConfig.mock.calls.length).toEqual(1);
        expect(props.loadUserData.mock.calls.length).toEqual(0);
      });
    });

    test("load config and user data if auth is enabled and authenticated.", () => {
      const { props } = setup({
        config: { authEnabled: true },
        isAuthenticated: true,
      });
      return flushPromises().then(() => {
        expect(props.loadConfig.mock.calls.length).toEqual(1);
        expect(props.loadUserData.mock.calls.length).toEqual(1);
      });
    });
  });
});
