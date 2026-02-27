"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.updateApplicationStyles = updateApplicationStyles;
const devkit_1 = require("@nx/devkit");
const ts_solution_setup_1 = require("@nx/js/src/utils/typescript/ts-solution-setup");
function updateApplicationStyles(tree, options, project) {
    let stylesEntryPoint = options.stylesEntryPoint;
    if (stylesEntryPoint && !tree.exists(stylesEntryPoint)) {
        throw new Error(`The provided styles entry point "${stylesEntryPoint}" could not be found.`);
    }
    if (!stylesEntryPoint) {
        stylesEntryPoint = findStylesEntryPoint(tree, options, project);
        if (!stylesEntryPoint) {
            throw new Error((0, devkit_1.stripIndents) `Could not find a styles entry point for project "${options.project}".
        Please specify a styles entry point using the "--stylesEntryPoint" option.`);
        }
    }
    const stylesEntryPointContent = tree.read(stylesEntryPoint, 'utf-8');
    tree.write(stylesEntryPoint, (0, devkit_1.stripIndents) `@tailwind base;
    @tailwind components;
    @tailwind utilities;

    ${stylesEntryPointContent}`);
}
function findStylesEntryPoint(tree, options, project) {
    const sourceRoot = (0, ts_solution_setup_1.getProjectSourceRoot)(project, tree);
    // first check for common names
    const possibleStylesEntryPoints = [
        (0, devkit_1.joinPathFragments)(sourceRoot, 'styles.css'),
        (0, devkit_1.joinPathFragments)(sourceRoot, 'styles.scss'),
        (0, devkit_1.joinPathFragments)(sourceRoot, 'styles.sass'),
        (0, devkit_1.joinPathFragments)(sourceRoot, 'styles.less'),
    ];
    let stylesEntryPoint = possibleStylesEntryPoints.find((s) => tree.exists(s));
    if (stylesEntryPoint) {
        return stylesEntryPoint;
    }
    // then check for the specified styles in the build configuration if it exists
    const styles = project.targets?.[options.buildTarget]?.options?.styles;
    if (!styles) {
        return undefined;
    }
    // find the first style that belongs to the project source
    const style = styles.find((s) => typeof s === 'string'
        ? s.startsWith(project.root) && tree.exists(s)
        : s.input.startsWith(project.root) &&
            s.inject !== false &&
            tree.exists(s.input));
    if (!style) {
        return undefined;
    }
    return typeof style === 'string' ? style : style.input;
}
