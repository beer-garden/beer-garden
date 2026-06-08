export const DataTablePT = {
  paginator: {
    firstPageIcon: {
      role: "img",
      "aria-label": "First Paginator Icon",
    },
    prevPageIcon: {
      role: "img",
      "aria-label": "Previous Paginator Icon",
    },
    nextPageIcon: {
      role: "img",
      "aria-label": "Next Paginator Icon",
    },
    lastPageIcon: {
      role: "img",
      "aria-label": "Last Paginator Icon",
    },
  },
  column: ({ props }: { props: any }) => {
    let pt = {};
    if (props && props?.sortable === true) {
      pt = {
        ...pt,
        sortIcon: {
          role: "img",
          "aria-label": `Toggle Sort for Column ${props.header ?? props.field}`,
        },
      };
    }
    if (props && ["multiple", "checkbox"].includes(props.selectionMode)) {
      pt = {
        ...pt,
        rowCheckbox: {
          root: {
            "aria-label": undefined,
            "aria-checked": undefined,
            role: undefined,
          },
        },
        headerCheckbox: {
          root: {
            "aria-label": undefined,
            "aria-checked": undefined,
            role: undefined,
          },
        },
      };
    }

    return pt;
  },
};
