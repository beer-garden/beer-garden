import { describe, expect, it } from "vitest";

import { TourStepProps } from "../models/models";
import {
  AddTourStep,
  ClearTourSteps,
  ConvertToTourStepProps,
  GenerateTourProps,
  RemoveTourStep,
} from "./tour_service";

describe("tour_service", () => {
  const makeTourStep = (
    partial: Partial<TourStepProps> = {},
  ): TourStepProps => ({
    content: "Test content",
    prefix: "test_prefix",
    uuid: "test-uuid",
    label: "Test Label",
    layer: "NAVIGATION",
    pos: 0,
    ...partial,
  });

  describe("ConvertToTourStepProps", () => {
    it("converts tour steps by layer and sorts within each layer", () => {
      const steps: TourStepProps[] = [
        makeTourStep({ layer: "NAVIGATION", prefix: "a", pos: 1, label: "A" }),
        makeTourStep({ layer: "NAVIGATION", prefix: "a", pos: 0, label: "B" }),
        makeTourStep({ layer: "LAYOUT", prefix: "c", pos: 0, label: "C" }),
        makeTourStep({ layer: "NAVIGATION", prefix: "b", pos: 0, label: "D" }),
      ];

      const result = ConvertToTourStepProps(steps);

      expect(result).toHaveLength(4);
      // NAVIGATION prefix "a" comes first (sorted by prefix), within "a" sorted by pos
      expect(result[0].target).toContain("a");
      expect(result[0].title).toBe("B"); // pos 0 before pos 1
      expect(result[1].title).toBe("A"); // pos 1
      expect(result[2].title).toBe("D"); // prefix "b" after "a"
      expect(result[3].title).toBe("C"); // LAYOUT comes after NAVIGATION
    });

    it("returns empty array for no steps", () => {
      const result = ConvertToTourStepProps([]);
      expect(result).toEqual([]);
    });

    it("sets correct target attributes", () => {
      const steps = [makeTourStep({ prefix: "nav", label: "Home" })];
      const result = ConvertToTourStepProps(steps);
      expect(result[0].target).toBe(
        '[data-step="nav-test-uuid-Home"]',
      );
    });

    it("sets beaconPlacement to top", () => {
      const steps = [makeTourStep()];
      const result = ConvertToTourStepProps(steps);
      expect(result[0].beaconPlacement).toBe("top");
    });
  });

  describe("GenerateTourProps", () => {
    it("generates data-step attribute with all parts", () => {
      const step = { prefix: "nav", uuid: "abc", label: "Home" };
      const result = GenerateTourProps(step);
      expect(result).toEqual({
        "data-step": "nav-abc-Home",
      });
    });

    it("returns undefined when prefix is missing", () => {
      const result = GenerateTourProps({ uuid: "abc", label: "Home" });
      expect(result).toBeUndefined();
    });

    it("returns undefined when uuid is missing", () => {
      const result = GenerateTourProps({ prefix: "nav", label: "Home" });
      expect(result).toBeUndefined();
    });

    it("returns undefined when label is missing", () => {
      const result = GenerateTourProps({ prefix: "nav", uuid: "abc" });
      expect(result).toBeUndefined();
    });
  });

  describe("AddTourStep", () => {
    it("adds a step when ref is empty", () => {
      const ref = { current: [] as TourStepProps[] };
      const step = makeTourStep();

      AddTourStep(ref as any, step);

      expect(ref.current).toHaveLength(1);
      expect(ref.current[0]).toEqual(step);
    });

    it("does not add duplicate step (same prefix and label)", () => {
      const step = makeTourStep();
      const ref = { current: [step] };

      AddTourStep(ref as any, makeTourStep({ label: step.label }));

      expect(ref.current).toHaveLength(1);
    });

    it("does not add step with same prefix and label even if uuid differs", () => {
      const step1 = makeTourStep({ uuid: "uuid1" });
      const ref = { current: [step1] };

      AddTourStep(ref as any, makeTourStep({ uuid: "uuid2" }));

      // The code only checks prefix and label, not uuid, for dedup
      expect(ref.current).toHaveLength(1);
    });

    it("does nothing when ref.current is undefined", () => {
      const ref = { current: undefined };
      const step = makeTourStep();

      expect(() => AddTourStep(ref as any, step)).not.toThrow();
    });

    it("does nothing when step.uuid is undefined", () => {
      const ref = { current: [] as TourStepProps[] };

      AddTourStep(ref as any, makeTourStep({ uuid: undefined }));

      expect(ref.current).toHaveLength(0);
    });
  });

  describe("RemoveTourStep", () => {
    it("removes step matching prefix, label, and uuid", () => {
      const step1 = makeTourStep({ uuid: "u1", prefix: "a", label: "L1" });
      const step2 = makeTourStep({ uuid: "u2", prefix: "a", label: "L2" });
      const ref = { current: [step1, step2] };

      RemoveTourStep(ref as any, step1);

      expect(ref.current).toHaveLength(1);
      expect(ref.current[0].uuid).toBe("u2");
    });

    it("does nothing when step not found", () => {
      const step1 = makeTourStep({ uuid: "u1" });
      const ref = { current: [step1] };

      RemoveTourStep(ref as any, makeTourStep({ uuid: "u999" }));

      expect(ref.current).toHaveLength(1);
    });

    it("does nothing when uuid is undefined", () => {
      const ref = { current: [makeTourStep()] };

      RemoveTourStep(ref as any, { uuid: undefined } as any);

      expect(ref.current).toHaveLength(1);
    });

    it("does nothing when ref.current is undefined", () => {
      const ref = { current: undefined };

      expect(() =>
        RemoveTourStep(ref as any, makeTourStep()),
      ).not.toThrow();
    });
  });

  describe("ClearTourSteps", () => {
    it("removes steps matching prefix and uuid", () => {
      const step1 = makeTourStep({ uuid: "u1", prefix: "a" });
      const step2 = makeTourStep({ uuid: "u2", prefix: "a" });
      const step3 = makeTourStep({ uuid: "u3", prefix: "b" });
      const ref = { current: [step1, step2, step3] };

      ClearTourSteps(ref as any, "a", "u1");

      expect(ref.current).toHaveLength(2);
      expect(ref.current.map((s) => s.uuid)).toEqual(["u2", "u3"]);
    });

    it("does nothing when uuid is undefined", () => {
      const step = makeTourStep({ prefix: "a" });
      const ref = { current: [step] };

      ClearTourSteps(ref as any, "a");

      expect(ref.current).toHaveLength(1);
    });

    it("does nothing when ref.current is undefined", () => {
      const ref = { current: undefined };

      expect(() => ClearTourSteps(ref as any, "a", "u1")).not.toThrow();
    });
  });
});
