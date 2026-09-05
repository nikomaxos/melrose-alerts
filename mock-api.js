const http = require('http');

let deliveryRate = 95.0; // Starts healthy

const requestListener = function (req, res) {
  if (req.url === '/v1/stats') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ delivery_rate: deliveryRate }));
    
    // Drop the rate after first successful healthy response for testing
    if (deliveryRate > 80.0) {
      setTimeout(() => {
        deliveryRate = 75.0;
        console.log('[Mock API] Delivery rate dropped to 75.0% to simulate outage.');
      }, 7000);
    }
  } else {
    res.writeHead(404);
    res.end();
  }
};

const server = http.createServer(requestListener);
server.listen(8080, () => {
  console.log('[Mock API] Server is running on http://localhost:8080');
});
