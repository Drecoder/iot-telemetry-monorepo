import { FlatCompat } from "@eslint/eslintrc";
import js from "@eslint/js";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const compat = new FlatCompat({
    baseDirectory: __dirname,
    recommendedConfig: js.configs.recommended
});

export default [
    // Automatically pulls down baseline recommended JavaScript rules natively
    js.configs.recommended,
    
    // Ignores build artifacts and third-party modules globally
    {
        ignores: ["**/dist/**", "**/node_modules/**", "scan-results/**"]
    },

    // Allows your current monorepo structure to pass lint checks smoothly
    ...compat.config({
        env: {
            node: true,
            es2024: true,
            jest: true
        },
        parserOptions: {
            ecmaVersion: "latest",
            sourceType: "module"
        }
    })
];