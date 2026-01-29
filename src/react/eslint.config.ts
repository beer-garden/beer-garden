// @ts-check
import simpleImportSort from 'eslint-plugin-simple-import-sort';
import tseslint from 'typescript-eslint';
import eslint from '@eslint/js';

export default tseslint.config(
  {
    // Ignores are applied to the entire configuration cascade
    ignores: ['dist/', '**/*.js'], // Exclude build artifacts and all .js files from linting
  },
  {
    files: ['**/*.ts', '**/*.tsx'], // Target TypeScript files
    extends: [
      eslint.configs.recommended,
      ...tseslint.configs.recommendedTypeChecked, // Includes type-aware rules
      // For stricter rules, use tseslint.configs.strictTypeChecked
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.json'], // Required for type-aware linting
        ecmaFeatures: { modules: true },
        ecmaVersion: 'latest',
      },
    },
    rules: {
      // Add or override specific rules here
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-unused-vars': 'warn',
    },
  },
  {
    plugins: {
      'simple-import-sort': simpleImportSort,
    },
    rules: {
      'simple-import-sort/imports': 'error',
      'simple-import-sort/exports': 'error',
      
      // It is highly recommended to disable other sorting rules to avoid conflicts.
      // If you are using @typescript-eslint/eslint-plugin, you might have sort-imports enabled.
      // Make sure it is disabled or not included if it conflicts with simple-import-sort.
      // e.g., '@typescript-eslint/sort-imports': 'off', 
    },
  },
);

