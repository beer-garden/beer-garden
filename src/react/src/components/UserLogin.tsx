import {
  Alert,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
} from "@mui/material";
import TextField from "@mui/material/TextField";
import { useState } from "react";

import { UserLogin } from "../services/token_service";
import { FAIcon } from "../services/util_service";
import AccessButton from "./AccessButton";

const LoginDialog = ({
  visible,
  setVisible,
  setUsernameDisplay,
}: {
  visible: boolean;
  setVisible: any;
  setUsernameDisplay: any;
}) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [showFailedLogin, setShowFailedLogin] = useState(false);

  const handleLogin = () => {
    setShowFailedLogin(false);
    UserLogin(username, password)
      .then(() => {
        setVisible(false);
        setUsernameDisplay(username);
        setUsername("");
        setPassword("");
      })
      .catch((error) => {
        console.error(`Error Logging in ${error}`);
        setShowFailedLogin(true);
      });
  };

  return (
    <Dialog
      open={visible}
      onClose={() => setVisible(false)}
      aria-labelledby="login-dialog-title"
    >
      <DialogTitle id="login-dialog-title">Login</DialogTitle>
      <DialogContent>
        <Stack spacing={2}>
          {showFailedLogin && (
            <Alert severity="error">Incorrect username or password</Alert>
          )}
          <TextField
            id="username"
            label="Username"
            value={username}
            required
            onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
              setUsername(event.target.value);
            }}
          />
          <TextField
            id="password"
            label="Password"
            type="password"
            value={password}
            autoComplete="current-password"
            onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
              setPassword(event.target.value);
            }}
          />
        </Stack>
      </DialogContent>
      <DialogActions sx={{ justifyContent: "center" }}>
        <AccessButton
          label="Cancel"
          onClick={() => setVisible(false)}
          sx={{ mr: 1 }}
          text
        >
          <FAIcon icon="xmark" sx={{ mr: 1 }} />
          Cancel
        </AccessButton>
        <AccessButton label="Login" onClick={handleLogin} sx={{ mr: 1 }}>
          <FAIcon icon="check" sx={{ mr: 1 }} />
          Login
        </AccessButton>
      </DialogActions>
    </Dialog>
  );
};

export default LoginDialog;
