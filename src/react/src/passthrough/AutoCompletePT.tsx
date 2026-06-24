import { FindPropLabel } from "../passthrough/HelperPT";

export const AutoCompletePT = ({ props }: { props: any }) => {
  return {
    input: {
      // Gets overrided by aria-controls
      "aria-label": `${FindPropLabel(props)}: String with Typeahead input`,
    },
    listwrapper: {
      role: "region",
      "aria-label": `${FindPropLabel(props)}: Available options`,
      tabIndex: 0,
    },
    list: {
      "aria-label": `${FindPropLabel(props)}: List of available options`,
    },
    dropdownButton: {
      icon: {
        role: "img",
        "aria-label": `${FindPropLabel(props)}: Dropdown for Typeahead`,
      },
      root: {
        "aria-label": `${FindPropLabel(props)}: Dropdown for Typeahead, opens list of available options`,
      },
    },
  };
};
