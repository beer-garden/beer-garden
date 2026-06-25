import { AutoCompletePassThroughOptions } from "primereact/autocomplete";

import { FindPropLabel } from "../passthrough/HelperPT";

export const AutoCompletePT = ({
  props,
}: {
  props: any;
}): AutoCompletePassThroughOptions => {
  return {
    root: {
      "aria-description": `${FindPropLabel(props)}: Type to search available options, controls popup hidden from DOM until generated`,
      listwrapper: {
        role: "region",
        "aria-label": `${FindPropLabel(props)}: Available options`,
        tabIndex: 0,
      },
    },
    input: {
      root: {
        "aria-label": `${FindPropLabel(props)}: String with Typeahead input`,
      },
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
