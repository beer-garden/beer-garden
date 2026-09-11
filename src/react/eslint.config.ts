// @ts-check
import simpleImportSort from 'eslint-plugin-simple-import-sort';
import tseslint from 'typescript-eslint';
import eslint from '@eslint/js';
import { defineConfig } from 'eslint/config';
import jsxA11y from 'eslint-plugin-jsx-a11y';

export default defineConfig(
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

      // Disabled rules that check for any usage
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-unsafe-argument': 'off',
      '@typescript-eslint/no-unsafe-member-access': 'off',
      '@typescript-eslint/no-unsafe-call': 'off',
      '@typescript-eslint/no-unsafe-assignment': 'off',
      '@typescript-eslint/no-unsafe-return': 'off',
      '@typescript-eslint/no-redundant-type-constituents': 'off',
      "@typescript-eslint/no-misused-promises": [
      "error",
      {
        "checksVoidReturn": false
      }
    ],

      '@typescript-eslint/no-unused-vars': [
        "warn",
        { 
          "argsIgnorePattern": "^_",
          "varsIgnorePattern": "^_",
          "caughtErrorsIgnorePattern": "^_"
        }
      ],
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
  {
    files: ['**/*.{js,mjs,cjs,jsx,mjsx,ts,tsx,mtsx}'],
    ...jsxA11y.flatConfigs.recommended,
  },
);

