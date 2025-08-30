#!/usr/bin/env node

var torrentStream = require('torrent-stream');
var express = require('express');
var app = express();
var server = require('http').Server(app);
var io = require('socket.io')(server);
var del = require('del');
var mime = require('mime');
const path = require('path');
const fs = require('fs'); // Include the Node.js file system module
const cors = require('cors')


var client, corrent_torrent, corrent_movie;




app.use(cors());

var DIR ='D:\movies';
var PORT = parseArg('--port') || parseArg('-p') || process.env.PORT || 5020;

server.listen(PORT);
app.use(express.static(__dirname + '/public'));
console.log('Torrent Web started on port '+PORT+' ...');

//===============================
// API
//===============================



app.get('/torrent', function(req, res) {
    var file = corrent_movie

    if (file) {
        var range = req.headers.range;
        if (!range) {
            range = 'bytes=0-';
        }

        var positions = range.replace(/bytes=/, "").split("-");
        var start = parseInt(positions[0], 10);
        var total = file.length;
        var end = positions[1] ? parseInt(positions[1], 10) : total - 1;

        if (start >= total || end >= total) {
            // 416 Wrong range
            res.status(416).send('Range Not Satisfiable');
            return;
        }

        var chunksize = (end - start) + 1;
        var stream = file.createReadStream({ start, end });

        res.writeHead(206, {
            'Content-Range': `bytes ${start}-${end}/${total}`,
            'Accept-Ranges': 'bytes',
            'Content-Length': chunksize,
            'Content-Type': mime.lookup(file.name)
        });

        stream.pipe(res);
    } else {
        res.status(404).end();
    }
});




app.get('/watch/:torrent', function(req, res) {
    const torrent ="magnet:?" +  req.params.torrent;



    if (corrent_torrent != torrent){
    	corrent_torrent = torrent;
        addTorrent(torrent);
        console.log(`Torrent added`);

   } else {
      console.log(`Torrent exist`);
      res.status(200).send(Buffer.from(corrent_movie.name).toString('base64'));

}



client.on('ready', function() {
      corrent_movie= findFile();
      res.status(200).send(Buffer.from(corrent_movie.name).toString('base64'));
});



});

app.get('/exit', function(req, res) {

	removeTorrent();
	console.log("user left");
	corrent_torrent = "none"
	res.status(200).send(`Torrent removed`);


});
//===============================
// Main functions
//===============================

function findFile() {
	var f = null;
	client.files.forEach(function(file) {
		if (file.name.endsWith('.mp4') || file.name.endsWith('.mkv')) {
			f = file;
		}

	});

	return f;
}


function addTorrent(incoming) {
	removeTorrent();

	client = torrentStream(incoming, {
		uploads: 3,
		connections: 300,
		path: DIR
	});
}

function removeTorrent() {
	if (client) {
		console.log('Destroying client.');
		client.destroy();
		client = null;
	}
	deleteFiles();
}

//===============================
// Helper functions
//===============================

/**
 * Checks process.argv for one beginning with arg+'='
 * @param {string} arg
 */
function parseArg(arg) {
	for (var i = 0; i < process.argv.length; i++) {
		var val = process.argv[i];
		if (startsWith(val, arg+'=')) return val.substring(arg.length+1);
	}
	function startsWith(string, beginsWith) {
		return string.indexOf(beginsWith) === 0;
	}
}

function deleteFiles() {
setTimeout(function() {
    del.sync([DIR + '/**', '!' + DIR], {force: true});
}, 1000);

}





