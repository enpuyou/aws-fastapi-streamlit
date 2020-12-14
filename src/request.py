import requests

response = requests.get("http://54.83.130.248/add?num_1=3&num_2=5")
data_dict = response.json()
print(data_dict)
