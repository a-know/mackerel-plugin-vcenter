
mackerel-plugin-vcenter

Mackerel Plugin を自作したくて試しに作ったやつ

- vCenter にアクセスして下記の情報を取得してくる
  - クラスタの CPU数、メモリ (ホストのCPUスレッド数、メモリを集計)
  - 各ホストで稼働しているVMに割り当てている vCPU数、メモリを集計
  - 上記から計算した使用率
- グラフ定義(JSON) の生成を出力
- 上記 vCenter 情報の出力

で、使用率にアラート設定してアラートが飛ばせるところまでは試した。


```bash
[plugin.metrics.vcenter_resource]
command = "/usr/local/bin/mackerel-plugin-vcenter.py -s 127.0.0.1 -u username -p password"
```

```bash
# mackerel-plugin-vcenter.py -h
usage: mackerel-plugin-vcenter.py [-h] -s HOST -u USER -p PASSWORD

optional arguments:
  -h, --help            show this help message and exit
  -s HOST, --host HOST  vCenter ip address
  -u USER, --user USER  vCenter login account
  -p PASSWORD, --password PASSWORD
                        vCenter login password
```
