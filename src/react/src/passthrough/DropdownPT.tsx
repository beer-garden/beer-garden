import { FindPropLabel } from "../passthrough/HelperPT";

export const DropdownPT = ({ props }: { props: any }) => {
  return {
    dropdownIcon: {
      role: "img",
      "aria-label": `${FindPropLabel(props)}: Dropdown Icon`,
    },
    input: {
      autoComplete: "off",
    },
    select: {
      autoComplete: "off",
      "aria-label": `${FindPropLabel(props)}: Select`,
    },
    trigger: {
      "aria-label": `${FindPropLabel(props)}: Dropdown trigger`,
    },
  };
};
