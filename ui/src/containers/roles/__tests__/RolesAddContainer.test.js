import React from "react";
import RolesFormContainer from "../RolesFormContainer";
import { Redirect } from "react-router-dom";
import { RolesAddContainer } from "../RolesAddContainer";
import { shallow } from "enzyme";
import { flushPromises } from "../../../testHelpers";
import { ROLE_READ } from "../../../constants/permissions";

const setup = (overrideProps, overrideState) => {
  const props = Object.assign(
    {
      classes: {},
      createRole: jest.fn().mockResolvedValue({}),
      roleCreateLoading: false,
      roleCreateError: null,
      location: { pathname: "/advanced/roles/add" },
    },
    overrideProps,
  );

  const initialState = Object.assign(
    {
      newRoleName: "",
      redirect: false,
    },
    overrideState,
  );

  const container = shallow(<RolesAddContainer {...props} />);
  container.setState(initialState);
  return {
    container,
    props,
  };
};

describe("<RolesAddContainer />", () => {
  describe("saveRole", () => {
    it("should set redirect if everything saves correctly", async () => {
      const { container } = setup();
      container.instance().saveRole("name", "desc", [ROLE_READ]);
      await flushPromises();
      expect(container.state().redirect).toBe(true);
      expect(container.state().newRoleName).toEqual("name");
    });

    it("should not redirect if an error occurs", async () => {
      const { container } = setup({ roleCreateError: new Error("some error") });
      container.instance().saveRole("name", "desc", [ROLE_READ]);
      await flushPromises();
      expect(container.state().redirect).toBe(false);
      expect(container.state().newRoleName).toEqual("");
    });
  });

  describe("render", () => {
    it("should render a <RolesFormContainer /> if editing is true", () => {
      const { container } = setup({}, { editing: true });
      expect(container.find(RolesFormContainer)).toHaveLength(1);
    });

    it("should redirect if redirect is true", () => {
      const { container } = setup({}, { redirect: true });
      expect(container.find(Redirect)).toHaveLength(1);
    });
  });
});
