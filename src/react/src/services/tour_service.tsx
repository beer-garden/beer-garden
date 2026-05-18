import { RefObject } from "react";

import { TourStepProps } from "../models/models";

export const ConvertToTourStepProps = (steps: Array<TourStepProps>): any => {
  const tourSteps = [] as Array<any>;

  for (const layerType of ["NAVIGATION", "LAYOUT", "COMPONENT"]) {
    for (const layerStep of steps
      .filter((step) => step.layer === layerType)
      .sort((stepA, stepB) => {
        // Ensure components are grouped together
        const prefixSort = stepA.prefix.localeCompare(stepB.prefix);
        if (prefixSort !== 0) {
          return prefixSort;
        }

        // Ensure we respect component ordering
        return stepA.pos - stepB.pos;
      })) {
      tourSteps.push({
        content: layerStep.content,
        target: `[data-step="${layerStep.prefix}-${layerStep.uuid}-${layerStep.label}"]`,
        title: layerStep.label,
        beaconPlacement: "top",
      });
    }
  }

  return tourSteps;
};

export const GenerateTourProps = (tourStep: Partial<TourStepProps>) => {
  try {
    if (!tourStep.prefix || !tourStep.uuid || !tourStep.label) {
      throw new Error(
        "TourStepProps must have prefix, uuid, and label to generate tour props",
      );
    }
    return {
      "data-step": `${tourStep.prefix}-${tourStep.uuid}-${tourStep.label}`,
    };
  } catch (error) {
    console.error("Error adding tour step:", error);
  }
};

export const AddTourStep = (
  tourStepsRef: RefObject<Array<TourStepProps>>,
  tourStep: TourStepProps,
) => {
  if (tourStep?.uuid === undefined || tourStepsRef?.current === undefined) {
    return;
  }

  // either don't know about the prefix/label combo or
  // we already know about the combo with the UUID (indicating a re-write of the UI)
  if (
    tourStepsRef.current.length === 0 ||
    !tourStepsRef.current.some(
      (step) =>
        step.prefix === tourStep.prefix && step.label === tourStep.label,
    ) ||
    tourStepsRef.current.some(
      (step) =>
        step.prefix === tourStep.prefix &&
        step.label === tourStep.label &&
        step.uuid === tourStep.uuid,
    )
  ) {
    if (
      tourStepsRef.current.length === 0 ||
      !tourStepsRef.current.some(
        (step) =>
          step.prefix === tourStep.prefix &&
          step.label === tourStep.label &&
          step.uuid === tourStep.uuid,
      )
    ) {
      tourStepsRef.current.push(tourStep);
    }
  }
};

export const RemoveTourStep = (
  tourStepsRef: RefObject<Array<TourStepProps>>,
  tourStep: TourStepProps,
) => {
  if (tourStep.uuid && tourStepsRef.current) {
    tourStepsRef.current = tourStepsRef.current.filter(
      (step) =>
        !(
          step.prefix === tourStep.prefix &&
          step.label === tourStep.label &&
          step.uuid === tourStep.uuid
        ),
    );
  }
};

export const ClearTourSteps = (
  tourStepsRef: RefObject<Array<TourStepProps>>,
  prefix: string,
  uuid?: string,
) => {
  if (uuid && tourStepsRef?.current) {
    tourStepsRef.current = tourStepsRef.current.filter(
      (step) => !(step.prefix === prefix && step.uuid === uuid),
    );
  }
};
