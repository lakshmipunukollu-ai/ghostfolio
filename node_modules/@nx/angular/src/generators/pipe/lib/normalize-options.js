"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.normalizeOptions = normalizeOptions;
const devkit_1 = require("@nx/devkit");
const artifact_name_and_directory_utils_1 = require("@nx/devkit/src/generators/artifact-name-and-directory-utils");
const validations_1 = require("../../utils/validations");
const version_utils_1 = require("../../utils/version-utils");
async function normalizeOptions(tree, options) {
    const { major: angularMajorVersion } = (0, version_utils_1.getInstalledAngularVersionInfo)(tree);
    options.typeSeparator ??= angularMajorVersion < 20 ? '.' : '-';
    const { artifactName: name, directory, fileName, filePath, project: projectName, } = await (0, artifact_name_and_directory_utils_1.determineArtifactNameAndDirectoryOptions)(tree, {
        name: options.name,
        path: options.path,
        suffix: 'pipe',
        suffixSeparator: options.typeSeparator,
        allowedFileExtensions: ['ts'],
        fileExtension: 'ts',
    });
    const { className } = (0, devkit_1.names)(name);
    const { className: suffixClassName } = (0, devkit_1.names)('pipe');
    const symbolName = `${className}${suffixClassName}`;
    (0, validations_1.validateClassName)(symbolName);
    return {
        ...options,
        projectName,
        name,
        directory,
        fileName,
        filePath,
        symbolName,
        standalone: options.standalone ?? true,
    };
}
