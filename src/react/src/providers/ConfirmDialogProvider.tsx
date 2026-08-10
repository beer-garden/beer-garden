import {
  createContext,
  ReactElement,
  ReactNode,
  useContext,
  useState,
} from "react";

import ConfirmDialog from "../components/ConfirmDialog";

export interface ConfirmDialogArgs {
  accept: () => void;
  reject?: () => void;
  header: string | ReactElement;
  message: string | ReactElement;
}

interface ConfirmDialogContextType {
  showConfirmDialog: (args: ConfirmDialogArgs) => void;
}

// Create the context
const ConfirmDialogContext = createContext<
  ConfirmDialogContextType | undefined
>(undefined);

// Create the Provider Component
export const ConfirmDialogProvider = ({
  children,
}: {
  children: ReactNode;
}) => {
  const [dialogProps, setDialogProps] = useState<ConfirmDialogArgs | undefined>(
    undefined,
  );

  const showConfirmDialog = (args: ConfirmDialogArgs) => {
    setDialogProps(args);
  };

  return (
    <ConfirmDialogContext.Provider value={{ showConfirmDialog }}>
      {dialogProps && (
        <ConfirmDialog
          open={true}
          accept={dialogProps.accept}
          reject={dialogProps.reject}
          closeDialog={() => {
            setDialogProps(undefined);
          }}
          header={dialogProps.header}
          message={dialogProps.message}
        />
      )}
      {children}
    </ConfirmDialogContext.Provider>
  );
};

// Create a custom hook for consuming the context
export const useConfirmDialog = () => {
  const context = useContext(ConfirmDialogContext);
  if (!context) {
    throw new Error(
      "useConfirmDialog must be used within a ConfirmDialogProvider",
    );
  }
  return context.showConfirmDialog;
};
