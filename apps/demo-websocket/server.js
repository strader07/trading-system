const express = require('express');
const path = require('path');
const port = process.env.PORT || 8080;

const app = express();

// Serve the static files from the React app
app.use(express.static(path.join(__dirname)));

// Handles any requests that don't match the ones above
app.get('*', (req,res) =>{
    res.sendFile(path.join(__dirname + '/index.html'));
});

app.listen(port);

console.log('App is listening on port ' + port);
