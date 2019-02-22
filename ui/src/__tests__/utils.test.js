import {
  hasPermissions,
  isEmpty,
  getCookie,
  deleteCookie,
  isValidPassword,
  coalescePermissions,
  toggleItemInArray,
} from "../utils";

describe("utils", () => {
  describe("getCookie", () => {
    test("match", () => {
      expect(getCookie("cookiename")).toEqual("cookievalue");
    });

    test("no match", () => {
      expect(getCookie("NOTTHERE")).toEqual(null);
    });
  });

  describe("deleteCookie", () => {
    afterEach(() => {
      Object.defineProperty(window.document, "cookie", {
        writable: true,
        value: "cookiename=cookievalue",
        match: String.match,
      });
    });

    test("no match", () => {
      deleteCookie("NOTHERE");
      expect(getCookie("NOTHERE")).toEqual(null);
    });

    test("cookiename", () => {
      deleteCookie("cookiename");
      expect(getCookie("cookiename")).toEqual(null);
    });
  });

  describe("isEmpty", () => {
    test("true", () => {
      expect(isEmpty({})).toBe(true);
    });

    test("false", () => {
      expect(isEmpty({ foo: "bar" })).toBe(false);
    });

    test("undefined/null", () => {
      expect(isEmpty(undefined)).toBe(true);
      expect(isEmpty(null)).toBe(true);
    });
  });

  describe("hasPermissions", () => {
    test("no user data/empty permissions", () => {
      expect(hasPermissions({}, ["bg-system-read"])).toBe(false);
      expect(hasPermissions({ foo: "bar" }, ["bg-system-read"])).toBe(false);
      expect(hasPermissions({ permissions: [] }, ["bg-system-read"])).toBe(
        false,
      );
    });

    test("has bg-all permissions", () => {
      expect(
        hasPermissions({ permissions: ["bg-all"] }, ["any-permission"]),
      ).toBe(true);
    });

    test("does not have permissions", () => {
      expect(
        hasPermissions({ permissions: ["permission1"] }, ["permission2"]),
      ).toBe(false);
    });

    test("has only one permission", () => {
      expect(hasPermissions({ permissions: [1] }, [1, 2])).toBe(false);
    });

    test("empty required permissions", () => {
      expect(hasPermissions({ permissions: [1, 2, 3] }, [])).toBe(true);
    });

    test("has correct permissions", () => {
      expect(hasPermissions({ permissions: [1, 2, 3] }, [1])).toBe(true);
      expect(hasPermissions({ permissions: [1, 2, 3] }, [1, 2, 3])).toBe(true);
    });
  });

  describe("isValidPassword", () => {
    it("should be invalid if it is too short", () => {
      expect(isValidPassword("").valid).toBe(false);
      expect(isValidPassword("1234567").valid).toBe(false);
    });

    it("should be invalid if it contains no upper-case characters", () => {
      expect(isValidPassword("bcdefgh1!").valid).toBe(false);
    });

    it("should be invalid if it contains no lower-case characters", () => {
      expect(isValidPassword("BCDEFGH1!").valid).toBe(false);
    });

    it("should be invalid if it contains no digits", () => {
      expect(isValidPassword("Abcdefgh!").valid).toBe(false);
    });

    it("should be invalid if it contains no symbols", () => {
      expect(isValidPassword("Abcdefgh1").valid).toBe(false);
    });

    it("should be valid if it passes all requirements", () => {
      expect(isValidPassword("Abcdefgh1!").valid).toBe(true);
    });
  });

  describe("toggleItemInArray", () => {
    it("should add the item if it does not exist", () => {
      const newArray = toggleItemInArray([], "foo");
      expect(newArray).toEqual(["foo"]);
    });

    it("should remove the item if it alredy exists", () => {
      const newArray = toggleItemInArray(["foo"], "foo");
      expect(newArray).toEqual([]);
    });

    it("should format the item before adding", () => {
      const formatter = value => value.toUpperCase();
      const newArray = toggleItemInArray([], "foo", null, formatter, null);
      expect(newArray).toEqual(["FOO"]);
    });

    it("should respect the value key", () => {
      const newArray = toggleItemInArray(
        ["foo"],
        { key: "foo" },
        null,
        null,
        "key",
      );
      expect(newArray).toEqual([]);
    });

    it("should respect the item key", () => {
      const newArray = toggleItemInArray(
        [{ key: "foo" }],
        "foo",
        "key",
        null,
        null,
      );
      expect(newArray).toEqual([]);
    });
  });

  describe("coalescePermissions", () => {
    it("should return empty sets on empty sets", () => {
      const { roles, permissions } = coalescePermissions([]);
      expect(roles).toEqual(new Set());
      expect(permissions).toEqual(new Set());
    });

    it("should create a union of roles and permissions", () => {
      const roleList = [
        { name: "role1", permissions: ["perm1", "perm2"] },
        { name: "role2", permissions: ["perm1", "perm3"] },
      ];
      const { roles, permissions } = coalescePermissions(roleList);
      expect(roles).toEqual(new Set(["role1", "role2"]));
      expect(permissions).toEqual(new Set(["perm1", "perm2", "perm3"]));
    });

    it("should handle nested roles", () => {
      const role3 = { name: "role3", permissions: ["perm4", "perm2"] };
      const roleList = [
        { name: "role1", permissions: ["perm1", "perm2"] },
        { name: "role2", permissions: ["perm1", "perm3"], roles: [role3] },
      ];
      const { roles, permissions } = coalescePermissions(roleList);
      expect(roles).toEqual(new Set(["role1", "role2", "role3"]));
      expect(permissions).toEqual(
        new Set(["perm1", "perm2", "perm3", "perm4"]),
      );
    });
  });
});
