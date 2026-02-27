"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.applicationGenerator = applicationGenerator;
const devkit_1 = require("@nx/devkit");
const log_show_project_command_1 = require("@nx/devkit/src/utils/log-show-project-command");
const js_1 = require("@nx/js");
const convert_to_rspack_1 = require("../convert-to-rspack/convert-to-rspack");
const init_1 = require("../init/init");
const setup_ssr_1 = require("../setup-ssr/setup-ssr");
const setup_tailwind_1 = require("../setup-tailwind/setup-tailwind");
const ensure_angular_dependencies_1 = require("../utils/ensure-angular-dependencies");
const validations_1 = require("../utils/validations");
const version_utils_1 = require("../utils/version-utils");
const lib_1 = require("./lib");
async function applicationGenerator(tree, schema) {
    (0, validations_1.assertNotUsingTsSolutionSetup)(tree, 'application');
    (0, lib_1.validateOptions)(tree, schema);
    const isRspack = schema.bundler === 'rspack';
    if (isRspack) {
        schema.bundler = 'webpack';
    }
    const options = await (0, lib_1.normalizeOptions)(tree, schema, isRspack);
    const rootOffset = (0, devkit_1.offsetFromRoot)(options.appProjectRoot);
    await (0, js_1.initGenerator)(tree, {
        ...options,
        tsConfigName: options.rootProject ? 'tsconfig.json' : 'tsconfig.base.json',
        js: false,
        skipFormat: true,
    });
    await (0, init_1.angularInitGenerator)(tree, {
        ...options,
        skipFormat: true,
        addPlugin: options.addPlugin,
    });
    if (!options.skipPackageJson) {
        (0, ensure_angular_dependencies_1.ensureAngularDependencies)(tree, options.zoneless);
    }
    (0, lib_1.createProject)(tree, options);
    await (0, lib_1.createFiles)(tree, options, rootOffset);
    if (options.addTailwind) {
        await (0, setup_tailwind_1.setupTailwindGenerator)(tree, {
            project: options.name,
            skipFormat: true,
            skipPackageJson: options.skipPackageJson,
        });
    }
    await (0, lib_1.addLinting)(tree, options);
    await (0, lib_1.addUnitTestRunner)(tree, options);
    const e2ePort = await (0, lib_1.addE2e)(tree, options);
    (0, lib_1.addServeStaticTarget)(tree, options, options.e2eTestRunner !== 'none' ? e2ePort : options.port);
    (0, lib_1.updateTsconfigFiles)(tree, options);
    (0, lib_1.setGeneratorDefaults)(tree, options);
    if (options.rootProject) {
        const nxJson = (0, devkit_1.readNxJson)(tree);
        nxJson.defaultProject = options.name;
        (0, devkit_1.updateNxJson)(tree, nxJson);
    }
    if (options.backendProject) {
        (0, lib_1.addProxyConfig)(tree, options);
    }
    if (options.ssr) {
        await (0, setup_ssr_1.setupSsr)(tree, {
            project: options.name,
            standalone: options.standalone,
            skipPackageJson: options.skipPackageJson,
            serverRouting: options.serverRouting,
        });
    }
    if (isRspack) {
        await (0, convert_to_rspack_1.convertToRspack)(tree, {
            project: options.name,
            skipInstall: options.skipPackageJson,
            skipFormat: true,
        });
        if (options.ssr) {
            const { major: angularMajorVersion } = (0, version_utils_1.getInstalledAngularVersionInfo)(tree);
            (0, devkit_1.generateFiles)(tree, (0, devkit_1.joinPathFragments)(__dirname, './files/rspack-ssr'), options.appProjectSourceRoot, {
                pathToDistFolder: (0, devkit_1.joinPathFragments)((0, devkit_1.offsetFromRoot)(options.appProjectRoot), options.outputPath, 'browser'),
                zoneless: options.zoneless,
                useDefaultImport: angularMajorVersion >= 21,
                angularMajorVersion,
                tmpl: '',
            });
        }
    }
    if (!options.skipPackageJson) {
        const { major: angularMajorVersion } = (0, version_utils_1.getInstalledAngularVersionInfo)(tree);
        const devDependencies = {};
        const packageVersions = (0, version_utils_1.versions)(tree);
        if (angularMajorVersion >= 20) {
            const angularDevkitVersion = (0, version_utils_1.getInstalledAngularDevkitVersion)(tree) ??
                packageVersions.angularDevkitVersion;
            if (options.bundler === 'esbuild') {
                devDependencies['@angular/build'] = angularDevkitVersion;
            }
            else if (isRspack) {
                devDependencies['@angular/build'] = angularDevkitVersion;
                devDependencies['@angular-devkit/build-angular'] = angularDevkitVersion;
            }
            else {
                devDependencies['@angular-devkit/build-angular'] = angularDevkitVersion;
            }
        }
        if (options.style === 'less') {
            devDependencies['less'] = packageVersions.lessVersion;
        }
        if (Object.keys(devDependencies).length) {
            (0, devkit_1.addDependenciesToPackageJson)(tree, {}, devDependencies, undefined, true);
        }
    }
    if (!options.skipFormat) {
        await (0, devkit_1.formatFiles)(tree);
    }
    return () => {
        (0, devkit_1.installPackagesTask)(tree);
        (0, log_show_project_command_1.logShowProjectCommand)(options.name);
    };
}
exports.default = applicationGenerator;
