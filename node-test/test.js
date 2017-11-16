const io = require('socket.io-client');
const readline = require('readline');

var rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});



// const token = {
//   addr: '0x8f3470a7388c05ee4e7af3d01d8c722b0ff52374',
//   decimals: 18,
// };
//
// const user = {
//   addr: '0x00B7C0908514A44898E6a01C85bB6e8C82873f58',
//   pk: '',
// };
//
// order = {'contractAddr': '0x8d12a197cb00d4747a1fe03395095ce2a5cc6819', 'tokenGet': '0x59adcf176ed2f6788a41b8ea4c4904518e62b6a4', 'amountGet': 100000000000000000000, 'tokenGive': '0x0000000000000000000000000000000000000000', 'amountGive': 100000000000000000, 'expires': 4559402, 'nonce': 427189507, 'v': 28, 'r': '0x7ba721a486d105aad5b9b60c28df0599d2c2bcfa8e18b73bc612b45e56f2946b', 's': '0x42c325cdd6d5383653f48c16af129e47d7ea1bfe14c73c3934c861c68fde179a', 'user': '0x00b7c0908514a44898e6a01c85bb6e8c82873f58'};

socket = io.connect('https://socket.etherdelta.com', { transports: ['websocket'] });
socket.on('connect', () => {
  console.log('socket connected');
});

socket.on('disconnect', () => {
  console.log('socket disconnected');
});

socket.on('reconnect', () => {
  console.log('socket disconnected');
});

rl.on('line', function (line) {
  // console.log(line);
  const order = JSON.parse(line);
  socket.emit('message', order);
  socket.once('messageResult', (messageResult) => {
    console.log(messageResult);
  });
});
