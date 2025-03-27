// types/react-plotly.d.ts
import "react-plotly.js";
import { PlotlyHTMLElement } from "plotly.js";

declare module "react-plotly.js" {
  interface PlotProps {
    ref?: React.Ref<PlotlyHTMLElement>;
  }
}
