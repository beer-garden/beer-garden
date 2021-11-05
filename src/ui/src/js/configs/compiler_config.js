compilerConfig.$inject = ['$compileProvider']
/**
 * compilerConfig - Angular configuration object for the Angular compiler.
 * @param {$compileProvider} $compileProvider Angular's $compileProvider object.
 */
export function compilerConfig($compileProvider) {
    $compileProvider.aHrefSanitizationTrustedUrlList(/^\s*(https?|ftp|mailto|tel|file|blob):/);
};
