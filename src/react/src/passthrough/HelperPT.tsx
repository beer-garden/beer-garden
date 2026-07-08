export const FindPropLabel = (props: any) => {
  if (props.tooltip) {
    return props.tooltip;
  }

  if (Object.hasOwn(props, "aria-label") && props["aria-label"]) {
    return props["aria-label"];
  }

  if (props.placeholder) {
    return props.placeholder;
  }

  if (props.optionLabel) {
    return props.optionLabel;
  }

  if (props.id) {
    return props.id;
  }

  if (props.header) {
    return props.header;
  }

  if (props.label) {
    return props.label;
  }

  if (
    props?.pt &&
    Object.hasOwn(props.pt, "aria-label") &&
    props.pt["aria-label"]
  ) {
    return props.pt["aria-label"];
  }

  return "MISSING REF";
};
