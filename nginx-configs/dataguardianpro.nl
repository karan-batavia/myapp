server {
    listen 80;
    listen [::]:80;
    server_name dataguardianpro.nl www.dataguardianpro.nl;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name dataguardianpro.nl www.dataguardianpro.nl;

    ssl_certificate /etc/letsencrypt/live/dataguardianpro.nl/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dataguardianpro.nl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    client_max_body_size 100M;

    location /webhook/ {
        proxy_pass http://webhook_server;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Stripe-Signature $http_stripe_signature;
        proxy_buffering off;
    }

    location / {
        proxy_pass http://dataguardian_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
