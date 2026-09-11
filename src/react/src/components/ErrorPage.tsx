import { Box, Divider, Typography } from "@mui/material";

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
      {!isCard && (
        <Typography variant="h2" component="h1" sx={{ m: 2 }}>
          {errorType(errorCode)}
        </Typography>
      )}
      <Box sx={{ border: "1px solid grey", m: 2, borderRadius: 2 }}>
        <Box sx={{ bgcolor: "warning.light" }}>
          <Typography
            variant="h2"
            component="h2"
            sx={{ mx: 2, color: "warning.contrastText" }}
          >
            {isCard ? errorType(errorCode) : "Details"}
          </Typography>
        </Box>
        <Divider />
        <Box>
          <Typography sx={{ m: 2 }} variant="body1">
            {errorMsg ?? "This page isn't available. Please try something else"}
          </Typography>
        </Box>
      </Box>
    </div>
  );
}

export default ErrorPage;
