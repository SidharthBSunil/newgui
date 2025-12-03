````````

/home/sidharth/.cloudflared/config.yml
```````````
```````````
tunnel: 5cd0f9a5-3d30-42d7-8ead-bbfa7afe1e61
credentials-file: /home/sidharth/.cloudflared/5cd0f9a5-3d30-42d7-8ead-bbfa7afe1e61.json

ingress:
  - hostname: printer123.trycloudflare.com
    service: http://localhost:5001
  - service: http_status:404

```````````````
cloudflared tunnel route dns printer printer123.trycloudflare.com
```````````````
cloudflared tunnel run printer

`````````````