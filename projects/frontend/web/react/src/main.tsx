import { BrowserRouter } from "react-router";
import ReactDOM  from "react-dom/client";
import App from "./App.tsx";
import "./index.css";


const root = document.getElementById("root");

ReactDOM.createRoot(root).render(
  <BrowserRouter>
    <App />
  </BrowserRouter>,
);
