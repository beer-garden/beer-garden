import React from "react";
import Button from "@material-ui/core/Button";
import RoleForm from "../../../components/users/RoleForm";
import { Redirect } from "react-router-dom";
import { RolesAddContainer } from "../RolesAddContainer";
import { shallow } from "enzyme";
import { flushPromises } from "../../../testHelpers";
import { ROLE_CREATE, ROLE_READ } from "../../../constants/permissions";

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
      newRoleName: { value: "name", error: false, help: "" },
      newRoleDescription: { value: "some description", error: false, help: "" },
      permissions: { value: [{ inherited: false, value: ROLE_READ }] },
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
    it("should do nothing if the role is invalid", async () => {
      const {
        container,
        props: { createRole },
      } = setup({}, { newRoleName: { value: "", error: false, help: "" } });
      const event = { preventDefault: jest.fn() };
      container.instance().saveRole(event);
      await flushPromises();
      expect(createRole).not.toHaveBeenCalled();
    });

    it("should call createRole if everything is valid", async () => {
      const {
        container,
        props: { createRole },
      } = setup();
      const event = { preventDefault: jest.fn() };
      container.instance().saveRole(event);
      await flushPromises();
      expect(createRole).toHaveBeenCalled();
      expect(createRole).toHaveBeenCalledWith("name", "some description", [
        ROLE_READ,
      ]);
    });

    it("should set redirect if everything saves correctly", async () => {
      const { container } = setup();
      const event = { preventDefault: jest.fn() };
      container.instance().saveRole(event);
      await flushPromises();
      expect(container.state().redirect).toBe(true);
    });

    it("should not redirect if an error occurs", async () => {
      const { container } = setup({ roleCreateError: new Error("some error") });
      const event = { preventDefault: jest.fn() };
      container.instance().saveRole(event);
      await flushPromises();
      expect(container.state().redirect).toBe(false);
    });
  });

  describe("validateRole", () => {
    it("should set error to true on newRoleName if it is invalid", () => {
      const { container } = setup(
        {},
        {
          newRoleName: {
            value: "",
            error: false,
            help: "",
          },
          permissions: {
            value: [ROLE_READ],
            error: false,
            help: "",
          },
        },
      );
      const valid = container.instance().validateRole();
      expect(valid).toBe(false);
      expect(container.state().newRoleName).toEqual({
        value: "",
        error: true,
        help: "Role name is required",
      });
    });

    it("should set error to true if there are no permissions", () => {
      const { container } = setup(
        {},
        {
          newRoleName: {
            value: "some name",
            error: false,
            help: "",
          },
          permissions: {
            value: [],
            error: false,
            help: "",
          },
        },
      );
      const valid = container.instance().validateRole();
      expect(valid).toBe(false);
      expect(container.state().permissions).toEqual({
        value: [],
        error: true,
        help: "Please select at least one permission",
      });
    });
  });

  describe("handleFormChange", () => {
    it("should update the value correctly", () => {
      const { container } = setup();
      const event = { target: { name: "newRoleName", value: "newName" } };
      container.instance().handleFormChange(event);
      expect(container.state().newRoleName.value).toEqual("newName");
      expect(container.state().newRoleName.error).toBe(false);
      expect(container.state().newRoleName.help).toEqual("");
    });
  });

  describe("togglePermission", () => {
    it("should add a permission if it does not exist", () => {
      const { container } = setup();
      const event = { target: { value: ROLE_CREATE } };
      container.instance().togglePermission(event);
      const permissions = container.state().permissions;
      expect(permissions.value).toHaveLength(2);
      expect(permissions.value[1].inherited).toBe(false);
      expect(permissions.value[1].value).toEqual(ROLE_CREATE);
    });

    it("should remove a permission if it exists.", () => {
      const { container } = setup();
      const event = { target: { value: ROLE_READ } };
      container.instance().togglePermission(event);
      const permissions = container.state().permissions;
      expect(permissions.value).toHaveLength(0);
    });
  });

  describe("render", () => {
    it("should render the important bits", () => {
      const { container } = setup();
      expect(container.find(Button)).toHaveLength(1);
      expect(container.find(RoleForm)).toHaveLength(1);
    });

    it("should redirect if redirect is true", () => {
      const { container } = setup({}, { redirect: true });
      expect(container.find(Redirect)).toHaveLength(1);
    });
  });
});
