"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.transformCjsConfigFile = transformCjsConfigFile;
const tsquery_1 = require("@phenomnomnominal/tsquery");
function transformCjsConfigFile(tree, configPath) {
    const configContents = tree.read(configPath, 'utf-8');
    const usesJsExtensions = detectJsExtensions(configContents);
    ['@nx', '@nrwl'].forEach((scope) => {
        transformComposePlugins(tree, configPath, scope);
        transformWithNx(tree, configPath, scope);
        transformWithWeb(tree, configPath, scope);
        transformWithReact(tree, configPath, scope);
        transformModuleFederationConfig(tree, configPath, scope);
        transformWithModuleFederation(tree, configPath, scope, usesJsExtensions);
        transformWithModuleFederationSSR(tree, configPath, scope, usesJsExtensions);
    });
    // Add useLegacyHtmlPlugin: true to withWeb() calls
    transformWithWebCalls(tree, configPath);
}
function detectJsExtensions(configContents) {
    // Check if any require calls use .js extensions
    const requireWithJsExtensionRegex = /require\s*\(\s*['"]@nx\/[^'"]*\.js['"]\s*\)/;
    return requireWithJsExtensionRegex.test(configContents);
}
function transformWithWebCalls(tree, configPath) {
    const configContents = tree.read(configPath, 'utf-8');
    const sourceFile = (0, tsquery_1.ast)(configContents);
    // Find withWeb() calls
    const withWebCallNodes = (0, tsquery_1.query)(sourceFile, 'CallExpression > Identifier[name=withWeb]');
    // If there are withWeb calls, update them
    if (withWebCallNodes.length > 0) {
        let newContents = configContents;
        for (const node of withWebCallNodes) {
            const callExpr = node.parent;
            if (!callExpr)
                continue;
            const startPos = callExpr.getStart();
            const endPos = callExpr.getEnd();
            const callText = configContents.substring(startPos, endPos);
            // Skip if useLegacyHtmlPlugin is already present
            if (callText.includes('useLegacyHtmlPlugin')) {
                continue;
            }
            // If it's already withWeb({ ... }), add useLegacyHtmlPlugin: true to the options
            if (callText.includes('{') && callText.includes('}')) {
                const newCallText = callText.replace(/\{\s*/, '{ useLegacyHtmlPlugin: true,\n      ');
                newContents =
                    newContents.substring(0, startPos) +
                        newCallText +
                        newContents.substring(endPos);
            }
            else {
                // If it's just withWeb(), replace with withWeb({ useLegacyHtmlPlugin: true })
                const newCallText = 'withWeb({ useLegacyHtmlPlugin: true })';
                newContents =
                    newContents.substring(0, startPos) +
                        newCallText +
                        newContents.substring(endPos);
            }
        }
        if (newContents !== configContents) {
            tree.write(configPath, newContents);
        }
        return;
    }
    // If no withWeb calls, check for withReact calls
    const withReactCallNodes = (0, tsquery_1.query)(sourceFile, 'CallExpression > Identifier[name=withReact]');
    if (withReactCallNodes.length === 0) {
        return;
    }
    let newContents = configContents;
    for (const node of withReactCallNodes) {
        const callExpr = node.parent;
        if (!callExpr)
            continue;
        const startPos = callExpr.getStart();
        const endPos = callExpr.getEnd();
        const callText = configContents.substring(startPos, endPos);
        // Skip if useLegacyHtmlPlugin is already present
        if (callText.includes('useLegacyHtmlPlugin')) {
            continue;
        }
        // If it's already withReact({ ... }), add useLegacyHtmlPlugin: true to the options
        if (callText.includes('{') && callText.includes('}')) {
            const newCallText = callText.replace(/\{\s*/, '{ useLegacyHtmlPlugin: true,\n      ');
            newContents =
                newContents.substring(0, startPos) +
                    newCallText +
                    newContents.substring(endPos);
        }
        else {
            // If it's just withReact(), replace with withReact({ useLegacyHtmlPlugin: true })
            const newCallText = 'withReact({ useLegacyHtmlPlugin: true })';
            newContents =
                newContents.substring(0, startPos) +
                    newCallText +
                    newContents.substring(endPos);
        }
    }
    if (newContents !== configContents) {
        tree.write(configPath, newContents);
    }
}
function transformComposePlugins(tree, configPath, scope) {
    const configContents = tree.read(configPath, 'utf-8');
    const sourceFile = (0, tsquery_1.ast)(configContents);
    const HAS_COMPOSE_PLUGINS_FROM_NX_WEBPACK = `VariableDeclaration:has(Identifier[name=composePlugins]) > CallExpression:has(Identifier[name=require]) StringLiteral[value=${scope}/webpack]`;
    const nodes = (0, tsquery_1.query)(sourceFile, HAS_COMPOSE_PLUGINS_FROM_NX_WEBPACK);
    if (nodes.length === 0) {
        return;
    }
    const COMPOSE_PLUGINS_IMPORT = 'VariableDeclaration:has(Identifier[name=composePlugins]) Identifier[name=composePlugins]';
    const composePluginsNodes = (0, tsquery_1.query)(sourceFile, COMPOSE_PLUGINS_IMPORT);
    if (nodes.length === 0) {
        return;
    }
    const startIndex = composePluginsNodes[0].getStart();
    let endIndex = composePluginsNodes[0].getEnd();
    if (configContents.charAt(endIndex) === ',') {
        endIndex++;
    }
    const newContents = `const { composePlugins } = require('@nx/rspack');
  ${configContents.slice(0, startIndex)}${configContents.slice(endIndex)}`;
    tree.write(configPath, newContents);
}
function transformWithNx(tree, configPath, scope) {
    const configContents = tree.read(configPath, 'utf-8');
    const sourceFile = (0, tsquery_1.ast)(configContents);
    const HAS_WITH_NX_FROM_NX_WEBPACK = `VariableDeclaration:has(Identifier[name=withNx]) > CallExpression:has(Identifier[name=require]) StringLiteral[value=${scope}/webpack]`;
    const nodes = (0, tsquery_1.query)(sourceFile, HAS_WITH_NX_FROM_NX_WEBPACK);
    if (nodes.length === 0) {
        return;
    }
    const WITH_NX_IMPORT = 'VariableDeclaration:has(Identifier[name=withNx]) Identifier[name=withNx]';
    const withNxNodes = (0, tsquery_1.query)(sourceFile, WITH_NX_IMPORT);
    if (nodes.length === 0) {
        return;
    }
    const startIndex = withNxNodes[0].getStart();
    let endIndex = withNxNodes[0].getEnd();
    if (configContents.charAt(endIndex) === ',') {
        endIndex++;
    }
    const newContents = `const { withNx } = require('@nx/rspack');
  ${configContents.slice(0, startIndex)}${configContents.slice(endIndex)}`;
    tree.write(configPath, newContents);
}
function transformWithWeb(tree, configPath, scope) {
    const configContents = tree.read(configPath, 'utf-8');
    const sourceFile = (0, tsquery_1.ast)(configContents);
    const HAS_WITH_WEB_FROM_NX_WEBPACK = `VariableDeclaration:has(Identifier[name=withWeb]) > CallExpression:has(Identifier[name=require]) StringLiteral[value=${scope}/webpack]`;
    const nodes = (0, tsquery_1.query)(sourceFile, HAS_WITH_WEB_FROM_NX_WEBPACK);
    if (nodes.length === 0) {
        return;
    }
    const WITH_WEB_IMPORT = 'VariableDeclaration:has(Identifier[name=withWeb]) Identifier[name=withWeb]';
    const withWebNodes = (0, tsquery_1.query)(sourceFile, WITH_WEB_IMPORT);
    if (nodes.length === 0) {
        return;
    }
    const startIndex = withWebNodes[0].getStart();
    let endIndex = withWebNodes[0].getEnd();
    if (configContents.charAt(endIndex) === ',') {
        endIndex++;
    }
    const newContents = `const { withWeb } = require('@nx/rspack');
  ${configContents.slice(0, startIndex)}${configContents.slice(endIndex)}`;
    tree.write(configPath, newContents);
}
function transformWithReact(tree, configPath, scope) {
    const configContents = tree.read(configPath, 'utf-8');
    const sourceFile = (0, tsquery_1.ast)(configContents);
    const HAS_WITH_REACT_FROM_NX_REACT = `VariableDeclaration:has(Identifier[name=withReact]) > CallExpression:has(Identifier[name=require]) StringLiteral[value=${scope}/react]`;
    const nodes = (0, tsquery_1.query)(sourceFile, HAS_WITH_REACT_FROM_NX_REACT);
    if (nodes.length === 0) {
        return;
    }
    const WITH_REACT_IMPORT = 'VariableDeclaration:has(Identifier[name=withReact]) Identifier[name=withReact]';
    const withReactNodes = (0, tsquery_1.query)(sourceFile, WITH_REACT_IMPORT);
    if (nodes.length === 0) {
        return;
    }
    const startIndex = withReactNodes[0].getStart();
    let endIndex = withReactNodes[0].getEnd();
    if (configContents.charAt(endIndex) === ',') {
        endIndex++;
    }
    const newContents = `const { withReact } = require('@nx/rspack');
  ${configContents.slice(0, startIndex)}${configContents.slice(endIndex)}`;
    tree.write(configPath, newContents);
}
function transformModuleFederationConfig(tree, configPath, scope) {
    const configContents = tree.read(configPath, 'utf-8');
    const sourceFile = (0, tsquery_1.ast)(configContents);
    const HAS_WITH_MODULE_FEDERATION_FROM_NX_REACT = `VariableDeclaration:has(Identifier[name=ModuleFederationConfig]) > CallExpression:has(Identifier[name=require]) StringLiteral[value=${scope}/webpack]`;
    const nodes = (0, tsquery_1.query)(sourceFile, HAS_WITH_MODULE_FEDERATION_FROM_NX_REACT);
    if (nodes.length === 0) {
        return;
    }
    const WITH_MODULE_FEDERATION_IMPORT = 'VariableDeclaration:has(Identifier[name=ModuleFederationConfig]) Identifier[name=ModuleFederationConfig]';
    const withModuleFederationNodes = (0, tsquery_1.query)(sourceFile, WITH_MODULE_FEDERATION_IMPORT);
    if (nodes.length === 0) {
        return;
    }
    const startIndex = withModuleFederationNodes[0].getStart();
    let endIndex = withModuleFederationNodes[0].getEnd();
    if (configContents.charAt(endIndex) === ',') {
        endIndex++;
    }
    const newContents = `const { ModuleFederationConfig } = require('@nx/module-federation');
  ${configContents.slice(0, startIndex)}${configContents.slice(endIndex)}`;
    tree.write(configPath, newContents);
}
function transformWithModuleFederation(tree, configPath, scope, usesJsExtensions) {
    const configContents = tree.read(configPath, 'utf-8');
    const sourceFile = (0, tsquery_1.ast)(configContents);
    const HAS_WITH_MODULE_FEDERATION_FROM_NX_REACT = `VariableDeclaration:has(Identifier[name=withModuleFederation]) > CallExpression:has(Identifier[name=require]) StringLiteral[value="${scope}/module-federation/webpack${usesJsExtensions ? '.js' : ''}"]`;
    const nodes = (0, tsquery_1.query)(sourceFile, HAS_WITH_MODULE_FEDERATION_FROM_NX_REACT);
    if (nodes.length === 0) {
        return;
    }
    const WITH_MODULE_FEDERATION_IMPORT = 'VariableDeclaration:has(Identifier[name=withModuleFederation]) Identifier[name=withModuleFederation]';
    const withModuleFederationNodes = (0, tsquery_1.query)(sourceFile, WITH_MODULE_FEDERATION_IMPORT);
    if (nodes.length === 0) {
        return;
    }
    const startIndex = withModuleFederationNodes[0].getStart();
    let endIndex = withModuleFederationNodes[0].getEnd();
    if (configContents.charAt(endIndex) === ',') {
        endIndex++;
    }
    const rspackImport = usesJsExtensions
        ? '@nx/module-federation/rspack.js'
        : '@nx/module-federation/rspack';
    const newContents = `const { withModuleFederation } = require('${rspackImport}');
  ${configContents.slice(0, startIndex)}${configContents.slice(endIndex)}`;
    tree.write(configPath, newContents);
}
function transformWithModuleFederationSSR(tree, configPath, scope, usesJsExtensions) {
    const configContents = tree.read(configPath, 'utf-8');
    const sourceFile = (0, tsquery_1.ast)(configContents);
    const HAS_WITH_MODULE_FEDERATION_FROM_NX_REACT = `VariableDeclaration:has(Identifier[name=withModuleFederationForSSR]) > CallExpression:has(Identifier[name=require]) StringLiteral[value="${scope}/module-federation/webpack${usesJsExtensions ? '.js' : ''}"]`;
    const nodes = (0, tsquery_1.query)(sourceFile, HAS_WITH_MODULE_FEDERATION_FROM_NX_REACT);
    if (nodes.length === 0) {
        return;
    }
    const WITH_MODULE_FEDERATION_IMPORT = 'VariableDeclaration:has(Identifier[name=withModuleFederationForSSR]) Identifier[name=withModuleFederationForSSR]';
    const withModuleFederationNodes = (0, tsquery_1.query)(sourceFile, WITH_MODULE_FEDERATION_IMPORT);
    if (nodes.length === 0) {
        return;
    }
    const startIndex = withModuleFederationNodes[0].getStart();
    let endIndex = withModuleFederationNodes[0].getEnd();
    if (configContents.charAt(endIndex) === ',') {
        endIndex++;
    }
    const rspackImport = usesJsExtensions
        ? '@nx/module-federation/rspack.js'
        : '@nx/module-federation/rspack';
    const newContents = `const { withModuleFederationForSSR } = require('${rspackImport}');
  ${configContents.slice(0, startIndex)}${configContents.slice(endIndex)}`;
    tree.write(configPath, newContents);
}
