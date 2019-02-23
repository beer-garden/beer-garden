import React from "react";
import { shallow } from "enzyme";
import { UsersAddContainer } from "../UsersAddContainer";
import { flushPromises } from "../../../testHelpers";
import { Redirect } from "react-router-dom";
import UsersFormContainer from "../UsersFormContainer";

const setup = (propOverrides, stateOverrides) => {
  const props = Object.assign(
    {
      classes: {},
      currentUser: {},
      createUser: jest.fn().mockResolvedValue({}),
      createUserLoading: false,
      createUserError: null,
      location: { pathname: "/advanced/users/add" },
    },
    propOverrides,
  );

  const container = shallow(<UsersAddContainer {...props} />);
  container.setState(stateOverrides);
  return {
    props,
    container,
  };
};

describe("<UsersAddContainer />", () => {
  describe("saveUser", () => {
    it("should call createUser with the args provided", () => {
      const {
        props: { createUser },
        container,
      } = setup();
      container.instance().saveUser("username", "password", "roleNames");
      expect(createUser).toHaveBeenCalled();
      expect(createUser).toHaveBeenCalledWith(
        "username",
        "password",
        "roleNames",
      );
    });

    it("should set redirect to true if the save was successful", async () => {
      const { container } = setup();
      container.instance().saveUser("u", "p", "r");
      await flushPromises();
      expect(container.state().redirect).toBe(true);
      expect(container.state().newUsername).toEqual("u");
    });

    it("should not redirect if there was an error", async () => {
      const { container } = setup({ createUserError: new Error("some error") });
      container.instance().saveUser("u", "p", "r");
      await flushPromises();
      expect(container.state().redirect).toBe(false);
    });
  });

  describe("render", () => {
    it("should redirect if redirect is true", () => {
      const { container } = setup(
        {},
        { redirect: true, newUsername: "username" },
      );

      expect(container.find(Redirect)).toHaveLength(1);
      expect(container.find(Redirect).prop("to")).toEqual(
        "/advanced/users/username",
      );
    });

    it("should render a <UsersFormContainer />", () => {
      const { container } = setup();
      expect(container.find(UsersFormContainer)).toHaveLength(1);
    });
  });
});
