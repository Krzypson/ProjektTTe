const gameUsername = window.gameUsername;
const gameRoomId = window.gameRoomId;
let isReady = false;

const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const host = window.location.host;
window.gameWebSocket = new WebSocket(`${protocol}//${host}/ws/${gameRoomId}/${gameUsername}`);

window.gameWebSocket.onmessage = function(event) {
    const messageText = event.data;

    if (messageText.startsWith('PLAYERLIST:')) {
        const players = messageText.replace('PLAYERLIST:', '').split(',');
        updatePlayerList(players);
    } else if (messageText.startsWith('READY_STATUS:')) {
        const statusData = messageText.replace('READY_STATUS:', '');
        updateReadyStatus(statusData);
    } else if (messageText.startsWith('PLAYER_POSITIONS:')) {
        const positionData = messageText.replace('PLAYER_POSITIONS:', '');
        updatePlayerPositions(positionData);
    } else if (messageText.startsWith('GAME_START:')) {
        const firstPlayer = messageText.replace('GAME_START:', '');
        handleGameStart(firstPlayer);
    } else if (messageText.startsWith('DICE_ROLL:')) {
        const diceData = messageText.replace('DICE_ROLL:', '');
        handleDiceRoll(diceData);
    } else if (messageText.startsWith('TURN_CHANGE:')) {
        const nextPlayer = messageText.replace('TURN_CHANGE:', '');
        handleTurnChange(nextPlayer);
    }else if (messageText.startsWith('WIN:')) {
        const winner = messageText.replace('WIN:', '');
        handleWin(winner);
    } else {
        displayChatMessage(messageText);
    }
};

function sendMessage(event) {
    event.preventDefault();
    const messageText = document.getElementById("messageText");
    const messageValue = messageText.value.trim();

    if (messageValue && window.gameWebSocket && window.gameWebSocket.readyState === WebSocket.OPEN) {
        window.gameWebSocket.send(messageValue);
        messageText.value = '';
    } else if (!messageValue) {
        console.warn("Empty message not sent");
    } else {
        console.error("WebSocket is not connected");
    }
}

function updatePlayerList(players) {
    const playersList = document.getElementById('playersList');
    playersList.innerHTML = '';

    players.forEach(player => {
        if (player.trim()) {
            const tr = document.createElement('tr');
            const td = document.createElement('td');
            td.textContent = player.trim();
            td.dataset.username = player.trim();
            tr.appendChild(td);
            playersList.appendChild(tr);
        }
    });
}

function toggleReady() {
    if (window.gameWebSocket && window.gameWebSocket.readyState === WebSocket.OPEN) {
        window.gameWebSocket.send("READY_TOGGLE");
        isReady = !isReady;
        document.getElementById('readyButton').textContent = isReady ? "Not Ready" : "Ready";
        document.getElementById('readyButton').style.backgroundColor = isReady ? "green" : "";
    }
}

function updateReadyStatus(statusData) {
    if (!statusData) return;

    const statuses = statusData.split(',');
    const playersList = document.getElementById('playersList');

    statuses.forEach(statusPair => {
        const [username, status] = statusPair.split(':');
        const rows = playersList.getElementsByTagName('tr');

        for (let row of rows) {
            const td = row.getElementsByTagName('td')[0];
            if (td) {
                if (!td.dataset.username) {
                    td.dataset.username = td.textContent.replace('(ready)', '').trim();
                }

                if (td.dataset.username === username) {
                    const readyIndicator = status === 'ready' ? '(ready)' : '';
                    td.textContent = username + readyIndicator;
                    td.style.color = status === 'ready' ? 'green' : 'black';
                    td.style.fontWeight = status === 'ready' ? 'bold' : 'normal';
                }
            }
        }
    });
}

function updatePlayerPositions(positionData) {
    if (!positionData) return;

    document.querySelectorAll('.field-players').forEach(el => el.remove());

    const positions = positionData.split(',');

    positions.forEach(positionPair => {
        const [username, position] = positionPair.split(':');
        const fieldIndex = parseInt(position);

        const field = document.getElementById(fieldIndex.toString());

        if (field) {
            let playerLabel = field.querySelector('.field-players');
            if (!playerLabel) {
                playerLabel = document.createElement('div');
                playerLabel.className = 'field-players';
                field.appendChild(playerLabel);
            }

            const playerSpan = document.createElement('span');
            playerSpan.className = 'player-name';
            playerSpan.textContent = username;
            playerSpan.style.display = 'block';
            playerSpan.style.fontSize = '10px';
            playerSpan.style.color = username === gameUsername ? 'blue' : 'red';
            playerSpan.style.fontWeight = 'bold';
            playerLabel.appendChild(playerSpan);
        }
    });
}

function handleGameStart(firstPlayer) {
    const statusDiv = document.getElementById('game-status');

    if (firstPlayer === gameUsername) {
        statusDiv.textContent = "YOUR TURN!";
        statusDiv.style.color = "green";
        document.getElementById('rollButton').disabled = false;
    } else {
        statusDiv.textContent = `${firstPlayer}'s turn`;
        statusDiv.style.color = "orange";
        document.getElementById('rollButton').disabled = true;
    }

    document.getElementById('readyButton').disabled = true;
}

function rollDice() {
    if (window.gameWebSocket && window.gameWebSocket.readyState === WebSocket.OPEN) {
        window.gameWebSocket.send("ROLL_DICE");
    }
}

function handleDiceRoll(diceData) {
    const [username, diceResult] = diceData.split(':');
    const message = `${username} rolled a ${diceResult}!`;
    displayChatMessage(message);
}

function handleTurnChange(nextPlayer) {
    const statusDiv = document.getElementById('game-status');

    if (nextPlayer === gameUsername) {
        statusDiv.textContent = "YOUR TURN!";
        statusDiv.style.color = "green";
        document.getElementById('rollButton').disabled = false;
    } else {
        statusDiv.textContent = `${nextPlayer}'s turn`;
        statusDiv.style.color = "orange";
        document.getElementById('rollButton').disabled = true;
    }
}

function handleWin(winner){
    document.getElementById('readyButton').disabled = false;
    toggleReady();
    document.getElementById('rollButton').disabled = true;
    document.getElementById('game-status').textContent = `winner: ${winner}`;
}

function displayChatMessage(message) {
    let messages = document.getElementById('messages');
    let li = document.createElement('li');
    let timestamp = new Date().toLocaleTimeString("pl-PL");
    li.textContent = `[${timestamp}] ${message}`;
    messages.insertBefore(li, messages.firstChild);
}