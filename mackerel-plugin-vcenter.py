#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import sys
import argparse
import time
import json
import atexit
from math import floor, log

# PyVmomi
from pyVim.connect import SmartConnect, Disconnect
import ssl
ssl._create_default_https_context = ssl._create_unverified_context


def convertMemory(sizeBytes):
    """
    ホストのメモリ(byte)をGBに変換する
    """
    base = int(floor(log(sizeBytes, 1024)))
    power = pow(1024, base)
    size = round(sizeBytes/power, 2)
    return "{}".format(floor(size))


def vcenter_resources(ipaddress, user, password):
    """
    vCenter に接続して Cluster 毎のCPU/MEM、起動しているVMのCPU/MEMを集計して返す
    """
    return_dict = {}    # 関数から返すリスト

    si = SmartConnect(host=ipaddress, user=user, pwd=password)
    atexit.register(Disconnect, si)
    content = si.RetrieveContent()

    root_folder = content.rootFolder

    # データセンタ
    for datacenter in root_folder.childEntity:
        for cluster in datacenter.hostFolder.childEntity:
            return_dict.setdefault('vcenter', {})
            return_dict['vcenter'].setdefault(cluster.name, {})

            # ホスト
            hosts_cpu = 0
            hosts_mem = 0
            guests_cpu = 0
            guests_mem = 0
            for host in cluster.host:
                hosts_cpu += host.hardware.cpuInfo.numCpuThreads
                hosts_mem += int(float(convertMemory(host.hardware.memorySize)))

                # 起動しているVMだけを対象にする
                for vm in host.vm:
                    if vm.summary.runtime.powerState == 'poweredOn':
                        guests_cpu += vm.summary.config.numCpu
                        guests_mem += int(float(vm.summary.config.memorySizeMB // 1024))

            return_dict['vcenter'].setdefault(cluster.name, {})
            return_dict['vcenter'][cluster.name]['hosts_cpu'] = hosts_cpu
            return_dict['vcenter'][cluster.name]['hosts_mem'] = hosts_mem
            return_dict['vcenter'][cluster.name]['guests_cpu'] = guests_cpu
            return_dict['vcenter'][cluster.name]['guests_mem'] = guests_mem

    return return_dict


def graph_definition(resource_dict):
    """
    Mackerel カスタムグラフの定義
    """
    print('# mackerel-agent-plugin')

    graphdef = {}
    graphdef.setdefault('graphs', {})

    for cluster_name in resource_dict['vcenter']:
        graphdef['graphs'].setdefault(cluster_name, {})
        graphdef['graphs'][cluster_name]['label'] = 'Cluster ' + cluster_name + ' resource usage'
        graphdef['graphs'][cluster_name]['unit'] = 'integer'
        graphdef['graphs'][cluster_name].setdefault('metrics', [])
        graphdef['graphs'][cluster_name]['metrics'].append({'name': '*', 'label': '%1'})

    print(json.dumps(graphdef))


def metrics_output(resource_dict):
    """
    メトリクスの値を出力する
    """
    timestamp = int(time.time())

    for cluster_name in resource_dict['vcenter']:
        hosts_cpu = resource_dict['vcenter'][cluster_name]['hosts_cpu']
        hosts_mem = resource_dict['vcenter'][cluster_name]['hosts_mem']
        guests_cpu = resource_dict['vcenter'][cluster_name]['guests_cpu']
        guests_mem = resource_dict['vcenter'][cluster_name]['guests_mem']

        print(cluster_name + '.CPU', hosts_cpu, timestamp, sep='\t')
        print(cluster_name + '.Memory', hosts_mem, timestamp, sep='\t')
        print(cluster_name + '.GuestsCPU', guests_cpu, timestamp, sep='\t')
        print(cluster_name + '.GuestsMEM', guests_mem, timestamp, sep='\t')


def main():
    """
    メイン
    """

    # 引数の処理
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--host',
                        help='vCenter ip address', action='store',
                        required=True)
    parser.add_argument('-u', '--user',
                        help='vCenter login account', action='store',
                        required=True)
    parser.add_argument('-p', '--password',
                        help='vCenter login password', action='store',
                        required=True)
    args = parser.parse_args()

    # vCenter にアクセスして情報を取得
    resource_dict = vcenter_resources(args.host, args.user, args.password)

    # グラフ定義の生成と送信
    if os.environ.get('MACKEREL_AGENT_PLUGIN_META') == '1':
        graph_definition(resource_dict)
        sys.exit(0)

    # メトリクスの出力
    metrics_output(resource_dict)


if __name__ == '__main__':
    main()
