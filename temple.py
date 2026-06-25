import requests

url = "https://hindu-temples-api.p.rapidapi.com/"

querystring = {"limit":"10","page":"1"}

headers = {
	"x-rapidapi-key": "8c78e7e2e4mshbdb842cc77a2d89p1c45d4jsnde2e649e5f9d",
	"x-rapidapi-host": "hindu-temples-api.p.rapidapi.com",
	"Content-Type": "application/json"
}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())