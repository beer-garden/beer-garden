import React from "react";
import { shallow } from "enzyme";
import { RoleForm } from "../RoleForm";
import Input from "@material-ui/core/Input";
import PermissionList from "../PermissionList";

const setup = overrideProps => {
  const props = Object.assign(
    {
      classes: {},
      edit: false,
      permissions: { value: [], error: false, help: "" },
      togglePermission: jest.fn(),
      handleFormChange: jest.fn(),
      newRoleName: { value: "", error: false, help: "" },
      newRoleDescription: { value: "", error: false, help: "" },
      saving: false,
    },
    overrideProps,
  );
  const form = shallow(<RoleForm {...props} />);
  return {
    form,
    props,
  };
};

describe("<RoleForm />", () => {
  describe("render", () => {
    it("should render inputs and a <PermissionList />", () => {
      const { form } = setup();
      expect(form.find(Input)).toHaveLength(2);
      expect(form.find(PermissionList)).toHaveLength(1);
    });
  });
});
