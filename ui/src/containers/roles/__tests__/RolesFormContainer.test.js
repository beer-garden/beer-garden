import React from "react";
import Typography from "@material-ui/core/Typography";
import Button from "@material-ui/core/Button";
import RoleForm from "../../../components/users/RoleForm";
import { RolesFormContainer } from "../RolesFormContainer";
import { shallow } from "enzyme";
import { flushPromises } from "../../../testHelpers";
import { ROLE_CREATE, ROLE_READ } from "../../../constants/permissions";

const setup = (overrideProps, overrideState) => {
  const props = Object.assign(
    {
      classes: {},
      handleSubmit: jest.fn(),
      header: "header",
      loading: false,
      error: null,
      newRoleName: "",
      newRoleDescription: "",
      permissions: [],
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

  const container = shallow(<RolesFormContainer {...props} />);
  container.setState(initialState);
  return {
    container,
    props,
  };
};

describe("<RolesFormContainer />", () => {
  describe("handleSubmit", () => {
    it("should do nothing if the role is invalid", async () => {
      const {
        container,
        props: { handleSubmit },
      } = setup({}, { newRoleName: { value: "", error: false, help: "" } });
      const event = { preventDefault: jest.fn() };
      container.instance().handleSubmit(event);
      await flushPromises();
      expect(handleSubmit).not.toHaveBeenCalled();
    });

    it("should call handleSubmit if everything is valid", async () => {
      const {
        container,
        props: { handleSubmit },
      } = setup();
      const event = { preventDefault: jest.fn() };
      container.instance().handleSubmit(event);
      await flushPromises();
      expect(handleSubmit).toHaveBeenCalled();
      expect(handleSubmit).toHaveBeenCalledWith("name", "some description", [
        ROLE_READ,
      ]);
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
      const { container } = setup({ header: <Button /> });
      expect(container.find(Typography)).toHaveLength(1);
      expect(container.find(Button)).toHaveLength(1);
      expect(container.find(RoleForm)).toHaveLength(1);
    });
  });
});
