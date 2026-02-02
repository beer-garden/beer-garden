export const CompareObjects = (obj1: any, obj2: any) => {
  if (obj1 === obj2) return true; // Check if they are the same reference

  if (typeof obj1 !== typeof obj2) return false; // Check if they are of the same type

  if (
    typeof obj1 !== "object" ||
    obj1 === null ||
    typeof obj2 !== "object" ||
    obj2 === null
  ) {
    return false; // Check if both are objects and not null
  }

  const keys1 = Object.keys(obj1);
  const keys2 = Object.keys(obj2);

  if (keys1.length !== keys2.length) return false; // Must have the same number of keys

  for (const key of keys1) {
    if (!keys2.includes(key) || !CompareObjects(obj1[key], obj2[key])) {
      return false; // Recursively check nested values
    }
  }

  return true;
};
