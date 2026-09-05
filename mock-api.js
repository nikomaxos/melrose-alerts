const http = require('http');

let deliveryRate = 95.0; // Starts healthy
let pendingMessages = 10; // Starts healthy

const requestListener = function (req, res) {
  if (req.url === '/v1/stats') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ 
      delivery_rate: deliveryRate,
      pending_messages: pendingMessages 
    }));
    
    // Drop the rate and spike messages after first successful healthy response for testing
    if (deliveryRate > 80.0) {
      setTimeout(() => {
        deliveryRate = 75.0;
        pendingMessages = 1500;
        console.log('[Mock API] Delivery rate dropped to 75.0% and pending spiked to 1500 to simulate outage.');
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
