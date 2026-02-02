import { ScratchPadValue } from "../models/models";
import { v4 as uuidv4 } from "uuid";

export const GetScratchPadItems = () => {
  const storedValue = localStorage.getItem("scratchPadItems");

  if (storedValue !== null) {
    return JSON.parse(storedValue) as Array<ScratchPadValue>;
  }
  const defaultPads = [] as Array<ScratchPadValue>;
  localStorage.setItem("scratchPadItems", JSON.stringify(defaultPads));
  return defaultPads;
};

export const SetScratchPadItems = (items: Array<ScratchPadValue>) => {
  localStorage.setItem("scratchPadItems", JSON.stringify(items));
  return items;
};

export const UpdateScratchPadItem = (updatedPadValue: ScratchPadValue) => {
  const currentItems = GetScratchPadItems();
  let list = currentItems.map((value: ScratchPadValue) => {
    if (value.padId === updatedPadValue.padId) {
      return updatedPadValue;
    }
    return value;
  });
  return SetScratchPadItems(list);
};

export const PushToScratchPad = (padType: string, values: any) => {
  const currentItems = GetScratchPadItems();

  currentItems.push({
    padId: uuidv4(),
    padType: padType,
    values: values,
  } as ScratchPadValue);
  return SetScratchPadItems(currentItems);
};

export const RemoveScratchPadItem = (padId: string) => {
  const currentItems = GetScratchPadItems();
  let list = currentItems.filter((value: ScratchPadValue) => {
    return value.padId !== padId && value !== null;
  });
  return SetScratchPadItems(list);
};

export const ClearScratchPad = () => {
  const defaultPads = [] as Array<ScratchPadValue>;
  localStorage.setItem("scratchPadItems", JSON.stringify(defaultPads));
  return defaultPads;
};
