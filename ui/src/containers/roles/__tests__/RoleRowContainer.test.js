import React from "react";
import { shallow } from "enzyme";
import { RoleRowContainer } from "../RoleRowContainer";
import { ROLE_CREATE, USER_DELETE } from "../../../constants/permissions";
import { flushPromises } from "../../../testHelpers";
import RoleRow from "../../../components/roles/RoleRow";
import RoleDialog from "../../../components/roles/RoleDialog";
import RoleAddDialog from "../../../components/roles/RoleAddDialog";

const setup = propOverrides => {
  const props = Object.assign(
    {
      afterSaveRole: jest.fn(),
      selectedRoles: [],
      handleRoleClick: jest.fn(),
      handleFormChange: jest.fn(),
      permissions: { value: [{ value: USER_DELETE }], help: "", error: false },
      newRoleDescription: { value: "desc", help: "", error: false },
      newRoleName: { value: "name", help: "", error: false },
      togglePermission: jest.fn(),
      triggerRoleSave: false,
      validateRole: () => {
        return true;
      },
      fetchRoles: jest.fn(),
      currentUser: { permissions: [ROLE_CREATE] },
      roleCreateError: null,
      roleCreateLoading: false,
      roles: [],
      rolesLoading: false,
      rolesError: null,
      createRole: jest.fn().mockResolvedValue("result"),
    },
    propOverrides,
  );

  const container = shallow(<RoleRowContainer {...props} />);
  return {
    props,
    container,
  };
};

describe("<RoleRowContainer />", () => {
  describe("componentDidMount", () => {
    it("should call fetchRoles ", () => {
      const {
        props: { fetchRoles },
      } = setup();
      expect(fetchRoles).toHaveBeenCalled();
    });
  });

  describe("toggle dialogs", () => {
    it("should open/close the create dialog", () => {
      const { container } = setup();
      container.instance().closeCreateDialog();
      expect(container.state().createDialogOpen).toBe(false);
      container.instance().openCreateDialog();
      expect(container.state().createDialogOpen).toBe(true);
    });

    it("should open/close the read dialog", () => {
      const { container } = setup();
      container.instance().closeReadDialog();
      expect(container.state().readDialogOpen).toBe(false);
      container.instance().openReadDialog();
      expect(container.state().readDialogOpen).toBe(true);
    });
  });

  describe("saveRole", () => {
    it("should not create the roll if validate returns false", async () => {
      const {
        container,
        props: { createRole },
      } = setup({
        validateRole: () => {
          return false;
        },
      });
      container.instance().saveRole();
      await flushPromises();
      expect(createRole).not.toHaveBeenCalled();
    });

    it("should call create roll if validate returns true", async () => {
      const {
        props: { createRole },
        container,
      } = setup();
      container.instance().saveRole();
      await flushPromises();
      expect(createRole).toHaveBeenCalled();
      expect(createRole).toHaveBeenCalledWith("name", "desc", [USER_DELETE]);
    });

    it("should close the create dialog after a successful save", async () => {
      const { container } = setup();
      container.setState({ createDialogOpen: true });
      container.instance().saveRole();
      await flushPromises();
      expect(container.state().createDialogOpen).toBe(false);
    });

    it("should call afterSave if the save was successful", async () => {
      const {
        container,
        props: { afterSaveRole },
      } = setup();
      container.instance().saveRole();
      await flushPromises();
      expect(afterSaveRole).toHaveBeenCalled();
      expect(afterSaveRole).toHaveBeenCalledWith("result");
    });

    it("should not do anything if create fails", async () => {
      const {
        container,
        props: { afterSaveRole },
      } = setup({ roleCreateError: new Error("some error") });
      container.setState({ createDialogOpen: true });
      container.instance().saveRole();
      await flushPromises();
      expect(afterSaveRole).not.toHaveBeenCalled();
      expect(container.state().createDialogOpen).toBe(true);
    });
  });

  describe("render", () => {
    it("should display the right components", () => {
      const { container } = setup();
      expect(container.find(RoleRow)).toHaveLength(1);
      expect(container.find(RoleDialog)).toHaveLength(1);
      expect(container.find(RoleAddDialog)).toHaveLength(1);
    });

    it("should not display role add dialog if the user cannot create roles", () => {
      const { container } = setup({ currentUser: { permissions: [] } });
      expect(container.find(RoleAddDialog)).toHaveLength(0);
    });

    it("should set roleAddDialog to open if triggerRoleSave is set", () => {
      const { container } = setup({ triggerRoleSave: true });
      expect(container.find(RoleAddDialog).prop("open")).toBe(true);
    });
  });
});
