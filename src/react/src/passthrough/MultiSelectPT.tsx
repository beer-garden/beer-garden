import { FindPropLabel } from "../passthrough/HelperPT";

export const MultiSelectPT = ({ props }: { props: any }) => {
  return {
    dropdownIcon: {
      role: "img",
      "aria-label": `${FindPropLabel(props)}: Multiselect Icon`,
    },
    input: {
      autoComplete: "off",
      "aria-label": `${FindPropLabel(props)}: Multiselect`,
    },
    headerCheckbox: {
      input: {
        "aria-label": `${FindPropLabel(props)}: Multiselect Header Checkbox`,
      },
    },
    list: {
      "aria-label": `${FindPropLabel(props)}: Multiselect Options List`,
    },
    checkboxContainer: {
      root: {
        input: {
          "aria-label": `${FindPropLabel(props)}: Multiselect Option Checkbox`,
        },
      },
    },
    item: ({ context }: { context: any }) => {
      return {
        style: context?.selected
          ? {
              backgroundColor: "var(--info-background-color)",
              color: "var(--info-color)",
            }
          : {},
      };
    },
  };
};
