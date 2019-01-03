import { isEmpty, getCookie, deleteCookie } from "../utils";

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
});
