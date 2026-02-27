import { Configuration } from '@rspack/core';
import { ExtraEntryPointClass } from './model';
import { NxRspackExecutionContext } from './config';
export interface WithWebOptions {
    baseHref?: string;
    deployUrl?: string;
    extractCss?: boolean;
    generateIndexHtml?: boolean;
    index?: string;
    postcssConfig?: string;
    scripts?: Array<ExtraEntryPointClass | string>;
    styles?: Array<ExtraEntryPointClass | string>;
    stylePreprocessorOptions?: {
        includePaths?: string[];
        sassOptions?: Record<string, any>;
        lessOptions?: Record<string, any>;
    };
    cssModules?: boolean;
    ssr?: boolean;
    /**
     * Use the legacy WriteIndexHtmlPlugin instead of the built-in HtmlRspackPlugin.
     */
    useLegacyHtmlPlugin?: boolean;
    /**
     * Requires useLegacyHtmlPlugin to be false.
     * Allows to overwrite the parameters used in the template. When using a function, pass in the original template parameters and use the returned object as the final template parameters.
     */
    templateParameters?: Record<string, string> | boolean | ((params: Record<string, any>) => Record<string, any> | Promise<Record<string, any>>);
}
export declare function withWeb(pluginOptions?: WithWebOptions): (config: Configuration, { options, context }: NxRspackExecutionContext) => Configuration;
//# sourceMappingURL=with-web.d.ts.map