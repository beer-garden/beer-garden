import React from "react";
import { shallow } from "enzyme";
import { RolesListContainer } from "../RolesListContainer";
import { ROLE_CREATE } from "../../../constants/permissions";
import Typography from "@material-ui/core/Typography";
import Spinner from "../../../components/layout/Spinner";
import RoleList from "../../../components/roles/RoleList";
import RoleListHeader from "../../../components/roles/RoleListHeader";

const setup = (propOverrides, permissions = null) => {
  permissions = permissions ? permissions : [ROLE_CREATE];
  const props = Object.assign(
    {
      classes: {},
      match: {
        url: "/advanced/users",
      },
      currentUser: {
        username: "user2",
        permissions: permissions,
      },
      roles: [{ name: "role1" }, { name: "role2" }],
      rolesLoading: false,
      rolesError: null,
      fetchRoles: jest.fn(),
    },
    propOverrides,
  );

  const container = shallow(<RolesListContainer {...props} />);
  return {
    props,
    container,
  };
};

describe("<RolesListContainer />", () => {
  describe("componentDidMount", () => {
    it("should call fetchRoles", () => {
      const {
        props: { fetchRoles },
      } = setup();
      expect(fetchRoles).toHaveBeenCalled();
    });
  });

  describe("filterRoles", () => {
    it("should filter roles based on name", () => {
      const { container } = setup();
      container.instance().changeFilter({ target: { value: "1" } });
      container.update();
      expect(container.find(RoleList).prop("roles")).toHaveLength(1);
    });
  });

  describe("render", () => {
    it("should display a spinner while loading", () => {
      const { container } = setup({ rolesLoading: true });
      expect(container.find(Spinner)).toHaveLength(1);
    });

    it("should display an error if one exists", () => {
      const { container } = setup({ rolesError: new Error("error") });
      expect(container.find(Typography)).toHaveLength(1);
    });

    it("should display <RoleList /> and <RoleListHeader /> if it is not loading/errored", () => {
      const { container } = setup();
      expect(container.find(RoleListHeader)).toHaveLength(1);
      expect(container.find(RoleList)).toHaveLength(1);
    });

    it("should not allow users to add if they cannot", () => {
      const { container } = setup({}, []);
      expect(container.find(RoleListHeader).prop("canAdd")).toBe(false);
    });
  });
});
