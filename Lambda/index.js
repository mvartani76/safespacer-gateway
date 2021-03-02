const https = require('https');

const postURL = process.env.postURL
const postPath = process.env.postPath

exports.handler = async (event, context, callback) => {
    // TODO implement
    const response = {
        statusCode: 200,
        body: JSON.stringify('Hello from Lambda!'),
    };
    
    console.log('event: ', JSON.stringify(event));
    
    // Send Post request
    const post_data = JSON.stringify(event);
    const post_options = {
        hostname: postURL ,
        port: 443,
        path: postPath,
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Content-Length': post_data.length
        }
    };

    const req = https.request(post_options, res => {
        console.log(`statusCode: ${res.statusCode}`);

        res.on('data', d => {
            process.stdout.write(d);
        });
        console.log("got in here...");
    });
    
    req.on('error', error => {
            console.error(error);
    });

    console.log('postURL: ', postURL);
    console.log('postPath: ', postPath);

    req.write(post_data);
    req.end();
    
    return response;
};
