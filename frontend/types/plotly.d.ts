declare module "plotly.js-dist-min" {
  const Plotly: {
    react: (
      el: HTMLElement | null,
      data: unknown,
      layout: unknown,
      config: unknown,
    ) => void | Promise<void>;
    newPlot: (el: HTMLElement | null, data: unknown, layout?: unknown, config?: unknown) => void | Promise<void>;
    purge: (el: HTMLElement | null) => void;
  };
  export default Plotly;
}
