import { getCookie, deleteCookie } from "../utils";

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
