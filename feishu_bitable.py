# -*- coding: utf-8 -*-
"""
飞书多维表格 (Bitable) 数据读取模块

功能：
- 从飞书多维表格读取股票列表
- 支持自定义字段映射
- 自动错误处理和日志记录
- 使用 requests 直接调用飞书 API（无需 lark-oapi SDK）
"""

import logging
import requests
from typing import List, Optional, Dict, Any
from datetime import datetime
from config import get_config

logger = logging.getLogger(__name__)


class FeishuBitableReader:
    """
    飞书多维表格读取器（使用 HTTP API）

    不依赖 lark-oapi SDK，直接使用 requests 调用飞书开放 API
    """

    # 飞书 API 端点
    BASE_URL = "https://open.feishu.cn/open-apis"
    TOKEN_URL = f"{BASE_URL}/auth/v3/tenant_access_token/internal"
    TABLE_RECORDS_URL = f"{BASE_URL}/bitable/v1/apps/{{app_token}}/tables/{{table_id}}/records"

    def __init__(self):
        """
        初始化飞书多维表格读取器
        """
        self.config = get_config()
        self.app_id = self.config.feishu_app_id_bitable or self.config.feishu_app_id
        self.app_secret = self.config.feishu_app_secret_bitable or self.config.feishu_app_secret
        self.table_token = self.config.feishu_table_token

        # tenant_access_token 缓存
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None

        # HTTP 会话
        self._session = requests.Session()

    def is_configured(self) -> bool:
        """检查飞书多维表格配置是否完整"""
        return bool(self.app_id and self.app_secret and self.table_token)

    def _get_tenant_access_token(self) -> Optional[str]:
        """
        获取 tenant_access_token

        tenant_access_token 有效期为 2 小时，我们会缓存它
        """
        # 检查缓存的 token 是否仍然有效
        if self._access_token and self._token_expires_at:
            if datetime.now().timestamp() < self._token_expires_at:
                return self._access_token

        # 请求新的 token
        try:
            payload = {
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }

            response = requests.post(
                self.TOKEN_URL,
                json=payload,
                timeout=10
            )

            response.raise_for_status()
            data = response.json()

            if data.get("code") != 0:
                logger.error(f"获取 tenant_access_token 失败: {data.get('msg')}")
                return None

            self._access_token = data.get("tenant_access_token")
            # 缓存 1.5 小时（token 有效期 2 小时，提前更新）
            self._token_expires_at = datetime.now().timestamp() + 5400

            logger.info("tenant_access_token 获取成功")
            return self._access_token

        except requests.RequestException as e:
            logger.error(f"请求 tenant_access_token 失败: {e}")
            return None
        except Exception as e:
            logger.error(f"获取 tenant_access_token 异常: {e}")
            return None

    def _parse_table_token(self) -> tuple[str, str]:
        """
        解析 table_token，获取 app_token 和 table_id

        飞书多维表格 URL 格式：
        https://xxx.feishu.cn/base/<APP_TOKEN>/~/<TABLE_TOKEN>

        其中 TABLE_TOKEN 通常包含 app_token 和 table_id 信息

        Returns:
            (app_token, table_id) 元组
        """
        # 如果 table_token 包含 app_token 和 table_id（格式：app_token/table_id）
        if '/' in self.table_token:
            parts = self.table_token.split('/')
            if len(parts) == 2:
                return parts[0], parts[1]

        # 如果只有 table_token，需要从其他方式获取 app_token
        # 这里我们假设 table_token 就是表格的 token
        # 对于多维表格，我们需要先查询 app 信息

        # 简化方案：使用 table_token 直接查询
        # 注意：这需要 table_token 是完整的 token
        logger.warning(f"无法解析 table_token: {self.table_token}，尝试直接使用")

        # 返回一个默认值，实际使用时可能需要调整
        # 这里我们使用 table_token 作为 app_token的一部分
        return self.table_token, self.table_token

    def _list_table_records(
        self,
        app_token: str,
        table_id: str,
        page_size: int = 100,
        page_token: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        调用飞书 API 获取表格记录

        Args:
            app_token: 应用 token
            table_id: 表格 ID
            page_size: 每页记录数
            page_token: 分页 token

        Returns:
            API 响应数据字典，失败返回 None
        """
        access_token = self._get_tenant_access_token()
        if not access_token:
            return None

        url = self.TABLE_RECORDS_URL.format(app_token=app_token, table_id=table_id)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        params = {
            "page_size": page_size
        }

        if page_token:
            params["page_token"] = page_token

        try:
            response = self._session.get(
                url,
                headers=headers,
                params=params,
                timeout=10
            )

            response.raise_for_status()
            data = response.json()

            if data.get("code") != 0:
                logger.error(f"获取表格记录失败: {data.get('msg')} (code: {data.get('code')})")
                return None

            return data

        except requests.RequestException as e:
            logger.error(f"请求表格记录失败: {e}")
            return None
        except Exception as e:
            logger.error(f"获取表格记录异常: {e}")
            return None

    def read_stock_list(
        self,
        view_id: Optional[str] = None,
        field_name: str = "股票代码",
        filter_formula: Optional[str] = None
    ) -> List[str]:
        """
        从飞书多维表格读取股票代码列表

        Args:
            view_id: 视图 ID（可选，用于筛选特定视图的数据）
            field_name: 股票代码字段名称（默认："股票代码"）
            filter_formula: 筛选公式（可选，用于过滤数据）

        Returns:
            股票代码列表，如 ['600519', '000001', '300750']
        """
        if not self.is_configured():
            logger.warning("飞书多维表格未配置，无法读取股票列表")
            return []

        # 解析 table_token
        # 注意：飞书多维表格的 API 需要两个参数：
        # 1. app_token (从 URL 中获取)
        # 2. table_id (从 URL 中获取)
        #
        # table_token 格式可能为：
        # - bascnXXXXXX (旧的格式，需要单独获取 app_token)
        # - app_token/table_id (包含完整信息)

        # 如果使用完整格式
        if '/' in self.table_token:
            app_token, table_id = self.table_token.split('/')
        else:
            # 简化方案：使用 table_token 作为 table_id
            # app_token 需要单独配置或从其他方式获取
            # 这里我们假设用户配置的是完整的 token
            logger.error("table_token 格式不正确，应为 'app_token/table_id' 格式")
            logger.error("请在 .env 中设置正确的 FEISHU_TABLE_TOKEN")
            logger.error("格式示例: FEISHU_TABLE_TOKEN=app_token_here/table_id_here")
            return []

        # 获取第一页数据
        result = self._list_table_records(app_token, table_id, page_size=100)
        if not result:
            return []

        stock_list = []
        data = result.get("data", {})
        items = data.get("items", [])

        # 处理第一页数据
        stock_list.extend(self._extract_stock_codes(items, field_name))

        # 处理分页
        has_more = data.get("has_more", False)
        page_token = data.get("page_token")

        while has_more and page_token:
            result = self._list_table_records(app_token, table_id, page_token=page_token)
            if not result:
                break

            data = result.get("data", {})
            items = data.get("items", [])
            stock_list.extend(self._extract_stock_codes(items, field_name))

            has_more = data.get("has_more", False)
            page_token = data.get("page_token")

        logger.info(f"从飞书多维表格读取到 {len(stock_list)} 只股票")
        return stock_list

    def _extract_stock_codes(self, items: List[Dict[str, Any]], field_name: str) -> List[str]:
        """
        从记录列表中提取股票代码

        Args:
            items: 记录列表
            field_name: 股票代码字段名

        Returns:
            股票代码列表
        """
        stock_codes = []

        for record in items:
            fields = record.get("fields", {})
            stock_code = None

            # 优先使用指定的字段名
            if field_name in fields:
                stock_code = fields[field_name]

            # 尝试常见字段名
            elif '股票代码' in fields:
                stock_code = fields['股票代码']
            elif '代码' in fields:
                stock_code = fields['代码']
            elif 'code' in fields:
                stock_code = fields['code']
            elif 'Code' in fields:
                stock_code = fields['Code']

            # 处理股票代码
            if stock_code:
                # 如果是列表，取第一个元素
                if isinstance(stock_code, list):
                    stock_code = stock_code[0] if stock_code else None

                # 转换为字符串并清洗
                if isinstance(stock_code, str):
                    stock_code = stock_code.strip()
                    # 去除可能的前缀（如 "sz", "sh", "." 等）
                    stock_code = stock_code.replace('sz', '').replace('sh', '')
                    stock_code = stock_code.split('.')[0]  # 处理 "600519.SH" 格式

                    if stock_code and len(stock_code) == 6 and stock_code.isdigit():
                        stock_codes.append(stock_code)
                    else:
                        logger.warning(f"无效的股票代码格式: {stock_code}")
                else:
                    logger.warning(f"股票代码不是字符串类型: {stock_code} (类型: {type(stock_code)})")

        return stock_codes

    def get_table_records(
        self,
        view_id: Optional[str] = None,
        field_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        获取多维表格的所有记录数据（完整版）

        Args:
            view_id: 视图 ID（可选）
            field_names: 需要获取的字段名称列表（可选，None 表示获取所有字段）

        Returns:
            记录列表，每条记录是一个字典，包含字段名和对应的值
        """
        if not self.is_configured():
            logger.warning("飞书多维表格未配置，无法读取记录")
            return []

        # 解析 table_token
        if '/' in self.table_token:
            app_token, table_id = self.table_token.split('/')
        else:
            logger.error("table_token 格式不正确，应为 'app_token/table_id' 格式")
            return []

        # 获取第一页数据
        result = self._list_table_records(app_token, table_id, page_size=100)
        if not result:
            return []

        records = []
        data = result.get("data", {})
        items = data.get("items", [])

        # 处理第一页数据
        records.extend(self._process_records(items, field_names))

        # 处理分页
        has_more = data.get("has_more", False)
        page_token = data.get("page_token")

        while has_more and page_token:
            result = self._list_table_records(app_token, table_id, page_token=page_token)
            if not result:
                break

            data = result.get("data", {})
            items = data.get("items", [])
            records.extend(self._process_records(items, field_names))

            has_more = data.get("has_more", False)
            page_token = data.get("page_token")

        logger.info(f"从飞书多维表格读取到 {len(records)} 条记录")
        return records

    def _process_records(
        self,
        items: List[Dict[str, Any]],
        field_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        处理记录数据

        Args:
            items: 原始记录列表
            field_names: 需要保留的字段名列表

        Returns:
            处理后的记录列表
        """
        processed = []

        for record in items:
            fields = record.get("fields", {})

            # 如果指定了字段名，只返回这些字段
            if field_names:
                filtered_fields = {
                    k: v for k, v in fields.items()
                    if k in field_names
                }
                processed.append(filtered_fields)
            else:
                processed.append(dict(fields))

        return processed

    def __del__(self):
        """清理资源"""
        if hasattr(self, '_session'):
            self._session.close()


def get_stock_list_from_feishu() -> List[str]:
    """
    便捷函数：从飞书多维表格获取股票列表

    Returns:
        股票代码列表，如果读取失败则返回空列表
    """
    reader = FeishuBitableReader()
    return reader.read_stock_list()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    print("=" * 60)
    print("飞书多维表格读取测试（HTTP API 版本）")
    print("=" * 60)

    reader = FeishuBitableReader()

    # 检查配置
    if not reader.is_configured():
        print("\n[!] 飞书多维表格未配置")
        print("\n请在 .env 文件中配置以下环境变量：")
        print("  FEISHU_TABLE_TOKEN=<app_token>/<table_id>")
        print("  FEISHU_APP_ID_BITABLE=<你的 App ID>")
        print("  FEISHU_APP_SECRET_BITABLE=<你的 App Secret>")
        print("\n或者复用现有的飞书文档配置：")
        print("  FEISHU_APP_ID=<你的 App ID>")
        print("  FEISHU_APP_SECRET=<你的 App Secret>")
        print("  FEISHU_TABLE_TOKEN=<app_token>/<table_id>")
        print("\n注意：TABLE_TOKEN 格式应为 'app_token/table_id'")
    else:
        print(f"\n[*] 配置检查通过")
        print(f"    App ID: {reader.app_id[:10]}...")
        print(f"    Table Token: {reader.table_token[:20]}...")

        # 检查 table_token 格式
        if '/' not in reader.table_token:
            print(f"\n[!] 警告: TABLE_TOKEN 格式不正确")
            print(f"    当前格式: {reader.table_token}")
            print(f"    正确格式应为: app_token/table_id")
            print(f"    请在飞书多维表格 URL 中找到这两个值")
        else:
            app_token, table_id = reader.table_token.split('/')
            print(f"    App Token: {app_token[:10]}...")
            print(f"    Table ID: {table_id[:10]}...")

        # 读取股票列表
        print(f"\n[*] 正在读取股票列表...")
        stock_list = reader.read_stock_list()

        if stock_list:
            print(f"\n[OK] 成功读取 {len(stock_list)} 只股票：")
            for i, code in enumerate(stock_list, 1):
                print(f"  {i}. {code}")
        else:
            print(f"\n[X] 未读取到股票数据")

        # 获取完整记录（可选）
        print(f"\n[*] 正在读取完整记录...")
        records = reader.get_table_records()

        if records:
            print(f"\n[OK] 成功读取 {len(records)} 条记录")
            print(f"\n第一条记录示例：")
            if records:
                for k, v in records[0].items():
                    print(f"  {k}: {v}")
        else:
            print(f"\n[X] 未读取到记录数据")

    print("\n" + "=" * 60)
