import { Panel } from "primereact/panel";

function ErrorPage({
  errorNum,
  errorMsg,
}: {
  errorNum?: number;
  errorMsg?: string;
}) {
  function errorType(errorNum?: number) {
    switch (errorNum) {
      case 400:
        return "Bad Request";
      case 401:
        return "Unauthorized";
      case 404:
        return "Not Found";
      default:
        return "Something went wrong";
    }
  }

  return (
    <div>
      <h1 className="flex m-2">{errorType(errorNum)}</h1>
      <div className="flex">
        <Panel header="Details" className="m-2 flex-1">
          {errorMsg ? (
            <p>errorMsg</p>
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
