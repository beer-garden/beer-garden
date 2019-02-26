import React from "react";
import { shallow } from "enzyme";
import { RolesViewContainer } from "../RolesViewContainer";
import { ROLE_UPDATE, ROLE_DELETE } from "../../../constants/permissions";
import { flushPromises } from "../../../testHelpers";
import Dialog from "@material-ui/core/Dialog";
import Typography from "@material-ui/core/Typography";
import Spinner from "../../../components/layout/Spinner";
import RoleInfo from "../../../components/roles/RoleInfo";

const setup = (propOverrides, stateOverrides = {}) => {
  const props = Object.assign(
    {
      location: { pathname: "/advanced/users/role1" },
      match: {
        params: { name: "role1" },
      },
      selectedRole: {
        name: "role1",
        id: 1,
        permissions: [ROLE_DELETE, ROLE_UPDATE],
      },
      currentUser: {
        username: "user2",
        permissions: [ROLE_UPDATE, ROLE_DELETE],
        roles: ["role2"],
      },
      roleLoading: false,
      roleError: null,
      getRole: jest.fn(),
      deleteRole: jest.fn().mockResolvedValue(true),
      deleteRoleError: null,
      deleteRoleLoading: false,
      updateRoleError: null,
      updateRoleLoading: false,
      updateRole: jest.fn().mockResolvedValue({}),
    },
    propOverrides,
  );

  const container = shallow(<RolesViewContainer {...props} />);
  container.setState(stateOverrides);
  return {
    props,
    container,
  };
};

describe("<RolesViewContainer/>", () => {
  describe("componentDidMount", () => {
    it("should call get role based on the url", () => {
      const {
        props: { getRole },
      } = setup();
      expect(getRole).toHaveBeenCalled();
      expect(getRole).toHaveBeenCalledWith("role1");
    });
  });

  describe("deleteRole", () => {
    it("should call delete with the selected role id", () => {
      const {
        props: { deleteRole },
        container,
      } = setup();
      container.instance().deleteRole();
      expect(deleteRole).toHaveBeenCalled();
      expect(deleteRole).toHaveBeenCalledWith(1);
    });

    it("should set redirect to true if the delete was successful", async () => {
      const { container } = setup();
      container.instance().deleteRole();
      await flushPromises();
      return expect(container.state().redirect).toBe(true);
    });

    it("should not redirect if there was an error", async () => {
      const { container } = setup({ deleteRoleError: new Error("some error") });
      container.instance().deleteRole();
      await flushPromises();
      return expect(container.state().redirect).toBe(false);
    });

    it("should set showConfirmDialog to false", async () => {
      const { container } = setup({}, { showConfirmDialog: true });
      container.instance().deleteRole();
      await flushPromises();
      return expect(container.state().showConfirmDialog).toBe(false);
    });
  });

  describe("deleteRoleDialog", () => {
    it("should call deleteRole like normal for a regular delete", async () => {
      const {
        container,
        props: { deleteRole },
      } = setup({}, {});
      container.instance().deleteRoleDialog();
      await flushPromises();
      expect(deleteRole).toHaveBeenCalled();
    });

    it("should not call deleteRole if it is a protected role", async () => {
      const {
        container,
        props: { deleteRole },
      } = setup({
        selectedRole: { name: "bg-admin", permissions: [], id: 1 },
      });
      container.instance().deleteRoleDialog();
      await flushPromises();
      expect(deleteRole).not.toHaveBeenCalled();
      expect(container.state().showConfirmDialog).toBe(true);
    });

    it("should not call deleteRole if the currentUser has the role", async () => {
      const {
        container,
        props: { deleteRole },
      } = setup({
        selectedRole: { name: "role1", permissions: ["bg-all"], id: 1 },
        currentUser: { username: "foo", roles: ["role1"] },
      });
      container.instance().deleteRoleDialog();
      await flushPromises();
      expect(deleteRole).not.toHaveBeenCalled();
      expect(container.state().showConfirmDialog).toBe(true);
    });
  });

  describe("render", () => {
    it("should display a spinner while loading", () => {
      const { container } = setup({ roleLoading: true });
      expect(container.find(Spinner)).toHaveLength(1);
    });

    it("should display an error if one exists", () => {
      const { container } = setup({ roleError: new Error("error") });
      expect(container.find(Typography)).toHaveLength(1);
    });

    it("should display <RoleInfo /> if it is not loading/errored", () => {
      const { container } = setup();
      expect(container.find(RoleInfo)).toHaveLength(1);
    });

    it("should render <Dialog />", () => {
      const { container } = setup();
      expect(container.find(Dialog)).toHaveLength(1);
    });
  });
});
