#!/usr/bin/env python3
"""
Clash 订阅转换工具
支持: Base64编解码 / URL解析 / 节点过滤 / 格式转换
"""

import base64
import json
import re
import sys
import argparse
from urllib.parse import urlparse, parse_qs

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class SubConverter:
    """订阅转换处理类"""

    def __init__(self):
        self.proxies = []

    def parse_sub_url(self, url: str) -> list:
        """解析订阅URL，返回节点列表"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        try:
            parsed = urlparse(url)
            raw_content = parsed.query or parsed.fragment

            if not raw_content:
                import urllib.request
                req = urllib.request.Request(url, headers={'User-Agent': 'ClashForAndroid/2.5.12'})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    raw_content = resp.read().decode('utf-8')
        except Exception as e:
            print(f"获取订阅失败: {e}", file=sys.stderr)
            return []

        return self.parse_content(raw_content)

    def parse_content(self, content: str) -> list:
        """解析订阅内容"""
        content = content.strip()

        # Base64 解码
        try:
            decoded = base64.b64decode(content + '==').decode('utf-8')
            if decoded.startswith('ss://') or decoded.startswith('vmess://') or                decoded.startswith('trojan://') or decoded.startswith('vless://'):
                content = decoded
        except Exception:
            pass

        lines = []
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                lines.append(line)

        self.proxies = []
        for line in lines:
            try:
                if line.startswith('ss://'):
                    node = self.parse_ss(line)
                elif line.startswith('vmess://'):
                    node = self.parse_vmess(line)
                elif line.startswith('trojan://'):
                    node = self.parse_trojan(line)
                elif line.startswith('vless://'):
                    node = self.parse_vless(line)
                else:
                    continue
                if node:
                    self.proxies.append(node)
            except Exception:
                continue

        return self.proxies

    def parse_ss(self, line: str) -> dict:
        """解析 Shadowsocks 链接"""
        match = re.match(r'ss://([A-Za-z0-9+/=]+)@([^:]+):(\d+)(?:#(.+))?', line)
        if not match:
            return None
        userinfo, server, port, name = match.groups()
        try:
            method, password = base64.b64decode(userinfo + '==').decode('utf-8').split(':', 1)
        except Exception:
            return None
        return {
            'name': name or f"SS-{server}",
            'type': 'ss',
            'server': server,
            'port': int(port),
            'cipher': method,
            'password': password
        }

    def parse_vmess(self, line: str) -> dict:
        """解析 VMess 链接"""
        try:
            json_str = base64.b64decode(line[8:] + '==').decode('utf-8')
            obj = json.loads(json_str)
            return {
                'name': obj.get('ps', 'VMess'),
                'type': 'vmess',
                'server': obj.get('add'),
                'port': int(obj.get('port', 443)),
                'uuid': obj.get('id'),
                'alterId': int(obj.get('aid', 0)),
                'cipher': 'auto',
                'network': obj.get('net', 'tcp'),
                'ws-opts': {'path': obj.get('path', '/')} if obj.get('net') == 'ws' else None
            }
        except Exception:
            return None

    def parse_trojan(self, line: str) -> dict:
        """解析 Trojan 链接"""
        line = line.replace('trojan://', 'https://', 1)
        try:
            parsed = urlparse(line)
            return {
                'name': parsed.fragment or f"Trojan-{parsed.hostname}",
                'type': 'trojan',
                'server': parsed.hostname,
                'port': parsed.port or 443,
                'password': parsed.username,
                'sni': parsed.hostname
            }
        except Exception:
            return None

    def parse_vless(self, line: str) -> dict:
        """解析 VLESS 链接"""
        try:
            line = line.replace('vless://', 'https://', 1)
            parsed = urlparse(line)
            return {
                'name': parsed.fragment or f"VLESS-{parsed.hostname}",
                'type': 'vless',
                'server': parsed.hostname,
                'port': parsed.port or 443,
                'uuid': parsed.username,
                'tls': 'tls'
            }
        except Exception:
            return None

    def filter_proxies(self, keywords: list) -> list:
        """按关键词过滤节点"""
        if not keywords:
            return self.proxies
        filtered = []
        for p in self.proxies:
            for kw in keywords:
                if kw.lower() in p.get('name', '').lower():
                    filtered.append(p)
                    break
        return filtered

    def generate_clash_config(self, proxies: list = None) -> str:
        """生成 Clash YAML 配置"""
        if proxies is None:
            proxies = self.proxies

        config = {
            'port': 7890,
            'socks-port': 7891,
            'allow-lan': False,
            'mode': 'rule',
            'log-level': 'info',
            'external-controller': '0.0.0.0:9090',
            'dns': {
                'enable': True,
                'enhanced-mode': 'fake-ip',
                'nameserver': ['8.8.8.8', '1.1.1.1']
            },
            'proxies': proxies,
            'proxy-groups': [
                {
                    'name': 'PROXY',
                    'type': 'select',
                    'proxies': [p['name'] for p in proxies]
                },
                {
                    'name': 'Ads',
                    'type': 'select',
                    'proxies': ['REJECT']
                },
                {
                    'name': 'Domestic',
                    'type': 'select',
                    'proxies': ['DIRECT'] + [p['name'] for p in proxies]
                }
            ],
            'rules': [
                'DOMAIN-SUFFIX,doubleclick.net,Ads',
                'DOMAIN-SUFFIX,googlesyndication.com,Ads',
                'DOMAIN-KEYWORD,advertising,Ads',
                'DOMAIN-SUFFIX,cn,Domestic',
                'DOMAIN-SUFFIX,baidu.com,Domestic',
                'DOMAIN-SUFFIX,taobao.com,Domestic',
                'GEOIP,CN,Domestic',
                'MATCH,PROXY'
            ]
        }

        if HAS_YAML:
            return yaml.dump(config, allow_unicode=True, sort_keys=False, default_flow_style=False)
        else:
            return json.dumps(config, indent=2, ensure_ascii=False)

    def to_base64(self, content: str) -> str:
        """内容转Base64"""
        return base64.b64encode(content.encode('utf-8')).decode('ascii')


def main():
    parser = argparse.ArgumentParser(description='Clash 订阅转换工具')
    parser.add_argument('--url', help='订阅URL')
    parser.add_argument('--decode', help='Base64解码')
    parser.add_argument('--filter', action='append', help='节点过滤关键词')
    parser.add_argument('--output', choices=['json', 'yaml', 'mihomo', 'base64'], default='yaml', help='输出格式')
    args = parser.parse_args()

    converter = SubConverter()

    if args.decode:
        try:
            content = base64.b64decode(args.decode + '==').decode('utf-8')
            print(content)
            return
        except Exception as e:
            print(f"解码失败: {e}", file=sys.stderr)
            return

    if args.url:
        proxies = converter.parse_sub_url(args.url)
        print(f"[+] 解析到 {len(proxies)} 个节点")
        if args.filter:
            proxies = converter.filter_proxies(args.filter)
            print(f"[+] 过滤后剩余 {len(proxies)} 个节点")
        print(converter.generate_clash_config(proxies))
        return

    print("用法: sub-convert.py --url <订阅URL> [--filter 香港] [--output yaml]")


if __name__ == '__main__':
    main()
