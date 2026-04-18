import socket
import json
import threading
import time
from traceback import print_exc

class NetworkManager:
    def __init__(self, port=5005, broadcast_port=5006):
        self.port = port
        self.broadcast_port = broadcast_port
        self.running = False
        self.is_host = False
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Enable broadcasting
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Allow port reuse
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.sock.bind(("", self.port))
        except Exception as e:
            print("Could not bind to port:", e)
        
        self.peers = set() # (ip, port)
        self.host_addr = None # (ip, port) if client
        
        self.incoming_messages = []
        self.discovered_hosts = {} # addr: info
        
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        
    def start(self):
        self.running = True
        self.thread.start()
        
    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()
            
    def set_host(self, is_host: bool):
        self.is_host = is_host
        
    def broadcast_lobby(self, info: dict):
        if not self.is_host: return
        msg = {"type": "LOBBY_INFO", "info": info}
        data = json.dumps(msg).encode('utf-8')
        try:
            # Broadcast to entire local network
            self.sock.sendto(data, ('<broadcast>', self.broadcast_port))
        except Exception as e:
             pass

    def request_join(self, host_addr):
        self.host_addr = host_addr
        self.send_to({"type": "JOIN_REQ"}, host_addr)
        
    def send_to(self, msg_dict, addr):
        try:
            data = json.dumps(msg_dict).encode('utf-8')
            self.sock.sendto(data, addr)
        except Exception:
            print_exc()

    def broadcast_to_peers(self, msg_dict):
        for peer in self.peers:
            self.send_to(msg_dict, peer)

    def _listen_loop(self):
        # We need a secondary socket just for receiving broadcasts if we're a client
        broadcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        # Try to bind to broadcast port to receive lobby infos
        try:
             broadcast_sock.bind(("", self.broadcast_port))
             broadcast_sock.settimeout(0.5)
        except:
             broadcast_sock = None
             
        self.sock.settimeout(0.5)

        while self.running:
            # Receive direct messages
            try:
                data, addr = self.sock.recvfrom(4096)
                msg = json.loads(data.decode('utf-8'))
                self._handle_msg(msg, addr)
            except socket.timeout:
                pass
            except Exception as e:
                pass
                
            # Receive broadcasts (clients listening for hosts)
            if not self.is_host and broadcast_sock:
                try:
                    data, addr = broadcast_sock.recvfrom(4096)
                    msg = json.loads(data.decode('utf-8'))
                    if msg.get("type") == "LOBBY_INFO":
                        self.discovered_hosts[addr] = msg.get("info")
                except:
                    pass

        if broadcast_sock:
             broadcast_sock.close()

    def _handle_msg(self, msg, addr):
        mtype = msg.get("type")
        if self.is_host:
            if mtype == "JOIN_REQ":
                if addr not in self.peers:
                    self.peers.add(addr)
                    # Tell them they are accepted
                    self.send_to({"type": "JOIN_ACK"}, addr)
            elif mtype == "ACTION":
                # Resend action to all other peers, except sender
                for p in self.peers:
                    if p != addr:
                        self.send_to(msg, p)
                self.incoming_messages.append(msg)
        else:
            if mtype == "JOIN_ACK":
                print("Joined host:", addr)
                self.host_addr = addr
            elif mtype in ["START_GAME", "ACTION"]:
                self.incoming_messages.append(msg)

    def get_messages(self):
        msgs = list(self.incoming_messages)
        self.incoming_messages.clear()
        return msgs
