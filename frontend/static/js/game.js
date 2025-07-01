// Mafia Game Frontend JavaScript
class MafiaGameInterface {
  constructor() {
    this.socket = io();
    this.voteChart = null;
    this.currentFilter = "all";
    this.gameState = null;
    this.messageCount = 0;
    this.previousVotes = new Set(); // Track previous votes for highlighting

    this.initializeEventListeners();
    this.initializeSocketEvents();
    this.initializeChart();
  }

  initializeEventListeners() {
    // Game controls
    document.getElementById("start-game").addEventListener("click", () => {
      this.startGame();
    });

    document.getElementById("stop-game").addEventListener("click", () => {
      this.stopGame();
    });

    // Chat filters
    document.querySelectorAll(".filter-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        this.setFilter(e.target.dataset.filter);
      });
    });

    // Modal close
    document.getElementById("close-modal").addEventListener("click", () => {
      document.getElementById("game-end-modal").style.display = "none";
    });

    // Auto-scroll chat
    this.setupAutoScroll();
  }

  initializeSocketEvents() {
    this.socket.on("connect", () => {
      this.updateConnectionStatus(true);
      console.log("Connected to game server");
    });

    this.socket.on("disconnect", () => {
      this.updateConnectionStatus(false);
      console.log("Disconnected from game server");
    });

    this.socket.on("game_update", (data) => {
      this.handleGameUpdate(data);
    });

    this.socket.on("game_started", (data) => {
      this.showMessage("Game starting...", "success");
      this.clearChat();
    });

    this.socket.on("game_stopped", (data) => {
      this.showMessage("Game stopped", "info");
    });

    this.socket.on("game_state", (state) => {
      this.updateGameState(state);
    });

    this.socket.on("game_over", (data) => {
      this.showGameEnd(data);
    });

    this.socket.on("error", (data) => {
      this.showMessage(`Error: ${data.message}`, "error");
    });
  }

  initializeChart() {
    const ctx = document.getElementById("vote-chart").getContext("2d");
    this.voteChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: [],
        datasets: [
          {
            label: "Votes",
            data: [],
            backgroundColor: "rgba(78, 205, 196, 0.6)",
            borderColor: "rgba(78, 205, 196, 1)",
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false,
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              stepSize: 1,
              color: "#bdc3c7",
            },
            grid: {
              color: "rgba(255, 255, 255, 0.1)",
            },
          },
          x: {
            ticks: {
              color: "#bdc3c7",
            },
            grid: {
              color: "rgba(255, 255, 255, 0.1)",
            },
          },
        },
      },
    });
  }

  startGame() {
    this.socket.emit("start_game");
    document.getElementById("start-game").disabled = true;
    document.getElementById("start-game").innerHTML =
      '<span class="loading"></span> Starting...';

    setTimeout(() => {
      document.getElementById("start-game").disabled = false;
      document.getElementById("start-game").textContent = "Start New Game";
    }, 3000);
  }

  stopGame() {
    this.socket.emit("stop_game");
  }

  updateConnectionStatus(connected) {
    const statusElement = document.getElementById("connection-status");
    if (connected) {
      statusElement.textContent = "Connected";
      statusElement.className = "connection-status connected";
    } else {
      statusElement.textContent = "Disconnected";
      statusElement.className = "connection-status disconnected";
    }
  }

  handleGameUpdate(update) {
    const { type, data } = update;

    switch (type) {
      case "new_message":
        this.addChatMessage(data);
        break;
      case "game_state":
        this.updateGameState(data);
        break;
      case "player_action":
        this.handlePlayerAction(data);
        break;
      case "phase_change":
        this.handlePhaseChange(data);
        break;
      default:
        console.log("Unknown update type:", type, data);
    }
  }

  addChatMessage(messageData) {
    const chatMessages = document.getElementById("chat-messages");
    const messageDiv = document.createElement("div");

    // Determine message class based on chat type
    let messageClass = "message";
    if (messageData.chat_type === "mafia") {
      messageClass += " mafia-chat";
    } else if (messageData.chat_type === "private") {
      messageClass += " private-chat";
    }

    messageDiv.className = messageClass;
    messageDiv.dataset.chatType = messageData.chat_type;
    messageDiv.dataset.sender = messageData.sender;

    // Get sender role for styling
    const senderRole = this.getSenderRole(messageData.sender);
    const roleClass = senderRole ? `sender-${senderRole}` : "sender-civilian";

    // Format timestamp
    const timestamp = new Date(messageData.timestamp).toLocaleTimeString();

    messageDiv.innerHTML = `
            <div class="message-sender ${roleClass}">
                ${messageData.sender}
                ${messageData.chat_type === "mafia" ? "🔴" : ""}
                ${messageData.chat_type === "private" ? "🔒" : ""}
            </div>
            <div class="message-content">${this.formatMessageContent(
              messageData.message
            )}</div>
            <div class="message-timestamp">${timestamp}</div>
        `;

    // Add animation class
    messageDiv.classList.add("new");
    setTimeout(() => messageDiv.classList.remove("new"), 500);

    chatMessages.appendChild(messageDiv);
    this.applyCurrentFilter();
    this.scrollToBottom();

    // Remove welcome message if present
    const welcomeMessage = chatMessages.querySelector(".welcome-message");
    if (welcomeMessage) {
      welcomeMessage.remove();
    }

    this.messageCount++;
  }

  formatMessageContent(content) {
    // Add basic formatting for game messages
    content = content.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    content = content.replace(/_(.*?)_/g, "<em>$1</em>");

    // Add emoji for common game terms
    content = content.replace(/\bmedia\b/gi, "🔴 mafia");
    content = content.replace(/\bdetective\b/gi, "🔍 detective");
    content = content.replace(/\bdoctor\b/gi, "🏥 doctor");
    content = content.replace(/\bvote\b/gi, "🗳️ vote");
    content = content.replace(/\beliminate\b/gi, "💀 eliminate");

    return content;
  }

  getSenderRole(senderName) {
    if (!this.gameState || !this.gameState.players) return null;

    const player = this.gameState.players[senderName];
    return player ? player.role : null;
  }

  updateGameState(state) {
    this.gameState = state;

    if (!state.stats) return;

    // Update status panel
    document.getElementById("current-phase").textContent = state.stats.phase;
    document.getElementById("current-day").textContent = state.stats.day_count;
    document.getElementById("alive-count").textContent =
      state.stats.total_alive;
    document.getElementById("eliminated-count").textContent =
      state.stats.eliminated_count;

    // Update players grid
    this.updatePlayersGrid(state);

    // Update vote chart
    this.updateVoteChart(state.stats.vote_counts || {});

    // Update individual votes display
    this.updateIndividualVotes(state.votes || {});

    // Update progress stats
    this.updateProgressStats(state.stats);

    // Update events timeline
    this.updateEventsTimeline(state.recent_events || []);
  }

  updatePlayersGrid(state) {
    const playersGrid = document.getElementById("players-grid");
    playersGrid.innerHTML = "";

    if (!state.players) return;

    Object.entries(state.players).forEach(([name, info]) => {
      if (name === "Narrator") return;

      const playerCard = document.createElement("div");
      playerCard.className = `player-card ${
        info.status === "eliminated" ? "eliminated" : ""
      }`;

      const roleClass = `role-${info.role}`;
      const statusClass =
        info.status === "alive" ? "status-alive" : "status-eliminated";

      playerCard.innerHTML = `
                <div class="player-name">${name}</div>
                <div class="player-role ${roleClass}">${info.role}</div>
                <div class="player-status-indicator ${statusClass}"></div>
                <div class="player-votes">${
                  info.votes_received || 0
                } votes</div>
            `;

      playersGrid.appendChild(playerCard);
    });
  }

  updateVoteChart(voteCounts) {
    if (!this.voteChart) return;

    const labels = Object.keys(voteCounts);
    const data = Object.values(voteCounts);

    this.voteChart.data.labels = labels;
    this.voteChart.data.datasets[0].data = data;
    this.voteChart.update();
  }

  updateIndividualVotes(votes) {
    const votesList = document.getElementById("individual-votes-list");
    const votingStatus = document.getElementById("voting-status");
    votesList.innerHTML = "";

    // Show voting status if we're in voting phase and no votes yet
    if (
      this.gameState &&
      this.gameState.stats &&
      this.gameState.stats.phase === "day" &&
      Object.keys(votes).length === 0
    ) {
      votingStatus.style.display = "block";
    } else {
      votingStatus.style.display = "none";
    }

    // Clear previous votes if we're starting a new voting phase
    if (Object.keys(votes).length === 0) {
      this.previousVotes.clear();
      votesList.innerHTML =
        '<div class="vote-item"><span>No votes cast yet</span></div>';
      return;
    }

    Object.entries(votes).forEach(([voter, target]) => {
      const voteItem = document.createElement("div");
      const voteKey = `${voter}->${target}`;
      const isNewVote = !this.previousVotes.has(voteKey);

      voteItem.className = isNewVote ? "vote-item new-vote" : "vote-item";

      voteItem.innerHTML = `
        <span class="vote-voter">${voter}</span>
        <span class="vote-arrow">→</span>
        <span class="vote-target">${target}</span>
      `;

      votesList.appendChild(voteItem);

      // Add to previous votes set
      this.previousVotes.add(voteKey);

      // Remove highlight class after animation
      if (isNewVote) {
        setTimeout(() => {
          voteItem.classList.remove("new-vote");
        }, 2000);
      }
    });
  }

  updateProgressStats(stats) {
    document.getElementById("mafia-count").textContent = stats.alive_mafia || 0;
    document.getElementById("civilian-count").textContent =
      stats.alive_civilians || 0;

    const eliminationRate =
      stats.total_alive > 0
        ? Math.round(
            (stats.eliminated_count /
              (stats.total_alive + stats.eliminated_count)) *
              100
          )
        : 0;
    document.getElementById(
      "elimination-rate"
    ).textContent = `${eliminationRate}%`;
  }

  updateEventsTimeline(events) {
    const timeline = document.getElementById("events-timeline");
    timeline.innerHTML = "";

    events.slice(-10).forEach((event) => {
      const eventDiv = document.createElement("div");
      eventDiv.className = "timeline-event";

      const timestamp = new Date(event.timestamp).toLocaleTimeString();

      eventDiv.innerHTML = `
                <div class="event-type">${this.formatEventType(
                  event.type
                )}</div>
                <div class="event-description">${this.formatEventDescription(
                  event
                )}</div>
                <div class="event-timestamp">${timestamp}</div>
            `;

      timeline.appendChild(eventDiv);
    });
  }

  formatEventType(type) {
    const eventTypes = {
      elimination: "💀 Elimination",
      investigation: "🔍 Investigation",
      protection: "🛡️ Protection",
      vote: "🗳️ Vote",
      phase_change: "🔄 Phase Change",
      game_start: "🎮 Game Start",
      game_end: "🏁 Game End",
    };

    return eventTypes[type] || `📝 ${type}`;
  }

  formatEventDescription(event) {
    switch (event.type) {
      case "elimination":
        return `${event.player} (${event.role}) was eliminated`;
      case "phase_change":
        return `Game phase changed to ${event.phase}`;
      case "vote":
        return `${event.voter} voted for ${event.target}`;
      default:
        return JSON.stringify(event);
    }
  }

  setFilter(filter) {
    this.currentFilter = filter;

    // Update filter buttons
    document.querySelectorAll(".filter-btn").forEach((btn) => {
      btn.classList.remove("active");
    });
    document.querySelector(`[data-filter="${filter}"]`).classList.add("active");

    this.applyCurrentFilter();
  }

  applyCurrentFilter() {
    const messages = document.querySelectorAll(".message");

    messages.forEach((message) => {
      const chatType = message.dataset.chatType;
      const sender = message.dataset.sender;

      let show = false;

      switch (this.currentFilter) {
        case "all":
          show = true;
          break;
        case "public":
          show = chatType === "public";
          break;
        case "mafia":
          show = chatType === "mafia";
          break;
        case "narrator":
          show = sender === "Narrator";
          break;
      }

      message.style.display = show ? "block" : "none";
    });
  }

  setupAutoScroll() {
    const chatMessages = document.getElementById("chat-messages");
    let userScrolled = false;

    chatMessages.addEventListener("scroll", () => {
      const isScrolledToBottom =
        chatMessages.scrollHeight - chatMessages.clientHeight <=
        chatMessages.scrollTop + 1;
      userScrolled = !isScrolledToBottom;
    });

    this.scrollToBottom = () => {
      if (!userScrolled) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
      }
    };
  }

  scrollToBottom() {
    const chatMessages = document.getElementById("chat-messages");
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  clearChat() {
    const chatMessages = document.getElementById("chat-messages");
    chatMessages.innerHTML =
      '<div class="welcome-message"><h3>Game Starting...</h3><p>AI agents are being initialized...</p></div>';
    this.messageCount = 0;
  }

  showGameEnd(data) {
    const modal = document.getElementById("game-end-modal");
    const announcement = document.getElementById("winner-announcement");
    const finalStats = document.getElementById("final-stats");

    // Set winner announcement
    if (data.winner === "mafia") {
      announcement.textContent = "🔴 MAFIA VICTORY! 🔴";
      announcement.style.color = "#e74c3c";
    } else {
      announcement.textContent = "🟢 CIVILIAN VICTORY! 🟢";
      announcement.style.color = "#27ae60";
    }

    // Set final statistics
    const stats = data.stats;
    finalStats.innerHTML = `
            <div class="stat-item">
                <span>Game Duration:</span>
                <span>${stats.day_count} days</span>
            </div>
            <div class="stat-item">
                <span>Total Players:</span>
                <span>${stats.total_alive + stats.eliminated_count}</span>
            </div>
            <div class="stat-item">
                <span>Survivors:</span>
                <span>${stats.total_alive}</span>
            </div>
            <div class="stat-item">
                <span>Eliminated:</span>
                <span>${stats.eliminated_count}</span>
            </div>
            <div class="stat-item">
                <span>Mafia Members:</span>
                <span>${stats.mafia_members.join(", ")}</span>
            </div>
        `;

    modal.style.display = "block";
  }

  showMessage(message, type = "info") {
    // Simple toast notification
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 600;
            z-index: 1000;
            animation: slideInRight 0.3s ease-out;
        `;

    switch (type) {
      case "success":
        toast.style.backgroundColor = "#27ae60";
        break;
      case "error":
        toast.style.backgroundColor = "#e74c3c";
        break;
      case "warning":
        toast.style.backgroundColor = "#f39c12";
        break;
      default:
        toast.style.backgroundColor = "#3498db";
    }

    document.body.appendChild(toast);

    setTimeout(() => {
      toast.remove();
    }, 3000);
  }

  handlePlayerAction(data) {
    // Handle specific player actions if needed
    console.log("Player action:", data);
  }

  handlePhaseChange(data) {
    // Handle phase changes with special effects
    this.showMessage(`Phase changed to: ${data.phase}`, "info");
  }
}

// Initialize the game interface when the page loads
document.addEventListener("DOMContentLoaded", () => {
  window.gameInterface = new MafiaGameInterface();
});

// Add CSS for toast animations
const style = document.createElement("style");
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);
