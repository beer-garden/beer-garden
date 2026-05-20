import { Panel } from "primereact/panel";

function ErrorPage({
  errorCode,
  errorMsg,
  isCard,
}: {
  errorCode?: number;
  errorMsg?: string;
  isCard?: boolean;
}) {
  function errorType(errorCode: number | undefined) {
    switch (errorCode) {
      case 400:
        return "400 Bad Request";
      case 401:
        return "401 Unauthorized";
      case 404:
        return "404 Not Found";
      case undefined:
        return "Error";
      default:
        return `${errorCode} Error`;
    }
  }

  return (
    <div>
      {!isCard && <h1 className="flex m-2">{errorType(errorCode)}</h1>}
      <div className="flex">
        <Panel
          header={isCard ? errorType(errorCode) : "Details"}
          className="m-2 flex-1"
        >
          {errorMsg ? (
            <p className="al">{errorMsg}</p>
          ) : (
            <p className="al">
              This page isn't available. Please try something else.
            </p>
          )}
        </Panel>
      </div>
    </div>
  );
}

export default ErrorPage;
