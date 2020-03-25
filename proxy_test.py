import requests
from time import sleep

ip_api = 'xxx'

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10)'
                  ' Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10'
}

url = 'https://buff.163.com/'

resp = requests.get(url, headers=headers)

print("不使用代理，响应：", resp)

for i in range(5):
    ip_resp = requests.get(ip_api)
    ip = ip_resp.json().get('data')

    if ip:
        ip = ip[0]
        print(ip, end=' ')
        try:
            resp = requests.get(url, headers=headers,
                                proxies={'https': ' https://{}'.format(ip),
                                         'http': 'http://{}'.format(ip)}, timeout=10)
        except:
            resp = 'Request_Error'
        print(resp)
    else:
        print('获取IP失败', ip_resp.text)

    sleep(2)