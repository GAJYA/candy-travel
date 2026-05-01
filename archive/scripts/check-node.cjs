const [major] = process.versions.node.split('.').map(Number);

if (major >= 18) {
  process.exit(0);
}

console.error(
  [
    '',
    `Unsupported Node.js version: ${process.version}`,
    'This project uses Vue 3 and Vite 5, which require Node.js 18 or newer.',
    'Please upgrade Node.js, then reinstall dependencies and start the dev server again.',
    'Suggested steps:',
    '  1. Install Node.js 18+',
    '  2. Remove node_modules if it was installed with an older Node version',
    '  3. Run npm install',
    '  4. Run npm run dev',
    '',
  ].join('\n'),
);

process.exit(1);
