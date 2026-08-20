/** data/ 目录内可用数据集清单（与 FastAPI 的 data_path 白名单对应，API 按相对路径读取）。 */
import type { DatasetInfo } from "./types";

export const DATASETS: DatasetInfo[] = [
  {
    path: "sample_sales.csv",
    name: "示例销售数据",
    description: "项目内置的示例销售额数据，适合快速体验自然语言问答与图表分析。",
    format: "CSV",
    size: "小",
  },
  {
    path: "olist/olist_orders_dataset.csv",
    name: "Olist 订单主表",
    description: "巴西电商订单主数据：订单状态、下单/发货/送达时间戳（9.9 万订单）。",
    format: "CSV",
    size: "中",
  },
  {
    path: "olist/olist_order_items_dataset.csv",
    name: "Olist 订单明细",
    description: "订单商品明细：单价、运费、卖家/买家评分（11.2 万明细行）。",
    format: "CSV",
    size: "中",
  },
  {
    path: "olist/olist_customers_dataset.csv",
    name: "Olist 客户主数据",
    description: "客户唯一 ID、所在城市/州（用于 RFM 分层与地域分析）。",
    format: "CSV",
    size: "中",
  },
  {
    path: "olist/olist_products_dataset.csv",
    name: "Olist 商品主数据",
    description: "商品 ID、类别、尺寸重量等属性。",
    format: "CSV",
    size: "中",
  },
  {
    path: "olist/olist_sellers_dataset.csv",
    name: "Olist 卖家主数据",
    description: "卖家 ID 与所在城市/州。",
    format: "CSV",
    size: "小",
  },
  {
    path: "olist/olist_order_reviews_dataset.csv",
    name: "Olist 订单评价",
    description: "订单评价分数与评论文本（客户满意度分析）。",
    format: "CSV",
    size: "中",
  },
];
