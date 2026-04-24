import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Dropdown } from "primereact/dropdown";
import { ToggleButton } from "primereact/togglebutton";
import { useEffect, useState } from "react";

import { ChangeTheme, ThemeOptions } from "../services/util_service";

function ChangeThemeDialog() {
  const [color, setColor] = useState<string>(
    localStorage.getItem("theme_color") || "blue",
  );
  const [dark, setDark] = useState<boolean>(
    localStorage.getItem("theme_dark") === "true" || false,
  );

  useEffect(() => {
    ChangeTheme(color, dark);
  }, [color, dark]);

  return (
    <>
      <div className="flex">
        <Dropdown
          value={color}
          onChange={(e) => setColor(e.value)}
          options={ThemeOptions()}
          optionLabel="Color"
          placeholder="Select a Color"
          className="mr-2"
        />

        <ToggleButton
          onLabel="Dark Mode"
          offLabel="Light Mode"
          offIcon={<FontAwesomeIcon className="mr-2" icon="sun" />}
          onIcon={<FontAwesomeIcon className="mr-2" icon="moon" />}
          checked={dark}
          onChange={(e) => setDark(e.value)}
        />
      </div>
    </>
  );
}

export default ChangeThemeDialog;
