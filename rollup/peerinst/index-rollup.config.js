import babel from "rollup-plugin-babel";
import eslint from "rollup-plugin-eslint";
import resolve from "rollup-plugin-node-resolve";
import commonjs from "rollup-plugin-commonjs";
import uglify from "rollup-plugin-uglify";

export default {
  input: "peerinst/static/peerinst/js/index.js",
  output: {
    file: "peerinst/static/peerinst/js/index.min.js",
    name: "bundle",
    format: "iife",
    sourceMap: "inline",
  },
  plugins: [
    resolve({
      jsnext: true,
      main: true,
      browser: true,
    }),
    commonjs(),
    eslint({
      exclude: ["**.css"],
    }),
    babel({
      exclude: ["node_modules/d3/**"],
    }),
    uglify(),
  ],
};
