export const FindPropLabel = (props: any) => {
  return (
    props.tooltip ??
    props["aria-label"] ??
    props.placeholder ??
    props.optionLabel ??
    props.id ??
    "MISSING REF"
  );
};
