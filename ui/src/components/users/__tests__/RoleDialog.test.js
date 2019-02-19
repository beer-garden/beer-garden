import React from "react";
import { shallow } from "enzyme";
import { RoleDialog } from "../RoleDialog";
import DialogContentText from "@material-ui/core/DialogContentText";
import Group from "@material-ui/icons/Group";
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";
import ListItemText from "@material-ui/core/ListItemText";
import Spinner from "../../layout/Spinner";

const setup = overrideProps => {
  const props = Object.assign(
    {
      canAdd: false,
      open: true,
      onClose: jest.fn(),
      roles: [
        { name: "role1" },
        { name: "role2", description: "text" },
        { name: "role3" },
      ],
      selectedRoles: [{ name: "role2" }],
      rolesError: null,
      rolesLoading: false,
      handleSelectRole: jest.fn(),
      handleAddRoleClick: jest.fn(),
    },
    overrideProps,
  );
  const dialog = shallow(<RoleDialog {...props} />);
  return {
    dialog,
    props,
  };
};

describe("<RoleDialog />", () => {
  describe("render", () => {
    test("loading", () => {
      const { dialog } = setup({ rolesLoading: true });
      expect(dialog.find(Spinner)).toHaveLength(1);
    });

    test("error", () => {
      const { dialog } = setup({ rolesError: { message: "foo" } });
      expect(dialog.find(DialogContentText)).toHaveLength(1);
      expect(dialog.find(DialogContentText).prop("color")).toEqual("error");
    });

    it("should render all the roles", () => {
      const { dialog } = setup();
      expect(dialog.find(List)).toHaveLength(1);
      expect(dialog.find(ListItem)).toHaveLength(3);
    });

    it("should render an extra add item if canAdd is true", () => {
      const { dialog } = setup({ canAdd: true });
      expect(dialog.find(ListItem)).toHaveLength(4);
    });

    it("should change icon and text colors for selected items", () => {
      const { dialog } = setup();
      const primaryIcons = dialog.find(Group).filter({ color: "primary" });
      const inheritedIcons = dialog.find(Group).filter({ color: "inherit" });
      expect(primaryIcons).toHaveLength(1);
      expect(inheritedIcons).toHaveLength(2);

      const textPrimaryItems = dialog
        .find(ListItemText)
        .filter({ primaryTypographyProps: { color: "textPrimary" } });
      const primaryItems = dialog
        .find(ListItemText)
        .filter({ primaryTypographyProps: { color: "primary" } });
      expect(primaryItems).toHaveLength(1);
      expect(textPrimaryItems).toHaveLength(2);
    });
  });
});
