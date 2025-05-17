const express = require('express');
const config = require('../config/default.json');
const app = express();
const port = process.env.PORT || config.serverPort || 3000;

app.get('/', (req, res) => {
	res.send('Cloud Optimizer Platform is running.');
});

app.listen(port, () => {
	console.log(`Server listening on port ${port}`);
});
