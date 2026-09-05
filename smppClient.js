const smpp = require('smpp');

class SmppClient {
  constructor(config) {
    this.config = config;
    this.session = null;
    this.connected = false;
  }

  connect() {
    return new Promise((resolve, reject) => {
      this.session = smpp.connect({
        url: `smpp://${this.config.host}:${this.config.port}`,
        auto_enquire_link_period: 10000,
        debug: true
      }, () => {
        console.log('Connected to SMPP server');
        this.session.bind_transceiver({
          system_id: this.config.username,
          password: this.config.password,
        }, (pdu) => {
          if (pdu.command_status === 0) {
            console.log('Successfully bound to SMPP server');
            this.connected = true;
            resolve();
          } else {
            reject(new Error(`Failed to bind. Status: ${pdu.command_status}`));
          }
        });
      });

      this.session.on('error', (error) => {
        console.error('SMPP Session error:', error);
        this.connected = false;
      });

      this.session.on('close', () => {
        console.log('SMPP Session closed');
        this.connected = false;
        // Optionally implement auto-reconnect here
      });
    });
  }

  sendSMS(message) {
    return new Promise((resolve, reject) => {
      if (!this.connected || !this.session) {
        return reject(new Error('SMPP Client not connected'));
      }

      this.session.submit_sm({
        source_addr: this.config.source_address,
        destination_addr: this.config.destination_number,
        short_message: message,
      }, (pdu) => {
        if (pdu.command_status === 0) {
          console.log('Message sent successfully. Message ID:', pdu.message_id);
          resolve(pdu.message_id);
        } else {
          reject(new Error(`Failed to send message. Status: ${pdu.command_status}`));
        }
      });
    });
  }
}

module.exports = SmppClient;
