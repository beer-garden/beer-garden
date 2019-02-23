import React from "react";
import { UsersFormContainer } from "../UsersFormContainer";
import { shallow } from "enzyme";
import {
  ALL,
  LIST_ALL,
  ROLE_CREATE,
  ROLE_READ,
  USER_READ,
} from "../../../constants/permissions";
import { flushPromises } from "../../../testHelpers";
import RoleRowContainer from "../RoleRowContainer";
import UserForm from "../../../components/users/UserForm";
import PermissionList from "../../../components/users/PermissionList";

const setup = (overrideProps, overrideState) => {
  const props = Object.assign(
    {
      classes: {},
      currentUser: { username: "user1", permissions: [ROLE_READ, ROLE_CREATE] },
      error: null,
      handleSubmit: jest.fn().mockResolvedValue({}),
      header: "some header",
      requirePassword: true,
      createUserLoading: false,
      createUserError: null,
    },
    overrideProps,
  );

  const initialState = Object.assign(
    {
      username: { value: "name", error: false, help: "" },
      password: { value: "asdfQWER1234!", error: false, help: "" },
      confirmPassword: { value: "asdfQWER1234!", error: false, help: "" },
      selectedRoles: [{ name: "role1", permissions: [ROLE_CREATE], roles: [] }],
      permissions: {
        value: [
          { inherited: true, value: ROLE_CREATE },
          { inherited: false, value: ROLE_READ },
        ],
      },
      newRolePermissions: {
        value: [{ inherited: false, value: ROLE_READ }],
        help: "",
        error: false,
      },
    },
    overrideState,
  );

  const container = shallow(<UsersFormContainer {...props} />);
  container.setState(initialState);
  return {
    container,
    props,
  };
};

describe("<UsersFormContainer />", () => {
  describe("handleFormChange", () => {
    it("should actually update the state correctly.", () => {
      const { container } = setup();
      container.setState({
        username: { value: "nam", error: true, help: "help message" },
      });
      const event = { target: { name: "username", value: "name" } };
      container.instance().handleFormChange(event);
      expect(container.state().username.value).toEqual("name");
      expect(container.state().username.help).toEqual("");
      expect(container.state().username.error).toBe(false);
    });
  });

  describe("handleSubmit", () => {
    it("should save the user and call handleSubmit if everything works", async () => {
      const {
        container,
        props: { handleSubmit },
      } = setup(
        {},
        {
          permissions: {
            value: [{ value: ROLE_CREATE, inherited: true }],
            help: "",
            error: false,
          },
        },
      );

      container.instance().handleSubmit({ preventDefault: () => {} });
      await flushPromises();
      expect(handleSubmit).toHaveBeenCalled();
      expect(handleSubmit).toHaveBeenCalledWith("name", "asdfQWER1234!", [
        "role1",
      ]);
    });

    it("should not create the user if the form is not valid", async () => {
      const {
        container,
        props: { handleSubmit },
      } = setup({}, { username: "" });
      container.instance().handleSubmit({ preventDefault: () => {} });
      await flushPromises();
      expect(handleSubmit).not.toHaveBeenCalled();
    });

    it("should trigger a role save if a permission does not have a role", async () => {
      const {
        container,
        props: { handleSubmit },
      } = setup();
      container.instance().handleSubmit({
        preventDefault: () => {},
      });
      await flushPromises();
      expect(handleSubmit).not.toHaveBeenCalled();
      expect(container.state().triggerRoleSave).toBe(true);
    });
  });

  describe("afterSaveRole", () => {
    it("should set triggerRoleSave to false", () => {
      const { container } = setup();
      const role = { name: "newRole", permissions: ["bg-all"], roles: [] };
      container.instance().afterSaveRole(role);
      expect(container.state().triggerRoleSave).toBe(false);
    });

    it("should add the new role to the selected roles", () => {
      const { container } = setup();
      const role = { name: "newRole", permissions: ["bg-all"], roles: [] };
      container.instance().afterSaveRole(role);
      expect(container.state().selectedRoles.length).toBe(2);
    });

    it("should continue saving the user if it was previously saving", () => {
      const {
        container,
        props: { handleSubmit },
      } = setup({}, { savingUser: true });
      const role = { name: "newRole", permissions: ["bg-all"], roles: [] };
      container.instance().afterSaveRole(role);
      expect(handleSubmit).toHaveBeenCalled();
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
          newRolePermissions: {
            value: [ROLE_CREATE],
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
          newRolePermissions: {
            value: [],
            error: false,
            help: "",
          },
        },
      );
      const valid = container.instance().validateRole();
      expect(valid).toBe(false);
      expect(container.state().newRolePermissions).toEqual({
        value: [],
        error: true,
        help: "Please select at least one permission",
      });
    });
  });

  describe("validateUser", () => {
    it("should check that the text fields are required", () => {
      const { container } = setup(
        {},
        {
          username: { value: "", error: false, help: "" },
          password: { value: "", error: false, help: "" },
          confirmPassword: { value: "", error: false, help: "" },
        },
      );
      const valid = container.instance().validateUser();
      expect(valid).toBe(false);
      expect(container.state().username.error).toBe(true);
      expect(container.state().password.error).toBe(true);
      expect(container.state().confirmPassword.error).toBe(true);
    });

    it("should validate permissions exist", () => {
      const { container } = setup(
        {},
        {
          permissions: { value: [], error: false, help: "" },
        },
      );
      const valid = container.instance().validateUser();
      expect(valid).toBe(false);
      expect(container.state().permissions.error).toBe(true);
    });

    it("should validate that the passwords match", () => {
      const { container } = setup(
        {},
        {
          password: { value: "asdf", error: false, help: "" },
          confirmPassword: { value: "qwer", error: false, help: "" },
        },
      );
      const valid = container.instance().validateUser();
      expect(valid).toBe(false);
      expect(container.state().password.error).toBe(true);
      expect(container.state().confirmPassword.error).toBe(true);
      expect(container.state().password.help).toEqual("Passwords do not match");
    });

    it("should validate the complexity of the password", () => {
      const { container } = setup(
        {},
        {
          password: { value: "asdf", error: false, help: "" },
          confirmPassword: { value: "asdf", error: false, help: "" },
        },
      );
      const valid = container.instance().validateUser();
      expect(valid).toBe(false);
      expect(container.state().password.error).toBe(true);
      expect(container.state().confirmPassword.error).toBe(true);
    });

    it("should not validate length/required password if it is not required", () => {
      const { container } = setup(
        { requirePassword: false },
        { password: { value: "", error: false, help: "" } },
      );
      container.instance().validateUser();
      expect(container.state().password.error).toBe(false);
    });

    it("should still validate a password length/match even if not required", () => {
      const { container } = setup(
        { requirePassword: false },
        {
          password: { value: "!QAZ2wsx", error: false, help: "" },
          confirmPassword: { value: "3edc$RFV", error: false, help: "" },
        },
      );
      container.instance().validateUser();
      expect(container.state().password.error).toBe(true);
    });
  });

  describe("toggleAndUpdatePermission", () => {
    it("should add a permission to both if it does not exist", () => {
      const { container } = setup();
      container
        .instance()
        .toggleAndUpdatePermission({ target: { value: USER_READ } });
      expect(container.state().permissions.value.length).toEqual(3);
      expect(container.state().newRolePermissions.value.length).toEqual(2);
    });

    it("should remove a permission to both if it exists", () => {
      const { container } = setup();
      container
        .instance()
        .toggleAndUpdatePermission({ target: { value: ROLE_READ } });
      expect(container.state().permissions.value.length).toEqual(1);
      expect(container.state().newRolePermissions.value.length).toEqual(0);
    });
  });

  describe("toggleNewPermission", () => {
    it("should add a permission only to the newRole state", () => {
      const { container } = setup();
      container
        .instance()
        .toggleNewPermission({ target: { value: USER_READ } });
      expect(container.state().permissions.value.length).toEqual(2);
      expect(container.state().newRolePermissions.value.length).toEqual(2);
    });
  });

  describe("handleRoleSelect", () => {
    it("should update the selectedRoles", () => {
      const { container } = setup();
      const role = { name: "role2", permissions: [ROLE_READ], roles: [] };
      container.instance().handleRoleSelect(role);
      expect(container.state().selectedRoles).toHaveLength(2);
    });

    it("should only keep inherited permissions on the user permissions", () => {
      const { container } = setup();
      const role = { name: "role2", permissions: [ROLE_READ], roles: [] };
      container.instance().handleRoleSelect(role);
      expect(container.state().permissions.value).toHaveLength(2);
      expect(container.state().newRolePermissions.value).toHaveLength(0);
    });

    it("should keep uninherited permissions on both", () => {
      const { container } = setup();
      const role = { name: "role2", permissions: [USER_READ], roles: [] };
      container.instance().handleRoleSelect(role);
      expect(container.state().permissions.value).toHaveLength(3);
      expect(container.state().newRolePermissions.value).toHaveLength(1);
    });
  });

  describe("render", () => {
    it("should render the important bits", () => {
      const { container } = setup();
      expect(container.find(UserForm)).toHaveLength(1);
      expect(container.find(RoleRowContainer)).toHaveLength(1);
      expect(
        container.find(PermissionList).filter({ edit: true }),
      ).toHaveLength(1);
    });

    it("should not render the row container if the user doesnt have permissions", () => {
      const { container } = setup(
        {
          currentUser: { username: "user1", permissions: [ROLE_CREATE] },
        },
        {},
      );
      expect(container.find(RoleRowContainer)).toHaveLength(0);
    });

    it("should not allow the user to edit permissions if they cannot", () => {
      const { container } = setup(
        {
          currentUser: { username: "user1", permissions: [ROLE_READ] },
        },
        {},
      );
      const list = container.find(PermissionList);
      expect(list).toHaveLength(1);
      expect(list.prop("edit")).toBe(false);
    });
  });

  describe("expandPermissions", () => {
    it("should set permissions to an empty array if they are not provided", () => {
      const { props } = setup();
      props.permissions = undefined;
      const container = shallow(<UsersFormContainer {...props} />);
      expect(container.state().permissions.value).toEqual([]);
    });

    it("should format permissions if given", () => {
      const { props } = setup();
      props.permissions = ["foo"];
      const container = shallow(<UsersFormContainer {...props} />);
      expect(container.state().permissions.value).toEqual([
        { inherited: true, value: "foo" },
      ]);
    });

    it("should expand bg-all to all permisions", () => {
      const { props } = setup();
      props.permissions = [ALL];
      const container = shallow(<UsersFormContainer {...props} />);
      expect(container.state().permissions.value).toHaveLength(LIST_ALL.length);
    });
  });
});
