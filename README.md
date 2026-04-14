# 代理工具箱 0414

> Clash 规则订阅转换 · 广告过滤 · 代理规则集

## 工具列表

| 文件 | 功能 |
|------|------|
| `sub-convert.py` | 订阅地址转换（Base64编解码/URL编解码/节点过滤） |
| `rules.yaml` | Clash 规则集（分流国内外流量，自动选择最优节点） |
| `adblock.txt` | 广告+追踪器域名黑名单 |
| `direct.txt` | 国内直连域名列表 |

## sub-convert.py 功能

```bash
# 转换订阅地址
python3 sub-convert.py --url "https://your-sub-url"

# Base64 解码
python3 sub-convert.py --decode "aHR0..."

# 节点过滤（筛选特定国家/协议）
python3 sub-convert.py --url "https://..." --filter "香港" --filter "日本"

# 导出为 mihomo 配置
python3 sub-convert.py --url "https://..." --output mihomo.yaml
```

## rules.yaml 规则说明

- 国内网站直连（DIRECT）
- 国际网站走代理（PROXY）
- 广告+追踪器屏蔽（REJECT）
- Netflix/Disney+/YouTube 等流媒体使用对应节点组

## adblock.txt 使用

在 Clash 的 `rule-providers` 中引用：
```yaml
rule-providers:
  ads:
    type: http
    behavior: domain
    url: "https://raw.githubusercontent.com/clashhub-net/airport-rec-xxx/main/adblock.txt"
    path: ./rules/ads.yaml
    interval: 86400
```

## 适用客户端

- mihomo / Clash.Meta
- Clash Verge / Clash for Windows
- Stash / Shadowrocket

## 推荐

- [机场导航](https://nav.clashvip.net)
- [ClashHub 规则集](https://clashhub.net)
- [Clash教程](https://clash-for-windows.net)
- [社区论坛](https://bbs.clashhub.net)

---

> 由 [ClashHub](https://clashhub.net) 维护 · 每日自动更新
