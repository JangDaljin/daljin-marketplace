import js from "@eslint/js";
import stylistic from "@stylistic/eslint-plugin";
import { defineConfig } from "eslint/config";
import importX from "eslint-plugin-import-x";
import n from "eslint-plugin-n";
import simpleImportSort from "eslint-plugin-simple-import-sort";
import tseslint from "typescript-eslint";

const config = defineConfig(
    {
        ignores: ["dist/**", "coverage/**", "src/generated/**"],
    },
    js.configs.recommended,
    tseslint.configs.recommendedTypeChecked,
    {
        languageOptions: {
            parserOptions: {
                projectService: true,
                tsconfigRootDir: import.meta.dirname,
            },
        },
        plugins: {
            "@stylistic": stylistic,
            "import-x": importX,
            n,
            "simple-import-sort": simpleImportSort,
        },
        rules: {
            // 포맷
            "@stylistic/indent": ["error", 4],
            "@stylistic/quotes": ["error", "double", { avoidEscape: true }],
            "@stylistic/comma-dangle": ["error", "always-multiline"],
            "@stylistic/max-len": ["error", { code: 180, ignoreUrls: true, ignoreStrings: true, ignoreTemplateLiterals: true }],
            "@stylistic/semi": ["error", "always"],
            "@stylistic/arrow-parens": ["error", "always"],
            "@stylistic/object-curly-spacing": ["error", "always"],
            "@stylistic/eol-last": ["error", "always"],
            "@stylistic/no-trailing-spaces": "error",
            "@stylistic/linebreak-style": ["error", "unix"],

            // 언어
            "no-var": "error",
            "prefer-const": "error",
            "eqeqeq": ["error", "always"],
            "curly": ["error", "all"],
            "no-nested-ternary": "error",
            "prefer-template": "error",
            "no-console": "error",

            // TypeScript
            "@typescript-eslint/consistent-type-definitions": ["error", "type"],
            "@typescript-eslint/no-explicit-any": "error",
            "@typescript-eslint/no-floating-promises": "error",
            "@typescript-eslint/no-misused-promises": "error",
            "@typescript-eslint/explicit-member-accessibility": ["error", { accessibility: "explicit", overrides: { constructors: "no-public" } }],
            "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_", varsIgnorePattern: "^_" }],

            // import, export
            "import-x/first": "error",
            "import-x/exports-last": "error",
            "import-x/group-exports": "error",
            "import-x/no-namespace": "error",
            "import-x/no-default-export": "error",
            "import-x/no-cycle": "error",
            "n/prefer-node-protocol": "error",
            "simple-import-sort/imports": "error",
            "simple-import-sort/exports": "error",

            // 기본 규칙으로 표현할 수 없는 개인 규약
            "no-restricted-syntax": [
                "error",
                {
                    selector: "ExportNamedDeclaration[declaration!=null]",
                    message: "선언과 export 를 분리하고 파일 끝에서 export { ... } 로 내보낸다.",
                },
                {
                    selector: "CallExpression > ArrowFunctionExpression.callee, CallExpression > FunctionExpression.callee",
                    message: "IIFE 대신 이름 있는 메서드로 뺀다.",
                },
                {
                    selector: "CallExpression[callee.property.name='then']",
                    message: ".then() 대신 async/await 를 쓴다.",
                },
            ],
        },
    },
    {
        files: ["**/*.js", "**/*.mjs"],
        extends: [tseslint.configs.disableTypeChecked],
    },
    {
        files: ["eslint.config.js", "**/*.config.{js,mjs,ts}"],
        rules: {
            "import-x/no-default-export": "off",
        },
    },
);

export default config;
