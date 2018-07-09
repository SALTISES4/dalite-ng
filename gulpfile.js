const gulp = require('gulp');
const rename = require('gulp-rename');
const sass = require('gulp-sass');
const sourcemaps = require('gulp-sourcemaps');
const postcss = require('gulp-postcss');
const autoprefixer = require('autoprefixer');
const runSequence = require('run-sequence');
const concat = require('gulp-concat');
// const rollup = require('rollup-stream');
// const source = require('vinyl-source-stream');

gulp.task('sass', function() {
  return gulp
    .src('./peerinst/static/peerinst/css/main.scss')
    .pipe(rename('main.min.css'))
    .pipe(sourcemaps.init())
    .pipe(
      sass({
        outputStyle: 'compressed',
        includePaths: './node_modules/',
      }),
    )
    .pipe(sourcemaps.write('.'))
    .pipe(gulp.dest('./peerinst/static/peerinst/css/'));
});

gulp.task('autoprefixer', function() {
  return gulp
    .src('./peerinst/static/peerinst/css/main.css')
    .pipe(sourcemaps.init())
    .pipe(postcss([autoprefixer({browsers: ['last 4 versions']})]))
    .pipe(sourcemaps.write('.'))
    .pipe(gulp.dest('./peerinst/static/peerinst/css/'));
});

/* Not working; error thrown
gulp.task('rollup', function() {
  return rollup('rollup.config.js')
    .pipe(source('index.min.js'))
    .pipe(gulp.dest('./peerinst/static/peerinst/js/'));
});*/

gulp.task('rollup', function() {
  const runCommand = require('child_process').execSync;
  runCommand('./node_modules/.bin/rollup -c', function(err, stdout, stderr) {
    console.log('Output: ' + stdout);
    console.log('Error: ' + stderr);
    if (err) {
      console.log('Error: ' + err);
    }
  });
});

gulp.task('build', function(callback) {
  runSequence('sass', 'autoprefixer', 'rollup', callback);
});

gulp.task('tos-styles', function() {
  return gulp
    .src('./tos/static/tos/css/*.scss')
    .pipe(sourcemaps.init())
    .pipe(
      sass({
        outputStyle: 'compressed',
        includePaths: './node_modules',
      }),
    )
    .pipe(postcss([autoprefixer({browsers: ['last 4 versions']})]))
    .pipe(concat('styles.min.css'))
    .pipe(sourcemaps.write('.'))
    .pipe(gulp.dest('tos/static/tos/css'));
});

gulp.task('tos-scripts', function() {
  const runCommand = require('child_process').execSync;
  runCommand(
    './node_modules/.bin/rollup -c ./rollup/tos-rollup.config.js',
    function(err, stdout, stderr) {
      console.log('Output: ' + stdout);
      console.log('Error: ' + stderr);
      if (err) {
        console.log('Error: ' + err);
      }
    },
  );
});

gulp.task('tos-build', function(callback) {
  runSequence('tos-styles', 'tos-scripts', callback);
});

gulp.task('watch', function() {
  gulp.watch('./tos/static/tos/css/*.scss', ['tos-styles']);
  gulp.watch('./tos/static/tos/js/index.js', ['tos-scripts']);
});
