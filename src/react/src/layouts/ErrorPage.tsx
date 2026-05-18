import { Panel } from "primereact/panel";

function ErrorPage({
  errorCode,
  errorMsg,
}: {
  errorCode?: number;
  errorMsg?: string;
}) {
  function errorType(errorCode: number) {
    switch (errorCode) {
      case 400:
        return "Bad Request";
      case 401:
        return "Unauthorized";
      case 404:
        return "Not Found";
      default:
        return "Error";
    }
  }

  return (
    <div>
      <h1 className="flex m-2">{errorType(errorCode)}</h1>
      <div className="flex">
        <Panel header="Details" className="m-2 flex-1">
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
