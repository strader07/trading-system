const express = require('express');
const path = require('path');
const port = process.env.PORT || 8081;

const app = express();

// Path to the production files
const SPA_PATH = path.join(__dirname, 'build');

// Serve the static files from the React app
app.use(express.static(SPA_PATH));

// Handles any requests that don't match the ones above
app.get('*', (_, res) => res.sendFile(path.join(SPA_PATH, 'index.html')));

app.listen(port);

console.log('App is listening on port ' + port);
