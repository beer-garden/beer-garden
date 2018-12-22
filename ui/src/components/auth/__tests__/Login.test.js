import React from "react";
import { Button, CircularProgress } from "@material-ui/core";
import { Login } from "../Login";
import { shallow } from "enzyme";

const setup = overrideProps => {
  const mockLogin = jest.fn();
  mockLogin.mockResolvedValue({});

  const props = Object.assign(
    {
      classes: {},
      loading: false,
      login: jest.fn(),
      guestLoginEnabled: true,
      guestLogin: jest.fn(),
      error: null,
    },
    overrideProps,
  );
  const login = shallow(<Login {...props} />);
  return {
    login,
    props,
  };
};

describe("Login Component", () => {
  describe("render", () => {
    test("render form and submit button", () => {
      const { login } = setup();
      expect(login.find("form")).toHaveLength(1);
      expect(login.find('[type="submit"]')).toHaveLength(1);
    });

    test("buttons should be disabled if loading", () => {
      const { login } = setup({ loading: true });
      login.find(Button).forEach(node => {
        expect(node.prop("disabled")).toBe(true);
      });
    });

    test("guest login button exists if enabled", () => {
      const { login } = setup();
      expect(login.find("#guestLoginBtn")).toHaveLength(1);
    });

    test("guest login button does not exist if disabled", () => {
      const { login } = setup({ guestLoginEnabled: false });
      expect(login.find("#guestLoginBtn")).toHaveLength(0);
    });

    test("error appears if it exists", () => {
      const { login } = setup({ error: { message: "errorMessage" } });
      expect(login.find("#errorMessage")).toHaveLength(1);
    });

    test("error does not appear if it does not exist", () => {
      const { login } = setup();
      expect(login.find("#errorMessage")).toHaveLength(0);
    });

    test("Loading appears if the user is loading", () => {
      const { login } = setup({ loading: true });
      expect(login.find(CircularProgress)).toHaveLength(1);
    });
  });

  describe("onChangeEvents", () => {
    test("set username", () => {
      const { login } = setup();
      login
        .find("#username")
        .simulate("change", { target: { name: "username", value: "name" } });
      expect(login.state("username")).toEqual("name");
    });
  });

  describe("logins", () => {
    test("onSubmit", () => {
      const { login, props } = setup();
      login.setState({ username: "name", password: "password" });
      const event = {
        preventDefault() {},
      };
      login.instance().onSubmit(event);
      expect(props.login.mock.calls.length).toBe(1);
      expect(props.login.mock.calls[0]).toEqual([login.state()]);
    });

    test("guestLogin", () => {
      const { login, props } = setup();
      login.find("#guestLoginBtn").simulate("click");
      expect(props.guestLogin.mock.calls.length).toBe(1);
      expect(props.guestLogin.mock.calls[0]).toEqual([login.state()]);
    });
  });
});
