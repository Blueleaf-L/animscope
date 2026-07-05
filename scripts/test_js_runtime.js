/**
 * Simulate browser JS loading order to find runtime errors.
 * Run: node scripts/test_js_runtime.js
 */

// Minimal browser API mocks
global.window = global;
global.document = {
    documentElement: {
        getAttribute: () => "light",
        setAttribute: () => {},
    },
    getElementById: () => null,
    addEventListener: () => {},
    querySelectorAll: () => ({ forEach: () => {} }),
    createElement: () => ({ textContent: "" }),
};
global.localStorage = { getItem: () => null, setItem: () => {} };
global.fetch = () => Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
global.setTimeout = (fn) => fn();
global.clearTimeout = () => {};
global.getComputedStyle = () => ({
    getPropertyValue: () => "#000000",
});
global.window.matchMedia = () => ({ matches: false });

const fs = require("fs");
const path = require("path");

const jsDir = path.join(__dirname, "..", "frontend", "js");
const files = [
    "config.js",
    "api.js",
    "analytics.js",
    "charts.js",
    "views.js",
    "router.js",
    "pages/overview.js",
    "pages/companies.js",
    "pages/company-detail.js",
    "pages/rankings.js",
    "pages/trends.js",
    "pages/compare.js",
    "pages/search.js",
    "pages/report.js",
    "app.js",
];

let passed = 0;
let failed = 0;

for (const file of files) {
    const filePath = path.join(jsDir, file);
    try {
        const code = fs.readFileSync(filePath, "utf-8");
        // Wrap in Function to catch runtime errors during load
        new Function(code)();
        console.log(`  [OK] ${file}`);
        passed++;
    } catch (err) {
        console.log(`  [FAIL] ${file}: ${err.message}`);
        failed++;
    }
}

console.log(`\nResult: ${passed} passed, ${failed} failed`);
