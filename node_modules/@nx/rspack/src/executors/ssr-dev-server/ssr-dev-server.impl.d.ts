import { ExecutorContext } from '@nx/devkit';
import { RspackSsrDevServerOptions, TargetOptions } from './schema';
export declare function ssrDevServerExecutor(options: RspackSsrDevServerOptions, context: ExecutorContext): AsyncGenerator<{
    baseUrl: string;
    success: boolean;
    options: TargetOptions;
}, void, unknown>;
export default ssrDevServerExecutor;
//# sourceMappingURL=ssr-dev-server.impl.d.ts.map