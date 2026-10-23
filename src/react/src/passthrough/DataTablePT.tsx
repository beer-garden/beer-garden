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
    if (props && props?.sortable === true) {
      return {
        sortIcon: {
          role: "img",
          "aria-label": `Toggle Sort for Column ${props.header ?? props.field}`,
        },
      };
    }
  },
};
