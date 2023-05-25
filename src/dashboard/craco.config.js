const { getThemeVariables } = require("antd/dist/theme");

module.exports = {
  plugins: [
    {
      plugin: require("craco-antd"),
      options: {
        customizeTheme: {
          ...getThemeVariables({ dark: true }),
          "@primary-color": "#EF8934",
          "@border-radius-base": "6px",
          "@form-vertical-label-padding": "3px",
        },
      },
    },
  ],
};
