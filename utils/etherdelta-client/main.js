/*!
 * This file is part of Maker Keeper Framework.
 *
 * Copyright (C) 2017-2018 reverendus
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

var args = require('minimist')(process.argv.slice(2));
const order = args['_'].join(" ");
const url = args['url'];
const retryInterval = args['retry-interval'];
const timeout = args['timeout'];

function publishOrder() {
  socket.emit('message', JSON.parse(order));
  console.log('Order sent');
}

console.log("Sending order '" + order + "' to " + url);

const io = require('socket.io-client');
const socket = io.connect(url, { transports: ['websocket'] });

socket.on('connect', () => {
  console.log("Connected to socket");
  publishOrder();
});

socket.on('messageResult', (messageResult) => {
  console.log("Response received: ", messageResult);

if (messageResult[0] === 'Added/updated order.') {
    console.log("Order placed successfully");
    socket.disconnect();
    setTimeout(() => process.exit(0), 2500);
  }
  else {
    console.log("Order placement failed");
    setTimeout(publishOrder, retryInterval*1000);
  }
});


socket.on('disconnect', () => {
  console.log('Disconnected from socket');
});

socket.on('reconnect', () => {
  console.log('Reconnected to socket');
});

setTimeout(() => {
  console.log('Timed out');
  process.exit(-1);
}, timeout*1000);
