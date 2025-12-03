````````

sudo cloudflared service install eyJhIjoiNDVlMzNlNDRkOGZhZjMyNmJiNzE3MTRjOGI0OGE2OWYiLCJ0IjoiYjUwYTc0MjQtNjFkMC00YWRmLWE1M2YtNjkxMzA0Yzg2YTYxIiwicyI6Ik9HWmxNVGN3TWpBdE5HSTVNaTAwT0RFMUxXSXlObVl0TVRreFlXSmxObUZoTlRFNSJ9
```````````
```````````
cloudflared tunnel run --token eyJhIjoiNDVlMzNlNDRkOGZhZjMyNmJiNzE3MTRjOGI0OGE2OWYiLCJ0IjoiYjUwYTc0MjQtNjFkMC00YWRmLWE1M2YtNjkxMzA0Yzg2YTYxIiwicyI6Ik9HWmxNVGN3TWpBdE5HSTVNaTAwT0RFMUxXSXlObVl0TVRreFlXSmxObUZoTlRFNSJ9

```````````````
cloudflared tunnel route dns printer printer123.trycloudflare.com
```````````````
tunnel: 5cd0f9a5-3d30-42d7-8ead-bbfa7afe1e61
credentials-file: /home/sidharth/.cloudflared/5cd0f9a5-3d30-42d7-8ead-bbfa7afe1e61.json

ingress:
  - hostname: printer123.trycloudflare.com
    service: http://localhost:5001
  - service: http_status:404

`````````````