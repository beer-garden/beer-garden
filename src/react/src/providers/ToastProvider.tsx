import { Toast } from "primereact/toast";
import { createContext, ReactNode, useContext, useRef } from "react";

export interface ToastArgs {
  severity: "success" | "info" | "warn" | "error";
  summary: string;
  detail: string;
  life: number;
}

interface ToastContextType {
  showToast: (args: ToastArgs) => void;
}

// Create the context
const ToastContext = createContext<ToastContextType | undefined>(undefined);

// Create the Provider Component
export const ToastProvider = ({ children }: { children: ReactNode }) => {
  const toast = useRef<Toast>(null);

  const showToast = (args: ToastArgs) => {
    toast.current?.show(args);
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      <Toast ref={toast} />
      {children}
    </ToastContext.Provider>
  );
};

// Create a custom hook for consuming the context
export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context.showToast;
};
