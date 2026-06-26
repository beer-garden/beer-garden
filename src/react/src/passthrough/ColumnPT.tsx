import { ColumnPassThroughOptions } from "primereact/column";

export const ColumnPT = ({
  props,
}: {
  props: any;
}): ColumnPassThroughOptions => {
  if (props && props?.sortable === true) {
    return {
      sortIcon: {
        role: "img",
        "aria-label": `Toggle Sort for Column ${props.header ?? props.field}`,
      },
    };
  }
  return {};
};
