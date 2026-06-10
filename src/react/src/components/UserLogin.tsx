import { Dialog } from "primereact/dialog";
import { InputText } from "primereact/inputtext";
import { Messages } from "primereact/messages";
import { Password } from "primereact/password";
import { classNames } from "primereact/utils";
import { useRef, useState } from "react";

import { UserLogin } from "../services/token_service";
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
  const msgs = useRef<Messages>(null);

  const handleLogin = () => {
    msgs.current?.clear();
    UserLogin(username, password)
      .then(() => {
        setVisible(false);
        setUsernameDisplay(username);
        setUsername("");
        setPassword("");
      })
      .catch((error) => {
        console.error(`Error Logging in ${error}`);
        msgs.current?.show({
          severity: "error",
          detail: "Incorrect username or password",
          sticky: true,
        });
      });
  };

  const dialogFooter = (
    <div>
      <AccessButton
        label="Cancel"
        icon="pi pi-times"
        onClick={() => setVisible(false)}
        className="p-button-text"
      />
      <AccessButton label="Login" icon="pi pi-check" onClick={handleLogin} />
    </div>
  );

  return (
    <Dialog
      header="Login"
      visible={visible}
      style={{ width: "50vw" }}
      breakpoints={{ "960px": "75vw", "640px": "100vw" }}
      onHide={() => setVisible(false)}
      footer={dialogFooter}
    >
      <Messages ref={msgs} />
      <div className="flex flex-column gap-3 p-input-filled">
        <div className="flex flex-column gap-2">
          <label htmlFor="username">Username</label>
          <InputText
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className={classNames({ "p-invalid": !username && visible })}
            aria-describedby="username-help"
          />
        </div>
        <div className="flex flex-column gap-2">
          <label htmlFor="password">Password</label>
          <Password
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            toggleMask
            feedback={false}
          />
        </div>
      </div>
    </Dialog>
  );
};

export default LoginDialog;
