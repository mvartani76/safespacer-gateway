const https = require('https');

const postURL = process.env.postURL
const postPath = process.env.postPath

exports.handler = async (event) => {

    console.log('event: ', JSON.stringify(event));
    
    // Send Post request
    const post_data = JSON.stringify(event);
    const post_options = {
        hostname: postURL ,
        port: 443,
        path: postPath,
        method: 'POST',
        headers: {
            'Content-Type': 'application/json; charset=utf-8'
        }
    };

    const response = await new Promise(function(resolve, reject) {

      var req = https.request(post_options, function(res) {  
        res.on('data', function(event) {
          console.log(post_data);
        });
        res.on('end', resolve);
      });
