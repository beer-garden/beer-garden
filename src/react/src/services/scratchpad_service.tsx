import { ScratchPadValue } from "../models/models";

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

export const UpdateScratchPadItem = (index: number, values: any) => {
  const currentItems = GetScratchPadItems();
  let list = currentItems.map((value: any, idx: number) => {
    if (index === idx) {
      value.values = values;
    }
    return value;
  });
  return SetScratchPadItems(list);
};

export const PushToScratchPad = (padType: string, values: any) => {
  const currentItems = GetScratchPadItems();
  currentItems.push({ padType: padType, values: values });
  return SetScratchPadItems(currentItems);
};

export const RemoveScratchPadItem = (index: number) => {
  const currentItems = GetScratchPadItems();
  let list = currentItems.filter((value: any, idx: number) => {
    return index !== idx && value !== null;
  });
  return SetScratchPadItems(list);
};

export const ClearScratchPad = () => {
  const defaultPads = [] as Array<ScratchPadValue>;
  localStorage.setItem("scratchPadItems", JSON.stringify(defaultPads));
  return defaultPads;
};
