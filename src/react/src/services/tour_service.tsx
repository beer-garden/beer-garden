import { RefObject } from "react";

import { TourStepProps } from "../models/models";

export const ConvertToTourStepProps = (steps: Array<TourStepProps>): any => {
  return steps.map((step) => {
    return {
      content: step.content,
      target: `[data-step="${step.prefix}-${step.uuid}-${step.label}"]`,
    };
  });
};

export const GenerateTourProps = (
  tourStepsRef: RefObject<Array<TourStepProps>>,
  tourStep: TourStepProps,
) => {
  if (tourStep.uuid === undefined) {
    return {};
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
    return {
      "data-step": `${tourStep.prefix}-${tourStep.uuid}-${tourStep.label}`,
    };
  }

  return {};
};

export const ClearTourSteps = (
  tourStepsRef: RefObject<Array<TourStepProps>>,
  prefix: string,
  uuid?: string,
) => {
  if (uuid) {
    tourStepsRef.current = tourStepsRef.current.filter(
      (step) => !(step.prefix === prefix && step.uuid === uuid),
    );
  }
};
