# automatly.ai — Deployment Guide

## Local Run

```bash
pip install -r requirements.txt
python app.py
```

Visit: http://localhost:5000

---

## Ubuntu Server Deployment

### 1. Upload files to server

```bash
scp -r ./automatly ubuntu@YOUR_SERVER_IP:/home/ubuntu/automatly
```

### 2. SSH into server and install dependencies

```bash
ssh ubuntu@YOUR_SERVER_IP
cd /home/ubuntu/automatly
sudo apt update
sudo apt install python3-pip python3-venv nginx -y
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run with Gunicorn (test)

```bash
gunicorn --bind 0.0.0.0:5000 app:app
```

### 4. Create systemd service (runs on boot)

```bash
sudo nano /etc/systemd/system/automatly.service
```

Paste this:

```
[Unit]
Description=automatly.ai Flask App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/automatly
Environment="PATH=/home/ubuntu/automatly/venv/bin"
ExecStart=/home/ubuntu/automatly/venv/bin/gunicorn --workers 3 --bind unix:automatly.sock -m 007 app:app

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl start automatly
sudo systemctl enable automatly
```

### 5. Nginx reverse proxy config

```bash
sudo nano /etc/nginx/sites-available/automatly
```

Paste this:

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/automatly/automatly.sock;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/automatly /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

### 6. (Optional) HTTPS via Certbot

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com
```

---

Visit your server IP or domain in browser. Done.
