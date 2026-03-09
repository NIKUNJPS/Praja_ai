/**
 * WebSocket Service for Real-Time Live Alerts
 * Auto-connect, exponential reconnect with jitter, message dispatcher, heartbeat
 */

class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.baseReconnectDelay = 1000; // 1 second
    this.maxReconnectDelay = 30000; // 30 seconds
    this.listeners = new Map();
    this.isConnected = false;
    this.shouldReconnect = true;
    this.heartbeatInterval = null;
    this.connectionCheckInterval = null;
  }

  // Public: Connect to WebSocket server
  connect() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('[WebSocket] Already connected');
      return;
    }

    // Ensure we don't have a stale connection
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
    // Default to localhost if not set
    const baseUrl = backendUrl || (window.location.protocol === 'https:' ? 'https://localhost:8000' : 'http://localhost:8000');
    const wsUrl = baseUrl.replace('https://', 'wss://').replace('http://', 'ws://');
    const wsEndpoint = `${wsUrl}/ws/live-alerts`;

    console.log('[WebSocket] Connecting to:', wsEndpoint);

    try {
      this.ws = new WebSocket(wsEndpoint);

      this.ws.onopen = this._handleOpen.bind(this);
      this.ws.onmessage = this._handleMessage.bind(this);
      this.ws.onerror = this._handleError.bind(this);
      this.ws.onclose = this._handleClose.bind(this);

      // Listen for online/offline events to reconnect when network comes back
      window.addEventListener('online', this._handleOnline.bind(this));
      window.addEventListener('offline', this._handleOffline.bind(this));

      // Start periodic connection check
      this._startConnectionCheck();
    } catch (error) {
      console.error('[WebSocket] Connection failed:', error);
      this._scheduleReconnect();
    }
  }

  // Public: Disconnect and stop reconnecting
  disconnect() {
    this.shouldReconnect = false;
    this._clearIntervals();
    window.removeEventListener('online', this._handleOnline);
    window.removeEventListener('offline', this._handleOffline);

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
    this.listeners.clear();
  }

  // Public: Send a message to the server
  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('[WebSocket] Cannot send message, not connected');
    }
  }

  // Public: Register an event listener
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  // Public: Remove an event listener
  off(event, callback) {
    if (!this.listeners.has(event)) return;
    const callbacks = this.listeners.get(event).filter(cb => cb !== callback);
    if (callbacks.length === 0) {
      this.listeners.delete(event);
    } else {
      this.listeners.set(event, callbacks);
    }
  }

  // Public: Get current connection status
  getConnectionStatus() {
    return this.isConnected;
  }

  // Private: Handle WebSocket open event
  _handleOpen() {
    console.log('✅ [WebSocket] Connected');
    this.isConnected = true;
    this.reconnectAttempts = 0;
    this._emit('connection_status', { connected: true });

    // Start heartbeat
    this._startHeartbeat();
  }

  // Private: Handle incoming messages
  _handleMessage(event) {
    try {
      const message = JSON.parse(event.data);
      console.log('[WebSocket] Message received:', message);

      // Dispatch to specific listeners
      if (message.type) {
        this._emit(message.type, message);
      }
      // Always emit to 'message' listener
      this._emit('message', message);
    } catch (error) {
      console.error('[WebSocket] Failed to parse message:', error);
    }
  }

  // Private: Handle WebSocket error
  _handleError(error) {
    console.error('[WebSocket] Error:', error);
    this._emit('connection_status', { connected: false, error: true });
  }

  // Private: Handle WebSocket close
  _handleClose() {
    console.log('❌ [WebSocket] Disconnected');
    this.isConnected = false;
    this._clearIntervals();
    this._emit('connection_status', { connected: false });

    if (this.shouldReconnect) {
      this._scheduleReconnect();
    }
  }

  // Private: Schedule reconnection with exponential backoff + jitter
  _scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WebSocket] Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    // Exponential backoff with full jitter
    const exponentialDelay = this.baseReconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    const cappedDelay = Math.min(exponentialDelay, this.maxReconnectDelay);
    const jitter = Math.random() * cappedDelay;
    const delay = Math.min(cappedDelay + jitter, this.maxReconnectDelay);

    console.log(`[WebSocket] Reconnecting in ${Math.round(delay)}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    setTimeout(() => {
      if (this.shouldReconnect) {
        this.connect();
      }
    }, delay);
  }

  // Private: Start heartbeat to keep connection alive
  _startHeartbeat() {
    this._clearHeartbeat();
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping' });
      }
    }, 30000); // every 30 seconds
  }

  // Private: Start periodic connection check (reconnect if unexpectedly closed)
  _startConnectionCheck() {
    this._clearConnectionCheck();
    this.connectionCheckInterval = setInterval(() => {
      if (this.shouldReconnect && this.ws && this.ws.readyState === WebSocket.CLOSED) {
        console.log('[WebSocket] Connection check: closed, reconnecting');
        this.connect();
      }
    }, 10000); // every 10 seconds
  }

  // Private: Clear intervals
  _clearIntervals() {
    this._clearHeartbeat();
    this._clearConnectionCheck();
  }

  _clearHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  _clearConnectionCheck() {
    if (this.connectionCheckInterval) {
      clearInterval(this.connectionCheckInterval);
      this.connectionCheckInterval = null;
    }
  }

  // Private: Emit event to listeners
  _emit(event, data) {
    if (!this.listeners.has(event)) return;
    this.listeners.get(event).forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error(`[WebSocket] Listener error for event '${event}':`, error);
      }
    });
  }

  // Private: Handle online event (reconnect immediately)
  _handleOnline() {
    console.log('[WebSocket] Network online, reconnecting...');
    if (this.shouldReconnect && (!this.ws || this.ws.readyState !== WebSocket.OPEN)) {
      this.connect();
    }
  }

  // Private: Handle offline event (stop reconnection attempts)
  _handleOffline() {
    console.log('[WebSocket] Network offline');
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Singleton instance
const websocketService = new WebSocketService();

export default websocketService;