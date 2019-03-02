import React from "react";
import { shallow } from "enzyme";
import { PermissionList } from "../PermissionList";
import { LIST_ALL, REQUEST_READ } from "../../../constants/permissions";
import Checkbox from "@material-ui/core/Checkbox";
import Table from "@material-ui/core/Table";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import TableCell from "@material-ui/core/TableCell";
import Typography from "@material-ui/core/Typography";
import Check from "@material-ui/icons/Check";
import Clear from "@material-ui/icons/Clear";

const setup = overrideProps => {
  const props = Object.assign(
    {
      classes: {},
      edit: false,
      permissions: [REQUEST_READ],
      togglePermission: jest.fn(),
      errorMessage: null,
    },
    overrideProps,
  );
  const permissionList = shallow(<PermissionList {...props} />);
  return {
    permissionList,
    props,
  };
};

describe("PermissionList Component", () => {
  describe("render", () => {
    test("table basics", () => {
      const { permissionList } = setup();
      const table = permissionList.find(Table);
      expect(table).toHaveLength(1);
      expect(
        table
          .find(TableHead)
          .find(TableRow)
          .find(TableCell),
      ).toHaveLength(5);
    });

    test("no edit table should render icons", () => {
      const { permissionList } = setup();
      expect(permissionList.find(Check).length).toEqual(1);
      expect(permissionList.find(Clear).length).toBeGreaterThan(1);
    });

    test("edit true; no permissions", () => {
      const { permissionList } = setup({ edit: true, permissions: [] });
      const boxes = permissionList.find(Checkbox);
      expect(boxes.length).toEqual(LIST_ALL.length);
      expect(boxes.first().prop("checked")).toBe(false);
      expect(boxes.first().prop("disabled")).toBe(false);
    });

    test("edit true; all permissions no inheritance", () => {
      const { permissionList } = setup({
        edit: true,
        permissions: LIST_ALL.map(p => {
          return { value: p, inherited: false };
        }),
      });
      const boxes = permissionList.find(Checkbox);
      expect(boxes.length).toEqual(LIST_ALL.length);
      expect(boxes.first().prop("checked")).toBe(true);
      expect(boxes.first().prop("disabled")).toBe(false);
    });

    test("edit true; all permissions, all inheritance", () => {
      const { permissionList } = setup({
        edit: true,
        permissions: LIST_ALL.map(p => {
          return { value: p, inherited: true };
        }),
      });
      const boxes = permissionList.find(Checkbox);
      expect(boxes.length).toEqual(LIST_ALL.length);
      expect(boxes.first().prop("checked")).toBe(true);
      expect(boxes.first().prop("disabled")).toBe(true);
    });

    test("it should render an error if an errorMessage is provided", () => {
      const { permissionList } = setup({ errorMessage: "some message" });
      expect(
        permissionList.find(Typography).filter({ color: "error" }),
      ).toHaveLength(1);
    });

    test("it should disable everything is disabled is true", () => {
      const { permissionList } = setup({
        edit: true,
        disabled: true,
      });
      const boxes = permissionList.find(Checkbox).filter({ disabled: true });
      expect(boxes.length).toEqual(LIST_ALL.length);
    });
  });
});
