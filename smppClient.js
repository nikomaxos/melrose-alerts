const smpp = require('smpp');

class SmppClient {
  constructor(config) {
    this.config = config;
    this.session = null;
    this.connected = false;
    this.lastError = null;
  }

  connect() {
    return new Promise((resolve, reject) => {
      this.disconnect(); // Ensure any existing session is closed

      console.log(`Connecting to SMPP server at ${this.config.host}:${this.config.port}...`);
      this.session = smpp.connect({
        url: `smpp://${this.config.host}:${this.config.port}`,
        auto_enquire_link_period: 10000,
        debug: true
      }, () => {
        console.log('Connected to SMPP server socket. Binding...');
        this.session.bind_transceiver({
          system_id: this.config.username,
          password: this.config.password,
        }, (pdu) => {
          if (pdu.command_status === 0) {
            console.log('Successfully bound to SMPP server');
            this.connected = true;
            this.lastError = null;
            resolve();
          } else {
            const err = new Error(`Failed to bind. Status: ${pdu.command_status}`);
            this.lastError = err.message;
            console.error(err.message);
            reject(err);
          }
        });
      });

      this.session.on('error', (error) => {
        console.error('SMPP Session error:', error.message);
        this.lastError = error.message;
        this.connected = false;
    this.lastError = null;
      });

      this.session.on('close', () => {
        console.log('SMPP Session closed');
        this.connected = false;
    this.lastError = null;
      });
    });
  }

  disconnect() {
    if (this.session) {
      console.log('Closing existing SMPP session...');
      try {
        if (this.connected) {
          this.session.unbind();
        }
        this.session.close();
      } catch (err) {
        console.error('Error during disconnect:', err.message);
      }
      this.session = null;
      this.connected = false;
    this.lastError = null;
    }
  }

  sendSMS(destination, message) {
    return new Promise((resolve, reject) => {
      if (!this.connected || !this.session) {
        return reject(new Error('SMPP Client not connected'));
      }

      this.session.submit_sm({
        source_addr: this.config.source_address,
        destination_addr: destination,
        short_message: message,
      }, (pdu) => {
        if (pdu.command_status === 0) {
          console.log(`Message sent successfully to ${destination}. Message ID:`, pdu.message_id);
          resolve(pdu.message_id);
        } else {
          reject(new Error(`Failed to send message to ${destination}. Status: ${pdu.command_status}`));
        }
      });
    });
  }
}

module.exports = SmppClient;
