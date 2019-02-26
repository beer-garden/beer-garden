import React from "react";
import { shallow } from "enzyme";
import { RoleInfoHeader } from "../RoleInfoHeader";
import Button from "@material-ui/core/Button";
import Typography from "@material-ui/core/Typography";
import HowToReg from "@material-ui/icons/HowToReg";
import Close from "@material-ui/icons/Close";
import Delete from "@material-ui/icons/Delete";
import Edit from "@material-ui/icons/Edit";
import Save from "@material-ui/icons/Save";

const setup = overrideProps => {
  const props = Object.assign(
    {
      classes: {},
      canEdit: true,
      canDelete: true,
      deleting: false,
      onCancelEdit: jest.fn(),
      onEdit: jest.fn(),
      onDelete: jest.fn(),
      errorMessage: "",
      editing: false,
      saving: false,
    },
    overrideProps,
  );
  const header = shallow(<RoleInfoHeader {...props} />);
  return {
    header,
    props,
  };
};

describe("<RoleInfoHeader />", () => {
  describe("render", () => {
    it("should render the title", () => {
      const { header } = setup();
      expect(header.find(Typography)).toHaveLength(2);
      expect(header.find(HowToReg)).toHaveLength(1);
    });

    it("should render the buttons", () => {
      const { header } = setup();
      expect(header.find(Button)).toHaveLength(2);
    });

    it("should not render if the user cant see them", () => {
      const { header } = setup({ canEdit: false, canDelete: false });
      expect(header.find(Button)).toHaveLength(0);
    });

    it("should disable the buttons if we are deleting", () => {
      const { header } = setup({ deleting: true });
      expect(header.find(Button).filter({ disabled: true })).toHaveLength(2);
    });

    it("should display an error message if one is provided", () => {
      const { header } = setup({ errorMessage: "error" });
      expect(header.find(Typography)).toHaveLength(3);
    });

    it("should render save/cancel buttons while editing", () => {
      const { header } = setup({ editing: true });
      expect(header.find(Save)).toHaveLength(1);
      expect(header.find(Close)).toHaveLength(1);
    });

    it("should only render the edit button if the user cant delete", () => {
      const { header } = setup({ canEdit: true, canDelete: false });
      expect(header.find(Edit)).toHaveLength(1);
      expect(header.find(Delete)).toHaveLength(0);
    });

    it("should only render the delete button if the user cant edit", () => {
      const { header } = setup({ canEdit: false, canDelete: true });
      expect(header.find(Edit)).toHaveLength(0);
      expect(header.find(Delete)).toHaveLength(1);
    });
  });
});
