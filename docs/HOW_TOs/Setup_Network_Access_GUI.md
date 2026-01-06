# Setup Network Access: GUI Interface

> **Share Your LLM Framework GUI on Your Local Network**
> Enable other devices on your network to access the web-based GUI interface running on your computer.

---

## Table of Contents

1. [What is GUI Network Access?](#what-is-gui-network-access)
2. [Security Considerations](#security-considerations)
3. [Quick Start (Recommended Method)](#quick-start-recommended-method)
4. [GUI Network Access Options](#gui-network-access-options)
5. [Starting GUI with Network Access](#starting-gui-with-network-access)
6. [Finding Your GUI Address](#finding-your-gui-address)
7. [Accessing GUI from Other Devices](#accessing-gui-from-other-devices)
8. [Managing the GUI](#managing-the-gui)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)
11. [Summary](#summary)

---

## What is GUI Network Access?

The LLM Framework provides a web-based graphical interface (GUI) powered by Gradio. By default, the GUI only accepts connections from your local computer (`127.0.0.1` or `localhost`). **GUI network access** allows other devices on your local network to access the GUI through their web browsers.

### Default vs Network Access

| Aspect | Localhost Only (Default) | Network Access (--share) |
|--------|-------------------------|-------------------------|
| **Binding** | 127.0.0.1 (localhost) | 0.0.0.0 (all interfaces) |
| **Access** | Only your computer | Any device on network |
| **Security** | Secure (isolated) | Less secure (exposed) |
| **Use Case** | Personal use | Share with team/devices |
| **Setup** | Automatic | Requires `--share` flag |
| **Authentication** | Optional | Highly recommended (`--key`) |

### What the GUI Provides

When you access the GUI from a browser, you can:

- **Chat with your LLM** through a web interface
- **Manage the LLM server** (start/stop/status)
- **Download and manage models** visually
- **Edit configuration files** without command line
- **Manage memory and data stores** with point-and-click
- **View and edit LLM memory** through a web interface

### Use Cases

**When to enable GUI network access:**
- Access LLM from your phone or tablet
- Share LLM with family/team on same network
- Use GUI from any device in your home/office
- Convenient access without SSH or terminal
- Visual interface for non-technical users

**When to keep it localhost:**
- Personal use only on one computer
- Security is critical
- You prefer command line interface
- No need for remote browser access

---

## Security Considerations

⚠️ **CRITICAL SECURITY WARNING** ⚠️

Enabling GUI network access has serious security implications. Understanding these risks is essential.

### Risks

1. **No Built-in Authentication (Without --key)**:
   - Anyone on your network can access your LLM
   - No password protection by default
   - Full control over your LLM Framework

2. **Full Access When Exposed**:
   - Start/stop LLM servers
   - Download large models (using your bandwidth)
   - Modify configuration files
   - Access all memory and data stores
   - Execute LLM queries (using your resources)

3. **Resource Consumption**:
   - Others can consume CPU/GPU/RAM
   - Bandwidth usage for model downloads
   - Disk space for downloaded models
   - No rate limiting

4. **Privacy Concerns**:
   - Others can see LLM responses
   - Access to memory contents
   - Visibility into configuration

5. **Network Exposure**:
   - Visible to all devices on network
   - No encryption (HTTP, not HTTPS)
   - Vulnerable to network sniffing

### Security Best Practices

✅ **STRONGLY RECOMMENDED:**
- **Always use `--key` for authentication** when using `--share`
- Use a strong, unique password (not "password" or "123456")
- Only enable on trusted networks (home, office)
- Turn off when not needed
- Monitor who's accessing the GUI
- Use strong WiFi password
- Consider firewall rules to limit access

✅ **DO:**
- Use `llf gui start --share --key STRONG_PASSWORD`
- Choose a secret key that's hard to guess
- Share the key only with trusted users
- Stop GUI when sharing is no longer needed
- Check GUI status regularly: `llf gui status`
- Monitor resource usage

❌ **DON'T:**
- Use `--share` without `--key` (no authentication!)
- Use weak passwords like "password", "admin", "123456"
- Enable on public WiFi or untrusted networks
- Leave it running unattended without authentication
- Share your secret key publicly
- Expose to the internet (no firewall port forwarding!)

### Authentication is CRITICAL

**Without `--key`:**
```bash
llf gui start --share
# ⚠️ DANGER: Anyone on network has full access!
```

**With `--key` (RECOMMENDED):**
```bash
llf gui start --share --key MyStrongSecretPassword123
# ✅ SECURE: Requires password to access GUI
```

### Recommended Security Setup

For the most secure network access:

```bash
# Use strong authentication
llf gui start --daemon --share --key "MyVeryStrongPassword123!@#"
```

This setup:
- Runs in background (`--daemon`)
- Accessible on network (`--share`)
- Requires authentication (`--key`)
- Can be accessed from any device on your network
- Protects against unauthorized access

---

## Quick Start (Recommended Method)

The fastest and most secure way to share your GUI on the network.

### Step 1: Start GUI with Authentication

```bash
# Activate virtual environment first
source llf_venv/bin/activate

# Start GUI with network access and authentication
llf gui start --daemon --share --key MySecretPassword
```

**What this does:**
- Starts GUI in background (daemon mode)
- Makes it accessible on your local network (`0.0.0.0:7860`)
- Requires password authentication
- Terminal remains free for other commands

### Step 2: Find Your IP Address

**macOS:**
```bash
ipconfig getifaddr en0  # WiFi
```

**Linux:**
```bash
hostname -I | awk '{print $1}'
```

**Windows:**
```bash
ipconfig
# Look for "IPv4 Address"
```

Example result: `192.168.1.100`

### Step 3: Access from Other Devices

On any device on your network:

1. Open a web browser
2. Navigate to: `http://192.168.1.100:7860`
3. Enter the secret key: `MySecretPassword`
4. Click "Login"
5. Start using the GUI!

### Step 4: Stop When Done

When you're finished sharing:

```bash
llf gui stop
```

---

## GUI Network Access Options

The `llf gui` command provides several options for network access.

### Command Structure

```bash
llf gui [ACTION] [OPTIONS]
```

### Actions

| Action | Description |
|--------|-------------|
| `start` | Start the GUI (default if not specified) |
| `stop` | Stop a running GUI daemon |
| `status` | Check if GUI daemon is running |

### Network Options

| Option | Description | Default |
|--------|-------------|---------|
| `--share` | Make GUI accessible on local network (binds to 0.0.0.0) | False (localhost only) |
| `--key SECRET` | Require authentication with secret key | None (no auth) |
| `--daemon` | Run GUI in background (daemon mode) | False (foreground) |
| `--port PORT` | Custom port number | 7860 |
| `--no-browser` | Don't automatically open browser | False (opens browser) |

### Common Combinations

**Basic network access (NOT RECOMMENDED - no auth):**
```bash
llf gui start --share
# ⚠️ No authentication! Anyone on network can access
```

**Network access with authentication (RECOMMENDED):**
```bash
llf gui start --share --key MyPassword
# ✅ Requires password to access
```

**Background network access with authentication (BEST):**
```bash
llf gui start --daemon --share --key MyPassword
# ✅ Runs in background + requires password
```

**Custom port with authentication:**
```bash
llf gui start --share --key MyPassword --port 8080
# Access at http://YOUR-IP:8080
```

**No browser auto-open (for servers):**
```bash
llf gui start --daemon --share --key MyPassword --no-browser
# Doesn't open browser automatically
```

---

## Starting GUI with Network Access

Detailed instructions for different scenarios.

### Localhost Only (Default - Secure)

For personal use on your computer only:

```bash
# Basic start (opens browser automatically)
llf gui

# Or explicitly
llf gui start

# In background
llf gui start --daemon
```

Access at: `http://localhost:7860` or `http://127.0.0.1:7860`

### Network Access WITHOUT Authentication (NOT RECOMMENDED)

⚠️ **WARNING: This is insecure!** Anyone on your network has full access.

```bash
# Foreground (terminal stays active)
llf gui start --share

# Background (daemon mode)
llf gui start --daemon --share
```

**When you start:**
```
Starting LLM Framework GUI...
Port: 7860
Server binding: 0.0.0.0 (network accessible)

⚠️  WARNING: GUI is accessible on local network WITHOUT authentication!
⚠️  Anyone on your network can access: http://192.168.1.100:7860

Running on local URL:  http://127.0.0.1:7860
Running on network URL: http://192.168.1.100:7860

GUI is running. Press Ctrl+C to stop.
```

### Network Access WITH Authentication (RECOMMENDED)

✅ **This is the secure way to share your GUI**

```bash
# Foreground with authentication
llf gui start --share --key MyStrongPassword123

# Background with authentication (BEST PRACTICE)
llf gui start --daemon --share --key MyStrongPassword123
```

**When you start:**
```
Starting LLM Framework GUI in daemon mode...
Port: 7860
Server binding: 0.0.0.0 (network accessible)
Authentication: ENABLED (secret key required)

✅ GUI started successfully!

Access URLs:
  Local:   http://127.0.0.1:7860
  Network: http://192.168.1.100:7860

🔐 Authentication is ENABLED
Users must enter the secret key to access the GUI.

GUI daemon PID: 12345
Use 'llf gui status' to check status
Use 'llf gui stop' to stop the daemon
```

### What Happens During Login

When someone accesses the GUI with authentication enabled:

1. **Initial page load:** Shows login screen
2. **User enters secret key:** Types the password you set with `--key`
3. **Key validation:** System checks if key matches
4. **Access granted/denied:**
   - ✅ Correct key → Full GUI access
   - ❌ Wrong key → "Invalid authentication key" error

### Example: Complete Workflow

```bash
# 1. Activate virtual environment
source llf_venv/bin/activate

# 2. Start GUI with network access and authentication
llf gui start --daemon --share --key "MyTeamPassword2024!"

# Output shows your network IP
# Access URLs:
#   Network: http://192.168.1.100:7860

# 3. Share the information with your team
# Tell them: "Go to http://192.168.1.100:7860 and use password: MyTeamPassword2024!"

# 4. Check GUI status anytime
llf gui status

# 5. When done, stop the GUI
llf gui stop
```

---

## Finding Your GUI Address

To access the GUI from other devices, you need your computer's IP address.

### Automatic Display

When you start the GUI with `--share`, it automatically displays your network IP:

```
Running on network URL: http://192.168.1.100:7860
```

This is the URL you share with others.

### Manual IP Discovery

If you need to find your IP manually:

**macOS:**
```bash
# WiFi connection
ipconfig getifaddr en0

# Ethernet connection
ipconfig getifaddr en1

# Or use System Settings
# System Settings > Network > [Your Connection] > Details
```

**Linux:**
```bash
# Method 1: hostname command
hostname -I | awk '{print $1}'

# Method 2: ip command
ip addr show | grep "inet " | grep -v 127.0.0.1

# Method 3: ifconfig
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**Windows:**
```cmd
# Command Prompt
ipconfig

# Look for "IPv4 Address" under your network adapter
```

### Typical IP Address Ranges

Your local IP will usually look like:
- `192.168.1.x` (most common home networks)
- `192.168.0.x`
- `10.0.0.x`
- `172.16.x.x` to `172.31.x.x`

Example: `192.168.1.100`

### GUI URL Format

Once you have your IP address:

```
http://YOUR-IP-ADDRESS:PORT
```

Examples:
- `http://192.168.1.100:7860` (default port)
- `http://192.168.1.100:8080` (custom port with `--port 8080`)

---

## Accessing GUI from Other Devices

Once the GUI is running with network access, other devices can connect.

### What to Share with Users

Provide these details:

```
GUI URL: http://192.168.1.100:7860
Secret Key: MySecretPassword (if using --key)
```

### From Another Computer

**On the remote computer:**

1. Open any web browser (Chrome, Firefox, Safari, Edge)
2. Navigate to: `http://192.168.1.100:7860`
3. If authentication is enabled:
   - Enter the secret key
   - Click "Login"
4. Use the GUI as if it were running locally

**Features available remotely:**
- Full chat interface with LLM
- Server management (start/stop/status)
- Model downloads and management
- Configuration editing
- Memory and data store management

### From Phone or Tablet

**On your mobile device:**

1. Connect to the same WiFi network as the server
2. Open mobile browser (Safari, Chrome, Firefox)
3. Navigate to: `http://192.168.1.100:7860`
4. Enter secret key if prompted
5. Use the mobile-friendly Gradio interface

**Mobile tips:**
- Works on iOS (iPhone/iPad) and Android
- Gradio interface is responsive
- May need to zoom for some controls
- Landscape mode may work better

### From Different Network Segments

If devices can't connect but are on "the same network":

**Check subnet:**
```bash
# Server IP: 192.168.1.100
# Client IP: 192.168.1.50  ✓ Same subnet (will work)
# Client IP: 192.168.2.50  ✗ Different subnet (won't work)
```

**Solutions:**
- Connect to the same WiFi network
- Check router VLAN/subnet settings
- Ensure no VPN is isolating traffic
- Try using server hostname: `http://server-name.local:7860`

### Testing Access

**From the server computer:**
```bash
# Test localhost access
curl http://127.0.0.1:7860

# Test network access
curl http://192.168.1.100:7860
```

**From remote computer:**
```bash
# Test connectivity
ping 192.168.1.100

# Test GUI access
curl http://192.168.1.100:7860
```

If `curl` returns HTML content, the GUI is accessible!

---

## Managing the GUI

Commands for controlling the GUI daemon.

### Check GUI Status

See if the GUI is running:

```bash
llf gui status
```

**If GUI is running:**
```
GUI Status: Running
PID: 12345
Port: 7860
Server: 0.0.0.0 (network accessible)
Authentication: ENABLED

Access URLs:
  Local:   http://127.0.0.1:7860
  Network: http://192.168.1.100:7860
```

**If GUI is not running:**
```
GUI Status: Not running (no daemon process)
Start GUI with: llf gui start --daemon
```

### Start GUI

**Basic start (localhost only):**
```bash
llf gui
# Or
llf gui start
```

**Network access with authentication (recommended):**
```bash
llf gui start --daemon --share --key MyPassword
```

**Custom port:**
```bash
llf gui start --share --key MyPassword --port 8080
```

### Stop GUI

Stop a running GUI daemon:

```bash
llf gui stop
```

**Output:**
```
✅ GUI stopped successfully
PID 12345 terminated
```

### Restart GUI

To restart with the same settings:

```bash
# Stop first
llf gui stop

# Wait a moment
sleep 2

# Start again
llf gui start --daemon --share --key MyPassword
```

**Note:** There's no built-in `restart` command, so you must stop and start manually.

### Force Stop

If `llf gui stop` doesn't work:

**Find the process:**
```bash
# Find Gradio/Python processes
ps aux | grep gradio

# Find by port
lsof -i :7860
```

**Kill the process:**
```bash
# Kill by PID
kill -9 PID

# Or kill all Python processes (CAREFUL!)
pkill -f "llf.cli gui"
```

---

## Troubleshooting

Common issues and solutions.

### Problem: "Connection Refused" from Remote Device

**Symptoms:**
- GUI works on server computer
- Remote devices can't connect
- Browser shows "Connection refused" or "Can't reach this page"

**Possible causes:**
1. GUI not started with `--share` flag
2. Firewall blocking connections
3. Wrong IP address
4. Different network/subnet

**Solutions:**

1. **Verify GUI is using `--share`:**
   ```bash
   llf gui status
   # Should show "Server: 0.0.0.0 (network accessible)"
   # If it shows "127.0.0.1", restart with --share
   ```

2. **Restart with network access:**
   ```bash
   llf gui stop
   llf gui start --daemon --share --key MyPassword
   ```

3. **Check firewall (macOS):**
   ```bash
   # System Settings > Network > Firewall
   # Allow incoming connections for Python or llf

   # Or temporarily disable for testing
   # (Re-enable after testing!)
   ```

4. **Check firewall (Linux):**
   ```bash
   # Allow port 7860
   sudo ufw allow 7860

   # Check status
   sudo ufw status

   # Or disable temporarily for testing
   sudo ufw disable  # Re-enable: sudo ufw enable
   ```

5. **Check firewall (Windows):**
   - Windows Defender Firewall > Allow an app
   - Add Python or llf to allowed apps
   - Allow on Private networks

6. **Verify correct IP:**
   ```bash
   # Make sure you're using the right IP
   ipconfig getifaddr en0  # macOS
   hostname -I  # Linux
   ipconfig  # Windows
   ```

### Problem: "Invalid Authentication Key"

**Symptoms:**
- Can access login page
- Entering password shows "Invalid authentication key"

**Solutions:**

1. **Verify the secret key:**
   - Make sure you're using the exact key from `--key`
   - Keys are case-sensitive
   - Check for extra spaces

2. **Check what key was used:**
   ```bash
   # GUI status doesn't show the key (security)
   # You must remember what you set with --key
   ```

3. **Restart with known key:**
   ```bash
   llf gui stop
   llf gui start --daemon --share --key "NewPasswordIKnow123"
   ```

### Problem: "Port Already in Use"

**Error:**
```
Error: Port 7860 is already in use
```

**Solutions:**

1. **Stop existing GUI:**
   ```bash
   llf gui stop
   ```

2. **Find and kill process:**
   ```bash
   # Find process using port
   lsof -i :7860

   # Kill it
   kill -9 PID
   ```

3. **Use different port:**
   ```bash
   llf gui start --share --key MyPassword --port 8080
   # Access at http://YOUR-IP:8080
   ```

### Problem: Very Slow or Timing Out

**Symptoms:**
- GUI loads slowly from remote devices
- Requests time out
- Chat responses are delayed

**Possible causes:**
1. Weak WiFi signal
2. Network congestion
3. Server overloaded
4. Large model or slow hardware

**Solutions:**

1. **Check network connection:**
   ```bash
   # From remote device, ping server
   ping 192.168.1.100

   # Should show low latency (<50ms)
   ```

2. **Use wired connection:**
   - Connect server computer via Ethernet
   - Reduces WiFi congestion

3. **Check server resources:**
   ```bash
   # On server machine
   top  # Check CPU/RAM usage

   # Look for high CPU or memory usage
   ```

4. **Use smaller model:**
   - Smaller models (3B-7B) respond faster
   - Large models (13B+) need more resources

5. **Close other applications:**
   - Free up RAM and CPU
   - Stop other LLM servers if running

### Problem: Can't Find GUI (No Login Page)

**Solutions:**

1. **Verify devices on same network:**
   ```bash
   # On server
   ipconfig getifaddr en0  # Get IP: 192.168.1.100

   # On client
   ipconfig getifaddr en0  # Should be 192.168.1.x
   ```

2. **Check subnet:**
   - Both devices should have similar IPs
   - Server: `192.168.1.100`
   - Client: `192.168.1.50` ✓ (same subnet)
   - Client: `192.168.2.50` ✗ (different subnet)

3. **Try hostname:**
   ```bash
   # Instead of IP, try hostname
   http://your-computer-name.local:7860
   ```

4. **Disable VPN:**
   - Some VPNs isolate network traffic
   - Temporarily disable VPN on client device

### Problem: GUI Works but LLM Server Won't Start

**Symptoms:**
- Can access GUI
- "Server is not running" message
- Can't start server from GUI

**Solutions:**

1. **Check server configuration:**
   - Verify `configs/config.json` has correct paths
   - Ensure model is downloaded

2. **Start server from command line:**
   ```bash
   # Test if server can start manually
   llf server start

   # Check for error messages
   ```

3. **Check model availability:**
   ```bash
   llf model list
   # Ensure your model is downloaded
   ```

4. **Review GUI server logs:**
   - Check terminal output if running in foreground
   - Look for error messages

---

## Best Practices

### Security

1. **Always Use Authentication for Network Access**
   ```bash
   # ✅ GOOD
   llf gui start --daemon --share --key "StrongPassword123!"

   # ❌ BAD
   llf gui start --daemon --share  # No authentication!
   ```

2. **Use Strong Secret Keys**
   - Minimum 12 characters
   - Mix of letters, numbers, symbols
   - Not easily guessable
   - Examples:
     - ✅ `MyTeam2024!SecureGUI`
     - ✅ `LLM-Access-2024-Q1`
     - ❌ `password`
     - ❌ `12345`

3. **Trusted Networks Only**
   - Home networks: ✅
   - Office networks: ✅ (if trusted)
   - Public WiFi: ❌ NEVER
   - Coffee shop: ❌ NEVER
   - Hotel WiFi: ❌ NEVER

4. **Stop When Not Needed**
   ```bash
   # When done sharing
   llf gui stop

   # Verify it stopped
   llf gui status
   ```

5. **Monitor Access**
   - Check who's connecting
   - Monitor resource usage
   - Watch for unusual activity

6. **Keep Keys Private**
   - Don't post keys in public chats
   - Share keys securely (in person, encrypted messaging)
   - Change keys periodically

### Performance

1. **Use Daemon Mode**
   ```bash
   # Runs in background, frees terminal
   llf gui start --daemon --share --key MyPassword
   ```

2. **Wired Connection for Server**
   - Connect server via Ethernet if possible
   - More stable than WiFi
   - Better for heavy usage

3. **Good WiFi Signal**
   - Strong signal for client devices
   - 5GHz WiFi if available
   - Reduce interference

4. **Resource Management**
   - Monitor CPU/RAM usage
   - Don't overload with concurrent users
   - Use appropriate model size

### Convenience

1. **Static IP for Server (Optional)**
   - Configure router to assign static IP
   - Easier to remember
   - No need to look up IP each time
   - Example: Always use `192.168.1.100`

2. **Bookmarks**
   - Save GUI URL as bookmark on client devices
   - Quick access without typing IP

3. **Documentation**
   - Keep a note of your setup:
     ```
     GUI URL: http://192.168.1.100:7860
     Secret Key: [stored securely]
     Started with: llf gui start --daemon --share --key PASSWORD
     ```

4. **Hostname Access (Optional)**
   ```bash
   # Configure local DNS or mDNS
   # Access as: http://my-llm-server.local:7860
   # Instead of: http://192.168.1.100:7860
   ```

### Backup and Scripts

1. **Start Script**

   Create `start_gui_network.sh`:
   ```bash
   #!/bin/bash
   source llf_venv/bin/activate
   llf gui start --daemon --share --key "MySecretPassword"
   llf gui status
   ```

   Make it executable:
   ```bash
   chmod +x start_gui_network.sh
   ./start_gui_network.sh
   ```

2. **Stop Script**

   Create `stop_gui.sh`:
   ```bash
   #!/bin/bash
   source llf_venv/bin/activate
   llf gui stop
   ```

3. **Status Check Script**

   Create `check_gui.sh`:
   ```bash
   #!/bin/bash
   source llf_venv/bin/activate
   llf gui status
   ```

---

## Summary

You now know how to share your LLM Framework GUI on your local network securely.

### Key Takeaways

1. **Two Access Modes:**
   - **Localhost (Default)**: `llf gui start` → Only your computer
   - **Network (--share)**: `llf gui start --share` → All devices on network

2. **Always Use Authentication:**
   ```bash
   # RECOMMENDED COMMAND
   llf gui start --daemon --share --key "YourStrongPassword"
   ```

3. **Security is Critical:**
   - ⚠️ `--share` without `--key` is DANGEROUS
   - ✅ Always use strong passwords with `--key`
   - Only enable on trusted networks
   - Stop when not needed

4. **Access from Other Devices:**
   - Find your IP: `ipconfig getifaddr en0` (macOS)
   - Access at: `http://YOUR-IP:7860`
   - Enter secret key to login
   - Full GUI functionality remotely

5. **Management Commands:**
   ```bash
   llf gui status  # Check if running
   llf gui stop    # Stop the GUI
   ```

### Quick Reference

**Start GUI with network access (SECURE):**
```bash
source llf_venv/bin/activate
llf gui start --daemon --share --key "MyStrongPassword123"
```

**Find your IP:**
```bash
ipconfig getifaddr en0  # macOS WiFi
hostname -I             # Linux
ipconfig                # Windows
```

**Access from other devices:**
```
1. Open browser
2. Go to: http://YOUR-IP:7860
3. Enter secret key
4. Use the GUI!
```

**Stop when done:**
```bash
llf gui stop
```

**Check status:**
```bash
llf gui status
```

### Security Checklist

Before enabling network access:

- [ ] Using a trusted network (home/office)
- [ ] Using `--key` with a strong password
- [ ] Shared key only with trusted users
- [ ] Plan to stop GUI when not needed
- [ ] Know how to check status: `llf gui status`
- [ ] Know how to stop: `llf gui stop`
- [ ] Firewall allows port 7860 (if applicable)

### Common Use Cases

**1. Access from phone/tablet:**
```bash
llf gui start --daemon --share --key "MobileAccess2024"
# Access from phone at http://YOUR-IP:7860
```

**2. Share with family:**
```bash
llf gui start --daemon --share --key "FamilyPassword"
# Tell family: "Go to http://192.168.1.100:7860, password: FamilyPassword"
```

**3. Team collaboration:**
```bash
llf gui start --daemon --share --key "TeamLLM2024"
# Share URL and password with team members
```

**4. Quick temporary access:**
```bash
# Start (no daemon, so you see activity)
llf gui start --share --key "TempAccess"
# Use it
# Press Ctrl+C when done
```

### Comparison: GUI vs LLM Server Network Access

| Feature | GUI Network Access | LLM Server Network Access |
|---------|-------------------|---------------------------|
| **Command** | `llf gui start --share --key PASSWORD` | `llf server start --share` |
| **Port** | 7860 (default) | 8000 (default) |
| **Authentication** | Optional (`--key`) | None (anyone can access) |
| **Interface** | Web browser | API calls |
| **Use Case** | Visual interface | Programmatic access |
| **Security** | Can be secured with `--key` | No built-in auth |

**Recommendation:** Use GUI network access when you want a visual interface with authentication. Use LLM server network access for API clients or when authentication is handled elsewhere.

### Related Documentation

- [Basic User Guide](../Basic_User_Guide.md) - Getting started with LLM Framework
- [Setup Network Access - LLM Server](Setup_Network_Access_LLM.md) - Share the LLM server API
- [Setup External LLM](Setup_External_LLM.md) - Use ChatGPT, Claude, etc.
- [Troubleshooting](Troubleshooting.md) - Solutions to common problems

---

**Security Reminder:**

⚠️ **ALWAYS use `--key` when using `--share`**

Without authentication, anyone on your network has full access to:
- Your LLM and all its capabilities
- Server controls (start/stop)
- Model downloads (using your bandwidth)
- Configuration files
- Memory and data stores

**Protect your LLM Framework with strong authentication!**

---

Happy (and secure) GUI sharing on your local network!
