// @ts-nocheck
/* eslint @typescript-eslint/no-var-requires: "off" */

/* Build tools */
const gulp = require("gulp");
const concat = require("gulp-concat");
const rename = require("gulp-rename");

/* Build modules for scripts */
const commonjs = require("@rollup/plugin-commonjs"); // loader
const eslint = require("@rollup/plugin-eslint"); // linter
const { babel } = require("@rollup/plugin-babel"); // transpiler + polyfills
const resolve = require("@rollup/plugin-node-resolve"); // loader
const nodeResolve = resolve.default;
const strip = require("@rollup/plugin-strip"); // remove console statements
const rollup = require("rollup"); // bundler
const { terser } = require("rollup-plugin-terser"); // minifier
const embedCSS = require("rollup-plugin-postcss");
const alias = require("@rollup/plugin-alias");
const replace = require("@rollup/plugin-replace");
const ts = require("gulp-typescript"); // typescript
const tsProject = ts.createProject("tsconfig.json");

/* Build modules for styles */
const scssLint = require("stylelint"); // linter
const cssMinify = require("cssnano"); // minifier
const cssPolyfills = require("postcss-preset-env"); // autoprefixer + polyfills
const postcss = require("gulp-postcss"); // css
//const failOnWarn = require("postcss-fail-on-warn"); // fail on warnings
const scss = require("postcss-scss"); // understand scss syntax
const sass = require("csstools-postcss-sass-pre-release"); // sass compiler
const sourcemaps = require("gulp-sourcemaps"); // sourcemaps

/* Build for icons */
const svgSprite = require("gulp-svg-sprite");

const { existsSync } = require("fs");

const templateModules = ["peerinst", "quality", "reputation", "tos"];

const styleBuilds = [
  {
    app: "peerinst",
    modules: [
      "group",
      "student",
      "question",
      "collection",
      "teacher",
      "layout",
      "admin",
      "main",
      "mdc",
      "rmwc",
      "cookie_law",
      "error",
      "search",
      "landing_page",
      "email",
      "material-web",
      "tiny",
    ],
  },
  {
    app: "quality",
    modules: ["edit"],
  },
];

const scriptBuilds = [
  {
    app: "peerinst",
    modules: [
      "account",
      "group",
      "student",
      // "search",
      "index",
      "preview",
      "question",
      "teacher",
      // "custom_elements",
      "teacher",
      "collection",
      // "admin",
      // "ajax",
      "preact",
      "material-web",
    ],
  },
  {
    app: "tos",
    modules: ["email"],
  },
  {
    app: "quality",
    modules: ["edit"],
  },
];

function buildStyle(app, module) {
  const cb = (file) => {
    // https://github.com/postcss/gulp-postcss#advanced-usage
    return {
      plugins: [
        scssLint(),
        sass({ includePaths: ["./node_modules"] }),
        cssPolyfills(),
        cssMinify(),
        //failOnWarn(),
      ],
      options: {
        parser: scss,
      },
    };
  };
  const build = gulp
    .src(
      [
        `./${app}/static/${app}/css/${module}/**/*.scss`,
        `./${app}/static/${app}/css/${module}.scss`,
      ],
      { allowEmpty: true },
    )
    .pipe(sourcemaps.init())
    .pipe(postcss(cb))
    .pipe(concat(`${module}.min.css`))
    .pipe(sourcemaps.write("."))
    .pipe(gulp.dest(`./${app}/static/${app}/css`));

  return build;
}

function watchStyle(app, module) {
  gulp.watch(
    [
      `./${app}/static/${app}/css/${module}/**/*.scss`,
      `./${app}/static/${app}/css/${module}.scss`,
    ],
    () => buildStyle(app, module),
  );
}

function typescript() {
  const build = gulp
    .src(["**/*.tsx"])
    // .src([
    //   "{analytics,peerinst,reputation,quality,tos}/**/*.{ts,tsx,js,jsx}",
    //   "!**/*.min.js",
    //   "!**/tinymce/**/*.js",
    // ])
    .pipe(tsProject());

  return build;
}

function buildScript(app, module) {
  const name = module === "index" ? "bundle" : module;
  // While migrating to typescript, we need to check for all file extensions
  const file = existsSync(`./${app}/static/${app}/js/${module}.js`)
    ? `./${app}/static/${app}/js/${module}.js`
    : existsSync(`./${app}/static/${app}/js/${module}.ts`)
    ? `./${app}/static/${app}/js/${module}.ts`
    : existsSync(`./${app}/static/${app}/js/${module}.tsx`)
    ? `./${app}/static/${app}/js/${module}.tsx`
    : `./${app}/static/${app}/js/${module}.jsx`;
  const inputOptions = {
    input: file,
    external: [
      "jquery",
      "flatpickr",
      "@babel/runtime",
      "@material/auto-init",
      "material/checkbox",
      "material/chips",
      "material/dialog",
      "@material/drawer",
      "@material/icon-toggle",
      "@material/radio",
      "material/select",
      "@material/toolbar",
      "material/snackbar",
    ],
    onwarn(warning, warn) {
      if (warning.code === "CIRCULAR_DEPENDENCY") return;
      warn(warning);
    },
    plugins: [
      alias({
        entries: [
          { find: "react", replacement: "preact/compat" },
          { find: "react-dom", replacement: "preact/compat" },
        ],
      }),
      replace({
        preventAssignment: true,
        "process.env.NODE_ENV": JSON.stringify("production"),
      }),
      eslint({
        fix: true,
      }),
      embedCSS({ extract: true }),
      // https://github.com/rollup/plugins/tree/master/packages/commonjs#using-with-rollupplugin-node-resolve
      nodeResolve({
        extensions: [".js", ".jsx", ".ts", ".tsx"],
        mainFields: ["module", "main", "browser"],
      }),
      commonjs(),
      // https://github.com/rollup/plugins/tree/master/packages/babel#using-with-rollupplugin-commonjs
      babel({
        babelHelpers: "bundled",
        exclude: "node_modules/**",
        extensions: [".js", ".jsx", ".ts", ".tsx"],
      }),
      // strip({ include: ["**/*.(js|jsx|ts|tsx)"] }),
    ],
  };
  const outputOptions = {
    extend: true,
    file: `./${app}/static/${app}/js/${module}.min.js`,
    format: "iife",
    globals: {
      jquery: "jquery",
      flatpickr: "flatpickr",
      "@babel/runtime": "@babel/runtime",
      "@material/auto-init": "@material/auto-init",
      "@material/checkbox": "@material/checkbox",
      "@material/chips": "@material/chips",
      "@material/dialog": "material/dialog",
      "@material/drawer": "@material/drawer",
      "@material/icon-toggle": "@material/icon-toggle",
      "@material/radio": "@material/radio",
      "@material/select": "material/select",
      "@material/toolbar": "@material/toolbar",
      "material/snackbar": "material/snackbar",
    },
    name,
    plugins: [
      terser({
        mangle: {
          reserved: ["gettext"],
        },
      }),
    ],
    sourcemap: true,
  };

  return rollup
    .rollup(inputOptions)
    .then((bundle) => bundle.write(outputOptions));
}

function watchScript(app, module) {
  gulp.watch(
    [
      `./${app}/static/${app}/js/_${module}/**/*.{js,jsx,ts,tsx}`,
      `./${app}/static/${app}/js/${module}.{js,jsx,ts,tsx}`,
    ],
    () => buildScript(app, module),
  );
}

function icons() {
  return gulp
    .src("./templates/icons/*.svg")
    .pipe(
      svgSprite({
        mode: {
          symbol: {
            inline: true,
          },
        },
        svg: {
          namespaceIDs: false,
          rootAttributes: {
            class: "svg-sprite",
          },
          transform: [(svg) => svg.replace(/style="[^"]*"/g, "")],
        },
      }),
    )
    .pipe(rename("icons.svg"))
    .pipe(gulp.dest("./templates/"))
    .pipe(gulp.dest("./peerinst/static/peerinst/"));
}

function watch() {
  styleBuilds.forEach((s) => s.modules.forEach((m) => watchStyle(s.app, m)));
  scriptBuilds.forEach((s) => s.modules.forEach((m) => watchScript(s.app, m)));
  gulp.watch(
    [
      "./peerinst/static/peerinst/js/*.js",
      "!./peerinst/static/peerinst/js/*.min.js*",
      "!./peerinst/static/peerinst/js/utils.js",
    ].concat(
      scriptBuilds
        .filter((s) => s.app === "peerinst")
        .map((s) => s.modules)
        .filter((m) => m !== "index")
        .map((m) => `./peerinst/static/peerinst/js/${m}.js`),
    ),
    () => buildScript("peerinst", "index"),
  );
  gulp.watch("./peerinst/static/peerinst/icons/*.svg", icons);
  templateModules.forEach((app) => gulp.watch(`./${app}/templates/**/*.html`));
}

const styles = gulp.parallel(
  ...[].concat(
    ...styleBuilds.map((s) =>
      s.modules.map((m) => {
        function task() {
          return buildStyle(s.app, m);
        }
        task.displayName = `${s.app} > ${m}`;
        return task;
      }),
    ),
  ),
);

const scripts = gulp.parallel(
  ...[].concat(
    ...scriptBuilds.map((s) =>
      s.modules.map((m) => {
        function task() {
          return buildScript(s.app, m);
        }
        task.displayName = `${s.app} > ${m}`;
        return task;
      }),
    ),
  ),
);

const typecheck = gulp.series(typescript, scripts);
const build = gulp.parallel(styles, scripts, icons);
const dev = gulp.series(build, watch);

exports.build = build;
exports.watch = watch;
exports.dev = dev;
exports.styles = styles;
exports.scripts = scripts;
exports.typescript = typescript;
exports.typecheck = typecheck;
exports.icons = icons;
