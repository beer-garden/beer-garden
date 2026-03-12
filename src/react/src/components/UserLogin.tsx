import { Button } from "primereact/button";
import { Dialog } from "primereact/dialog";
import { InputText } from "primereact/inputtext";
import { Password } from "primereact/password";
import { classNames } from "primereact/utils";
import { useState } from "react";

import { UserLogin } from "../services/token_service";

const LoginDialog = ({
  visible,
  setVisible,
}: {
  visible: boolean;
  setVisible: any;
}) => {
  // const [visible, setVisible] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = () => {
    UserLogin(username, password)
      .then(() => {
        setVisible(false);
        setUsername("");
        setPassword("");
      })
      .catch((error) => {
        // should throw an alert for the user
        console.log(`Error Logging in ${error}`);
      });
  };

  const dialogFooter = (
    <div>
      <Button
        label="Cancel"
        icon="pi pi-times"
        onClick={() => setVisible(false)}
        className="p-button-text"
      />
      <Button label="Login" icon="pi pi-check" onClick={handleLogin} />
    </div>
  );

  return (
    // <div className="card flex justify-content-center">
    // <Button label="Show Login" icon="pi pi-external-link" onClick={() => setVisible(true)} />

    <Dialog
      header="Login"
      visible={visible}
      style={{ width: "50vw" }}
      breakpoints={{ "960px": "75vw", "640px": "100vw" }}
      onHide={() => setVisible(false)}
      footer={dialogFooter}
    >
      <div className="flex flex-column gap-3 p-input-filled">
        <div className="flex flex-column gap-2">
          <label htmlFor="username">Username</label>
          <InputText
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className={classNames({ "p-invalid": !username && visible })} // Example validation styling
            aria-describedby="username-help"
          />
          {/* <small id="username-help">Enter your username.</small> */}
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
    // </div>
  );
};

export default LoginDialog;
