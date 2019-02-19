import React from "react";
import { shallow } from "enzyme";
import { RoleAddDialog } from "../RoleAddDialog";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContentText from "@material-ui/core/DialogContentText";
import DialogTitle from "@material-ui/core/DialogTitle";
import RoleForm from "../RoleForm";

const setup = overrideProps => {
  const props = Object.assign(
    {
      classes: {},
      error: null,
      handleFormChange: jest.fn(),
      open: true,
      onClose: jest.fn(),
      onSave: jest.fn(),
      permissions: { value: [], help: "", error: false },
      newRoleDescription: { value: "", help: "", error: false },
      newRoleName: { value: "", help: "", error: false },
      saving: false,
      togglePermission: jest.fn(),
    },
    overrideProps,
  );
  const dialog = shallow(<RoleAddDialog {...props} />);
  return {
    dialog,
    props,
  };
};

describe("<RoleAddDialog />", () => {
  describe("render", () => {
    test("no error", () => {
      const { dialog } = setup();
      expect(dialog.find(Dialog)).toHaveLength(1);
      expect(dialog.find(DialogTitle)).toHaveLength(1);
      expect(dialog.find(DialogContentText)).toHaveLength(1);
      expect(dialog.find(DialogActions)).toHaveLength(1);
      expect(dialog.find(RoleForm)).toHaveLength(1);
    });

    test("error", () => {
      const { dialog } = setup({ error: { message: "foo" } });
      expect(dialog.find(DialogContentText)).toHaveLength(2);
    });
  });
});
