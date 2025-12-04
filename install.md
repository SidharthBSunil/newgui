`````
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloudflare-main.gpg
echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared $(. /etc/os-release && echo $VERSION_CODENAME) main" | sudo tee /etc/apt/sources.list.d/cloudflared.list
`````







`````````
# Add cloudflare gpg key
sudo mkdir -p --mode=0755 /usr/share/keyrings
curl -fsSL https://pkg.cloudflare.com/cloudflare-public-v2.gpg | sudo tee /usr/share/keyrings/cloudflare-public-v2.gpg >/dev/null

# Add this repo to your apt repositories
echo 'deb [signed-by=/usr/share/keyrings/cloudflare-public-v2.gpg] https://pkg.cloudflare.com/cloudflared any main' | sudo tee /etc/apt/sources.list.d/cloudflared.list

# install cloudflared
sudo apt-get update && sudo apt-get install cloudflared

````````

sudo cloudflared service install eyJhIjoiNDVlMzNlNDRkOGZhZjMyNmJiNzE3MTRjOGI0OGE2OWYiLCJ0IjoiZTM0Yzc0MDgtMTIxOS00ZDc2LThlMjAtOTA5MzYwNGE4YzkxIiwicyI6Ik9EQTFaalUxWVRndE1HRm1aaTAwWldVM0xXSm1OREF0TUdRMk1qazVaRFJqWVRjNSJ9
````````
```````
cloudflared tunnel run --token eyJhIjoiNDVlMzNlNDRkOGZhZjMyNmJiNzE3MTRjOGI0OGE2OWYiLCJ0IjoiZTM0Yzc0MDgtMTIxOS00ZDc2LThlMjAtOTA5MzYwNGE4YzkxIiwicyI6Ik9EQTFaalUxWVRndE1HRm1aaTAwWldVM0xXSm1OREF0TUdRMk1qazVaRFJqWVRjNSJ9
```````
