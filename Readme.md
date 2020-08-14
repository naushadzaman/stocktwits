# Queries 
## Trending Stocks 
curl -X GET https://api.stocktwits.com/api/2/trending/symbols.json
curl -X GET https://api.stocktwits.com/api/2/trending/symbols.json?access_token=<access_token>

works without access token too. 

## Details for a stock
curl -X GET https://api.stocktwits.com/api/2/streams/symbol/AAPL.json

# Pushshift API 
http://twitter-48943539.pushshift.io/search?contains_symbol=true&size=10
http://twitter-48943539.pushshift.io/search?symbol=SRNE

# API 

https://api.stocktwits.com/developers/docs/api
```
cURL [ about cURL ]
// Token example
curl -X GET -u naushadzaman -p https://api.stocktwits.com/api/2/oauth/authorize -d 'client_id=ec5c616cd0d59066&response_type=token&redirect_uri=http://blackbird.ai&scope=read,watch_lists,publish_messages,publish_watch_lists,follow_users,follow_stocks'


curl -X GET -u naushadzaman -p https://api.stocktwits.com/api/2/oauth/authorize -d 'client_id=c84366e84ffa98b1&response_type=token&redirect_uri=stocktwits.com&scope=read,watch_lists,publish_messages,publish_watch_lists,follow_users,follow_stocks'

curl -X GET -u naushadzaman -p https://api.stocktwits.com/api/2/oauth/authorize -d 'client_id=47b7a38d80a93a44&response_type=token&redirect_uri=https://stocktwits.com&scope=read,watch_lists,publish_messages,publish_watch_lists,follow_users,follow_stocks'
```
Output: 
```
<html><body>You are being <a href="https://api.stocktwits.com/api/2/oauth/signin?client_id=ec5c616cd0d59066&amp;redirect_uri=http%3A%2F%2Fblackbird.ai&amp;response_type=token&amp;scope=read%2Cwatch_lists%2Cpublish_messages%2Cpublish_watch_lists%2Cfollow_users%2Cfollow_stocks">redirected</a>.</body></html>
```

```
// Code example
curl -X GET https://api.stocktwits.com/api/2/oauth/authorize -d 'client_id=ec5c616cd0d59066&response_type=code&redirect_uri=http://blackbird.ai&scope=read,watch_lists,publish_messages,publish_watch_lists,follow_users,follow_stocks'

```
Output
```
<html><body>You are being <a href="https://api.stocktwits.com/api/2/oauth/signin?client_id=ec5c616cd0d59066&amp;redirect_uri=http%3A%2F%2Fblackbird.ai&amp;response_type=code&amp;scope=read%2Cwatch_lists%2Cpublish_messages%2Cpublish_watch_lists%2Cfollow_users%2Cfollow_stocks">redirected</a>.</body></html>
```


# APPS
```
Site domain: blackbird.ai
Consumer key: ec5c616cd0d59066
Consumer secret: b8099130ff19bcd915eb68ec83a34e65c572e50e
#access_token=3d28ce2f84763ce8355fa5c73522947d75f6e894
```
```
Site domain: stocktwits.com
Consumer key: c84366e84ffa98b1
Consumer secret: 344957ba914116034495d0ebc48ed16178343fb3
#access_token=23208869136d4a135d7ae3f12babfc84afbf8df1
```
```
Site domain: stocktwits.com
Consumer key: 47b7a38d80a93a44
Consumer secret: 7b62570b8868273fc4952b0deda6fc8305d7128b
#access_token=db6053d8a0af4161a2bbf88b34bf984e4ff3f758
```


