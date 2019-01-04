import { hasPermissions, isEmpty, getCookie, deleteCookie } from "../utils";

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
});
