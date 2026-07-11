import React from "react";
import { createRoot } from "react-dom/client";
import { MsalProvider } from "@azure/msal-react";
import App from "./App.jsx";
import { msalInstance } from "./authConfig.js";
import "./styles.css";

// Phase C: when Entra is configured the app is wrapped in an MsalProvider and we
// initialise MSAL + drain any redirect response before the first render. When
// it's not (local dev, no VITE_AAD_* vars) msalInstance is null and the app
// renders straight away, unauthenticated — same as before.
const root = createRoot(document.getElementById("root"));

const render = () => {
  root.render(
    <React.StrictMode>
      {msalInstance ? (
        <MsalProvider instance={msalInstance}>
          <App />
        </MsalProvider>
      ) : (
        <App />
      )}
    </React.StrictMode>
  );
};

if (msalInstance) {
  msalInstance
    .initialize()
    .then(() => msalInstance.handleRedirectPromise())
    .then((result) => {
      // After an interactive redirect, adopt the returned account as active.
      if (result?.account) msalInstance.setActiveAccount(result.account);
      else if (!msalInstance.getActiveAccount()) {
        const [first] = msalInstance.getAllAccounts();
        if (first) msalInstance.setActiveAccount(first);
      }
      render();
    })
    .catch((err) => {
      // Without this, any MSAL init / redirect-drain rejection (bad config, an
      // AADSTS error, a cancelled sign-in) would leave render() uncalled and the
      // deployed SPA permanently blank with no message. Mount anyway so the
      // sign-in gate (or the error) is at least visible. Azure-only path —
      // msalInstance is null in local dev, so this never fires there.
      // Log a stable message in all builds; the raw MSAL error object (which can
      // carry tokens/claims/URLs) only in dev, never in the deployed console.
      console.error("[auth] MSAL initialisation failed; rendering the app unauthenticated");
      if (import.meta.env.DEV) console.error(err);
      render();
    });
} else {
  render();
}
