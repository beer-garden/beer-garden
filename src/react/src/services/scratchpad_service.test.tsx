import { v4 as uuidv4 } from "uuid";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ScratchPadValue } from "../models/models";
import {
  ClearScratchPad,
  GetScratchPadItems,
  PushToScratchPad,
  RemoveScratchPadItem,
  SetScratchPadItems,
  UpdateScratchPadItem,
} from "./scratchpad_service";

// Mock uuid to make tests deterministic
vi.mock("uuid", () => ({
  v4: vi.fn(() => "mock-uuid-1234"),
}));

describe("scratchpad_service", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe("GetScratchPadItems", () => {
    it("returns empty array and sets default when no items in localStorage", () => {
      const result = GetScratchPadItems();
      expect(result).toEqual([]);
      expect(localStorage.getItem("scratchPadItems")).toBe("[]");
    });

    it("returns parsed items from localStorage", () => {
      const items = [{ padId: "1", padType: "request", values: { foo: "bar" } }];
      localStorage.setItem("scratchPadItems", JSON.stringify(items));

      const result = GetScratchPadItems();
      expect(result).toEqual(items);
    });
  });

  describe("SetScratchPadItems", () => {
    it("stores items in localStorage and returns them", () => {
      const items: ScratchPadValue[] = [
        { padId: "1", padType: "request", values: { a: 1 } },
      ];
      const result = SetScratchPadItems(items);

      expect(result).toEqual(items);
      expect(localStorage.getItem("scratchPadItems")).toBe(
        JSON.stringify(items),
      );
    });
  });

  describe("UpdateScratchPadItem", () => {
    it("updates an existing item by padId", () => {
      const existing: ScratchPadValue[] = [
        { padId: "1", padType: "old", values: { old: true } },
        { padId: "2", padType: "keep", values: { keep: true } },
      ];
      localStorage.setItem("scratchPadItems", JSON.stringify(existing));

      const updated: ScratchPadValue = {
        padId: "1",
        padType: "new",
        values: { new: true },
      };

      const result = UpdateScratchPadItem(updated);

      expect(result[0]).toEqual(updated);
      expect(result[1].padId).toBe("2");
    });

    it("returns all items when padId does not match", () => {
      const existing: ScratchPadValue[] = [
        { padId: "1", padType: "a", values: {} },
      ];
      localStorage.setItem("scratchPadItems", JSON.stringify(existing));

      const result = UpdateScratchPadItem({
        padId: "nonexistent",
        padType: "b",
        values: {},
      });

      expect(result).toHaveLength(1);
      expect(result[0].padId).toBe("1");
    });
  });

  describe("PushToScratchPad", () => {
    it("adds a new item with generated uuid", () => {
      const result = PushToScratchPad("request", { foo: "bar" });

      expect(result).toHaveLength(1);
      expect(result[0]).toEqual({
        padId: "mock-uuid-1234",
        padType: "request",
        values: { foo: "bar" },
      });
      expect(uuidv4).toHaveBeenCalled();
    });

    it("adds to existing items", () => {
      const existing: ScratchPadValue[] = [
        { padId: "existing-1", padType: "old", values: {} },
      ];
      localStorage.setItem("scratchPadItems", JSON.stringify(existing));

      const result = PushToScratchPad("new_type", { new: true });

      expect(result).toHaveLength(2);
      expect(result[0].padId).toBe("existing-1");
      expect(result[1].padId).toBe("mock-uuid-1234");
    });
  });

  describe("RemoveScratchPadItem", () => {
    it("removes item by padId", () => {
      const existing: ScratchPadValue[] = [
        { padId: "1", padType: "a", values: {} },
        { padId: "2", padType: "b", values: {} },
      ];
      localStorage.setItem("scratchPadItems", JSON.stringify(existing));

      const result = RemoveScratchPadItem("1");

      expect(result).toHaveLength(1);
      expect(result[0].padId).toBe("2");
    });

    it("returns all items when padId not found", () => {
      const existing: ScratchPadValue[] = [
        { padId: "1", padType: "a", values: {} },
      ];
      localStorage.setItem("scratchPadItems", JSON.stringify(existing));

      const result = RemoveScratchPadItem("nonexistent");

      expect(result).toHaveLength(1);
    });

    it("handles undefined current items gracefully", () => {
      // GetScratchPadItems returns [] when nothing in localStorage
      const result = RemoveScratchPadItem("other");
      expect(result).toEqual([]);
    });
  });

  describe("ClearScratchPad", () => {
    it("clears all items and returns empty array", () => {
      localStorage.setItem("scratchPadItems", JSON.stringify([{ padId: "1" }]));

      const result = ClearScratchPad();

      expect(result).toEqual([]);
      expect(localStorage.getItem("scratchPadItems")).toBe("[]");
    });
  });
});
