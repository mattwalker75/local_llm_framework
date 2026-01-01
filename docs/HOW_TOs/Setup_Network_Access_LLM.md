# Setup Network Access: Local LLM Server

> **Share Your LLM on Your Local Network**
> Enable other devices on your network to access your locally running LLM server.

---

## Table of Contents

1. [What is Network Access?](#what-is-network-access)
2. [Security Considerations](#security-considerations)
3. [Temporary Network Access](#temporary-network-access)
4. [Permanent Network Access](#permanent-network-access)
5. [Finding Your Server Address](#finding-your-server-address)
6. [Accessing from Other Devices](#accessing-from-other-devices)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## What is Network Access?

By default, the LLM server only accepts connections from your local computer (`127.0.0.1` or `localhost`). **Network access** allows other devices on your local network to connect to your LLM server.

### Default vs Network Access

| Aspect | Localhost Only (Default) | Network Access |
|--------|-------------------------|----------------|
| **Binding** | 127.0.0.1 | 0.0.0.0 |
| **Access** | Only your computer | Any device on network |
| **Security** | Secure (isolated) | Less secure (exposed) |
| **Use Case** | Personal use | Share with team/devices |
| **Setup** | Automatic | Requires configuration |

### Use Cases

**When to enable network access:**
- Share your LLM with family members
- Access from your phone/tablet
- Team collaboration in same office
- Test LLM from different devices
- Development/testing scenarios

**When to keep it localhost:**
- Personal use only
- Security is critical
- Don't want to share resources
- Default secure configuration

---

## Security Considerations

⚠️ **IMPORTANT SECURITY WARNING** ⚠️

Enabling network access has security implications:

### Risks

1. **No Authentication**: The LLM server has NO built-in authentication
2. **Anyone Can Access**: Any device on your network can query your LLM
3. **Resource Usage**: Others can consume your computer's resources
4. **Privacy**: Others can see what queries are being made
5. **No Rate Limiting**: No protection against abuse

### Security Best Practices

✅ **DO:**
- Only enable on trusted networks (home, office)
- Use temporary access when possible
- Turn off when not needed
- Monitor who's using it
- Use strong WiFi password
- Consider firewall rules

❌ **DON'T:**
- Enable on public WiFi
- Leave it running unattended
- Share on untrusted networks
- Expose to the internet
- Ignore resource usage

### Recommended Approach

**For temporary sharing:** Use `--share` flag (easy to start/stop)
**For permanent sharing:** Only if you fully trust your network

---

## Temporary Network Access

The **recommended** way to share your LLM is using temporary network access. This lets you start the server with network access and easily stop it when done.

### How Temporary Access Works

- Use `--share` flag when starting the server
- Server binds to `0.0.0.0` (accessible on network)
- Stop the server when done
- Next time you start, it's localhost again (secure)

### Step 1: Start Server with Network Access

**Single Server:**
```bash
# Start in foreground (terminal stays active)
llf server start --share

# Start in background (daemon mode) - RECOMMENDED
llf server start --share --daemon
```

**Multi-Server:**
```bash
# Start specific server with network access
llf server start my-server-name --share

# Start in background
llf server start my-server-name --share --daemon
```

**What happens:**
- Server starts on `0.0.0.0` (all network interfaces)
- Accessible from any device on your local network
- Your terminal shows the server is running

### Step 2: Verify Server is Running

```bash
# Check server status
llf server status

# For multi-server
llf server status my-server-name
```

**Expected output:**
```
Server is running at http://0.0.0.0:8000
Accessible on network at http://YOUR-IP:8000
Model: Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
```

### Step 3: Find Your IP Address

See [Finding Your Server Address](#finding-your-server-address) section below.

### Step 4: Use from Other Devices

Other devices can now access your LLM at:
```
http://YOUR-IP-ADDRESS:8000/v1
```

See [Accessing from Other Devices](#accessing-from-other-devices) for details.

### Step 5: Stop Network Access When Done

**IMPORTANT:** Always stop the server when you're done sharing:

```bash
# Stop the server
llf server stop

# For multi-server
llf server stop my-server-name
```

**Verify it's stopped:**
```bash
llf server status
```

Expected output: `Server is not running`

### Restart with Network Access

If you need to restart the server with network access:

```bash
# Restart with network access
llf server restart --share

# Restart in background
llf server restart --share --daemon

# For multi-server
llf server restart my-server-name --share
```

### Example Workflow

```bash
# Morning: Share LLM with team
llf server start --share --daemon

# Team uses it throughout the day
# Access from various devices

# Evening: Stop sharing
llf server stop

# Next day: Back to localhost-only for personal use
llf server start --daemon
```

---

## Permanent Network Access

⚠️ **NOT RECOMMENDED** - Use temporary access instead

Permanent network access makes your LLM server always accessible on the network whenever it starts.

### Why This is Discouraged

1. **Always Exposed**: Every time you start the server, it's network-accessible
2. **Easy to Forget**: You might forget it's exposed
3. **No Authentication**: Anyone on network can use it
4. **Resource Drain**: Others can use your computer without you knowing
5. **Security Risk**: Higher risk than temporary access

### When to Use Permanent Access

Only consider this if:
- You have a dedicated server machine
- You want to always share the LLM
- You fully trust everyone on your network
- You actively monitor usage
- You understand the security risks

### Step 1: Backup Your Configuration

Before making changes:

```bash
cp configs/config.json configs/config.json.backup
```

### Step 2: Edit Configuration File

Open `configs/config.json` and change `server_host`:

**Single Server Configuration:**

```json
{
  "local_llm_server": {
    "llama_server_path": "/path/to/llama-server",
    "server_host": "0.0.0.0",  ← Change from 127.0.0.1 to 0.0.0.0
    "server_port": 8000,
    "model_dir": "YourModel-GGUF",
    "gguf_file": "model.gguf"
  },
  "llm_endpoint": {
    "api_base_url": "http://0.0.0.0:8000/v1",  ← Also update this
    "api_key": "EMPTY",
    "model_name": "Your/Model"
  }
}
```

**Multi-Server Configuration:**

```json
{
  "local_llm_servers": [
    {
      "name": "qwen-coder",
      "llama_server_path": "/path/to/llama-server",
      "server_host": "0.0.0.0",  ← Change from 127.0.0.1 to 0.0.0.0
      "server_port": 8000,
      "model_dir": "YourModel-GGUF",
      "gguf_file": "model.gguf"
    },
    {
      "name": "another-server",
      "llama_server_path": "/path/to/llama-server",
      "server_host": "0.0.0.0",  ← Change for each server you want to share
      "server_port": 8001,
      "model_dir": "AnotherModel-GGUF",
      "gguf_file": "model.gguf"
    }
  ],
  "llm_endpoint": {
    "api_base_url": "http://0.0.0.0:8000/v1",  ← Update this too
    "default_local_server": "qwen-coder"
  }
}
```

### Step 3: Start the Server Normally

Now when you start the server normally, it will be network-accessible:

```bash
# Single server
llf server start --daemon

# Multi-server
llf server start qwen-coder --daemon
```

**No need for `--share` flag** - it's always shared now.

### Step 4: Revert to Localhost Only

To go back to localhost-only access:

```bash
# Restore your backup
cp configs/config.json.backup configs/config.json

# Or manually edit config.json
# Change "server_host": "0.0.0.0" back to "127.0.0.1"
# Change "api_base_url": "http://0.0.0.0:8000/v1" back to "http://127.0.0.1:8000/v1"

# Restart the server
llf server restart
```

---

## Finding Your Server Address

To access your LLM from other devices, you need your computer's IP address.

### Find Your IP Address

**macOS:**
```bash
# Method 1: System Preferences
# Go to System Settings > Network > Your Connection > Details

# Method 2: Terminal
ipconfig getifaddr en0  # For WiFi
ipconfig getifaddr en1  # For Ethernet
```

**Linux:**
```bash
# Method 1: ip command
ip addr show | grep inet

# Method 2: hostname command
hostname -I | awk '{print $1}'

# Method 3: ifconfig
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**Windows:**
```bash
# Command Prompt
ipconfig

# Look for "IPv4 Address" under your network adapter
```

### Typical IP Addresses

Your local IP will usually look like:
- `192.168.1.x` (most common)
- `192.168.0.x`
- `10.0.0.x`
- `172.16.x.x` to `172.31.x.x`

Example: `192.168.1.100`

### Verify Server is Accessible

From your computer, test the server:

```bash
# Test the endpoint
curl http://YOUR-IP-ADDRESS:8000/v1/models

# Example
curl http://192.168.1.100:8000/v1/models
```

If you get a response, the server is working!

---

## Accessing from Other Devices

Once network access is enabled, other devices can use your LLM.

### Connection Information

Provide this information to others:

```
Server URL: http://YOUR-IP-ADDRESS:PORT/v1
API Key: EMPTY
Model: (your model name)
```

**Example:**
```
Server URL: http://192.168.1.100:8000/v1
API Key: EMPTY
Model: Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
```

### From Another Computer

**Using LLM Framework on another computer:**

Edit their `configs/config.json`:

```json
{
  "llm_endpoint": {
    "api_base_url": "http://192.168.1.100:8000/v1",
    "api_key": "EMPTY",
    "model_name": "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
  }
}
```

Then they can use:
```bash
llf chat
```

**Using curl:**
```bash
curl http://192.168.1.100:8000/v1/models
```

### From Phone/Tablet

Use an OpenAI-compatible mobile app:

1. Install an app that supports OpenAI API (ChatGPT apps, etc.)
2. Configure custom endpoint:
   - Base URL: `http://192.168.1.100:8000/v1`
   - API Key: `EMPTY` or leave blank
   - Model: Your model name
3. Start chatting!

### From Python Script

```python
import openai

client = openai.OpenAI(
    base_url="http://192.168.1.100:8000/v1",
    api_key="EMPTY"
)

response = client.chat.completions.create(
    model="Qwen/Qwen2.5-Coder-7B-Instruct-GGUF",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

### From Web Browser

Some tools have web interfaces that can connect to your server:
- Open WebUI
- ChatGPT-like interfaces
- Custom web apps

Configure them to use:
```
http://192.168.1.100:8000/v1
```

---

## Troubleshooting

### Problem: "Connection Refused"

**From other devices:**

**Possible causes:**
1. Server not started with `--share`
2. Firewall blocking connections
3. Wrong IP address
4. Server not running

**Solutions:**

1. **Verify server is running with network access:**
   ```bash
   llf server status
   # Should show 0.0.0.0, not 127.0.0.1
   ```

2. **Check firewall (macOS):**
   ```bash
   # Allow incoming connections
   # Go to System Settings > Network > Firewall
   # Allow llama-server or Python
   ```

3. **Check firewall (Linux):**
   ```bash
   # Allow port 8000
   sudo ufw allow 8000

   # Or disable firewall temporarily for testing
   sudo ufw disable  # Re-enable after: sudo ufw enable
   ```

4. **Check firewall (Windows):**
   - Go to Windows Defender Firewall
   - Allow app through firewall
   - Add llama-server or Python

5. **Verify correct IP:**
   ```bash
   # Make sure you're using the right IP
   ipconfig getifaddr en0  # macOS
   hostname -I  # Linux
   ipconfig  # Windows
   ```

### Problem: "Timeout" or Very Slow

**Possible causes:**
1. Network congestion
2. WiFi signal weak
3. Server overloaded
4. Model too large for hardware

**Solutions:**

1. **Check network connection:**
   ```bash
   # From other device, ping your server
   ping 192.168.1.100
   ```

2. **Use faster WiFi or wired connection**

3. **Check server resources:**
   ```bash
   # On server machine
   top  # Check CPU/RAM usage
   ```

4. **Use a smaller model** if hardware is struggling

### Problem: "Cannot Find Server"

**Solutions:**

1. **Verify devices are on same network:**
   - Both on same WiFi network
   - Not using VPN that isolates traffic

2. **Check subnet:**
   ```bash
   # Your IPs should be similar
   # Server: 192.168.1.100
   # Client: 192.168.1.50  ✓ Same subnet
   # Client: 192.168.2.50  ✗ Different subnet
   ```

3. **Try using server's hostname:**
   ```bash
   # Instead of IP, use hostname
   http://your-computer-name.local:8000/v1
   ```

### Problem: "Port Already in Use"

**Error:**
```
Error: Address already in use (port 8000)
```

**Solutions:**

1. **Stop existing server:**
   ```bash
   llf server stop
   ```

2. **Find and kill process:**
   ```bash
   # Find process using port
   lsof -i :8000  # macOS/Linux

   # Kill it
   kill -9 PID
   ```

3. **Use different port:**
   - Edit `server_port` in config.json
   - Use a different port like 8001, 8080, etc.

### Problem: "Works from Computer, Not from Network"

This usually means:
- Server started with `127.0.0.1` instead of `0.0.0.0`
- Need to use `--share` flag
- Or update config.json `server_host` to `0.0.0.0`

**Solution:**
```bash
# Make sure to use --share
llf server stop
llf server start --share --daemon
```

---

## Best Practices

### Security

1. **Use Temporary Access**
   - Prefer `--share` flag over permanent configuration
   - Only share when needed
   - Stop when done

2. **Trusted Networks Only**
   - Only enable on home/office networks
   - Never on public WiFi
   - Not on untrusted networks

3. **Monitor Usage**
   - Check who's connecting
   - Monitor resource usage
   - Watch for unusual activity

4. **Firewall Protection**
   - Keep firewall enabled
   - Only allow specific ports
   - Consider IP restrictions

### Performance

1. **Network Quality**
   - Use wired connection for server if possible
   - Strong WiFi signal for clients
   - Avoid network congestion

2. **Resource Management**
   - Monitor CPU/RAM usage
   - Limit concurrent connections
   - Use appropriate model size

3. **Bandwidth**
   - Larger responses use more bandwidth
   - Consider response size limits
   - Monitor network traffic

### Convenience

1. **Static IP** (Optional)
   - Configure server with static IP
   - Easier to remember and share
   - No need to find IP each time

2. **Hostname** (Optional)
   - Use hostname instead of IP
   - Example: `http://my-server.local:8000/v1`
   - Easier for users

3. **Documentation**
   - Document your server URL
   - Share instructions with users
   - Keep config backed up

### Backup and Recovery

1. **Backup Configs**
   ```bash
   cp configs/config.json configs/config.network.backup
   cp configs/config.json configs/config.localhost.backup
   ```

2. **Easy Switching**
   ```bash
   # Switch to network config
   cp configs/config.network.backup configs/config.json
   llf server restart

   # Switch to localhost config
   cp configs/config.localhost.backup configs/config.json
   llf server restart
   ```

---

## Summary

You now know how to enable network access for your local LLM server:

**Key Takeaways:**

1. **Two Methods:**
   - **Temporary (Recommended)**: Use `--share` flag
   - **Permanent (Discouraged)**: Edit config.json

2. **Temporary Access:**
   ```bash
   llf server start --share --daemon  # Start with network access
   llf server stop                    # Stop when done
   ```

3. **Permanent Access:**
   - Change `server_host` to `0.0.0.0` in config.json
   - NOT RECOMMENDED due to security risks

4. **Security:**
   - No built-in authentication
   - Only use on trusted networks
   - Stop when not needed
   - Monitor usage

5. **Access from Other Devices:**
   - Find your IP address
   - Use `http://YOUR-IP:8000/v1`
   - Configure OpenAI-compatible apps

**Quick Reference:**

```bash
# Temporary network access (RECOMMENDED)
llf server start --share --daemon
llf server stop

# Find your IP
ipconfig getifaddr en0  # macOS WiFi
hostname -I             # Linux
ipconfig                # Windows

# Test from another device
curl http://YOUR-IP:8000/v1/models

# Connection info for others
Server URL: http://YOUR-IP:8000/v1
API Key: EMPTY
```

**Security Reminder:**
⚠️ Network access has NO authentication. Only enable on trusted networks!

**For More Help:**
- [Basic User Guide](../Basic_User_Guide.md)
- [Setup External LLM](Setup_External_LLM.md)
- [Setup Network Access - GUI](Setup_Network_Access_GUI.md)
- [Troubleshooting](Troubleshooting.md)

Happy sharing your LLM (securely)!