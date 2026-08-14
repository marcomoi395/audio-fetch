import { defineConfig } from 'eslint/config'
import tseslint from '@electron-toolkit/eslint-config-ts'
import eslintConfigPrettier from '@electron-toolkit/eslint-config-prettier'

export default defineConfig(
  // Ignore build outputs
  { ignores: ['**/node_modules', '**/dist', '**/out', '**/legacy'] },

  // Base TypeScript recommended rules
  ...tseslint.configs.recommended,

  // Main rules - balanced approach
  {
    rules: {
      // === Security & Best Practices ===
      'guard-for-in': 'error', // Prevent prototype pollution
      'no-var': 'error', // Enforce const/let
      'no-eval': 'error', // Security: no eval()
      'no-implied-eval': 'error', // Security: no setTimeout(string)

      // === Code Quality ===
      'prefer-const': ['error', { destructuring: 'all' }],
      'no-console': ['warn', { allow: ['warn', 'error'] }], // Allow warn/error only
      complexity: ['warn', 15], // Keep functions simple

      // === TypeScript Strict ===
      '@typescript-eslint/explicit-function-return-type': 'off', // Let TypeScript infer
      '@typescript-eslint/no-unused-vars': [
        'error',
        {
          vars: 'all',
          args: 'after-used',
          ignoreRestSiblings: true,
          argsIgnorePattern: '^_', // Allow _param for unused
          varsIgnorePattern: '^_' // Allow _var for unused
        }
      ],
      '@typescript-eslint/no-redeclare': 'error',
      '@typescript-eslint/no-explicit-any': 'warn', // Warn but not error
      '@typescript-eslint/consistent-type-imports': 'warn' // Better import style
    }
  },

  // TypeScript files - disable JS-only checks
  {
    files: ['**/*.ts'],
    rules: {
      'no-undef': 'off' // TypeScript already checks this
    }
  },

  // Type declaration files - allow unused vars
  {
    files: ['**/*.d.ts'],
    rules: {
      '@typescript-eslint/no-unused-vars': 'off'
    }
  },

  // MUST BE LAST - Prettier disables conflicting format rules
  eslintConfigPrettier
)
