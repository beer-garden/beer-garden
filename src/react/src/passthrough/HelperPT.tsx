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

  if (props?.pt) {
    return FindPropLabel(props.pt);
  }

  if (props?.label) {
    return props.label;
  }

  if (
    props?.__parentMetadata &&
    props.__parentMetadata?.parent &&
    props.__parentMetadata.parent?.props
  ) {
    return FindPropLabel(props.__parentMetadata.parent.props);
  }

  return "MISSING REF";
};
