# -*- coding: utf-8 -*-
"""
飞书多维表格 URL 解析辅助工具

帮助用户从飞书多维表格 URL 中提取 app_token 和 table_id
"""

import re
from typing import Optional, Tuple


def parse_feishu_bitable_url(url: str) -> Optional[Tuple[str, str, str]]:
    """
    解析飞书多维表格 URL，提取 app_token 和 table_id

    支持的 URL 格式：
    1. https://xxx.feishu.cn/base/<APP_TOKEN>/~/<TABLE_ID>
    2. https://xxx.feishu.cn/base/<APP_TOKEN>/~/<TABLE_ID>?view=xxx
    3. https://xxx.feishu.cn/base/<APP_TOKEN> （只有 app_token）

    Args:
        url: 飞书多维表格 URL

    Returns:
        (app_token, table_id, full_token) 元组
        - app_token: 应用 token
        - table_id: 表格 ID
        - full_token: 完整的 token（app_token/table_id 格式）
        失败返回 None
    """
    # 移除 URL 中的参数
    if '?' in url:
        url = url.split('?')[0]

    # 移除末尾的斜杠
    url = url.rstrip('/')

    # 正则表达式匹配
    # 格式：https://xxx.feishu.cn/base/<APP_TOKEN>/~/<TABLE_ID>
    pattern = r'/base/([^/]+)/~/([^/]+)'

    match = re.search(pattern, url)
    if match:
        app_token = match.group(1)
        table_id = match.group(2)
        full_token = f"{app_token}/{table_id}"
        return app_token, table_id, full_token

    # 如果只找到 app_token
    pattern2 = r'/base/([^/]+)/?$'
    match2 = re.search(pattern2, url)
    if match2:
        app_token = match2.group(1)
        return app_token, None, app_token

    return None


def generate_env_config(
    app_token: str,
    table_id: Optional[str],
    app_id: str,
    app_secret: str
) -> str:
    """
    生成 .env 配置

    Args:
        app_token: 应用 token
        table_id: 表格 ID（可选）
        app_id: 飞书应用 ID
        app_secret: 飞书应用密钥

    Returns:
        .env 配置字符串
    """
    if table_id:
        table_token = f"{app_token}/{table_id}"
    else:
        table_token = app_token

    config = f"""
# 飞书多维表格配置
USE_FEISHU_BITABLE=true
FEISHU_TABLE_TOKEN={table_token}
FEISHU_APP_ID_BITABLE={app_id}
FEISHU_APP_SECRET_BITABLE={app_secret}
"""
    return config.strip()


if __name__ == "__main__":
    print("=" * 70)
    print("飞书多维表格 URL 解析工具")
    print("=" * 70)

    print("\n请按以下步骤操作：")
    print("\n1. 打开你的飞书多维表格")
    print("2. 复制浏览器地址栏中的完整 URL")
    print("3. 将 URL 粘贴到下面")

    print("\n" + "-" * 70)
    url = input("\n请输入飞书多维表格 URL: ").strip()

    if not url:
        print("\n[错误] URL 不能为空")
        exit(1)

    result = parse_feishu_bitable_url(url)

    if not result:
        print("\n[错误] 无法解析 URL，请检查 URL 格式")
        print("\n正确的 URL 格式应为:")
        print("  https://xxx.feishu.cn/base/<APP_TOKEN>/~/<TABLE_ID>")
        print("\n示例:")
        print("  https://xxx.feishu.cn/base/appljxxx/~/tblxxx")
        exit(1)

    app_token, table_id, full_token = result

    print("\n" + "=" * 70)
    print("解析结果")
    print("=" * 70)

    print(f"\nApp Token:  {app_token}")
    if table_id:
        print(f"Table ID:   {table_id}")
        print(f"\n完整 Token: {full_token}")
    else:
        print(f"\n注意: 只找到了 App Token，未找到 Table ID")
        print(f"完整 Token: {full_token}")
        print(f"\n请确保 URL 中包含 '/~/' 后面的表格 ID 部分")

    print("\n" + "-" * 70)
    print("\n请在 .env 文件中添加或修改以下配置：\n")

    print(f"# 启用飞书多维表格")
    print(f"USE_FEISHU_BITABLE=true")
    print(f"")
    print(f"# TABLE_TOKEN 格式: app_token/table_id")
    print(f"FEISHU_TABLE_TOKEN={full_token}")
    print(f"")
    print(f"# 飞书应用凭证（从飞书开放平台获取）")
    print(f"FEISHU_APP_ID_BITABLE=<你的_APP_ID>")
    print(f"FEISHU_APP_SECRET_BITABLE=<你的_APP_SECRET>")

    print("\n" + "=" * 70)
    print("\n配置说明：")
    print("\n1. 获取 APP_ID 和 APP_SECRET:")
    print("   - 访问飞书开放平台: https://open.feishu.cn/app")
    print("   - 创建自建应用或使用现有应用")
    print("   - 在权限管理中开启 bitable:app 权限")
    print("   - 复制 App ID 和 App Secret")

    print("\n2. 配置权限:")
    print("   - 确保应用有 bitable:app 权限")
    print("   - 将多维表格分享给应用")

    print("\n3. 测试配置:")
    print("   - 运行: python feishu_bitable.py")
    print("   - 查看是否能成功读取股票列表")

    print("\n" + "=" * 70)
