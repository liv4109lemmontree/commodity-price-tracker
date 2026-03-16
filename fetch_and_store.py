import random
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re
import os

# selenium 相关库
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# --- Supabase 配置 ---
SUPABASE_URL = "https://zfhxofztxbxxpgvkmuig.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}
# --------------------

# ========== 更新后的商品列表（化工品类已大幅扩充） ==========
commodities = [
    # --- 农副 (保持不变) ---
    {"name": "大豆", "page_name": "大豆", "category": "农副"},
    {"name": "玉米淀粉", "page_name": "玉米淀粉", "category": "农副"},
    {"name": "玉米", "page_name": "玉米", "category": "农副"},
    {"name": "干香菇", "page_name": "干香菇", "category": "农副"},
    {"name": "白糖", "page_name": "白糖", "category": "农副"},
    {"name": "鲜香菇", "page_name": "鲜香菇", "category": "农副"},
    {"name": "豆粕", "page_name": "豆粕", "category": "农副"},
    {"name": "大豆油", "page_name": "大豆油", "category": "农副"},
    {"name": "菜籽粕", "page_name": "菜籽粕", "category": "农副"},
    {"name": "菜籽油", "page_name": "菜籽油", "category": "农副"},
    {"name": "棕榈油", "page_name": "棕榈油", "category": "农副"},
    {"name": "生猪", "page_name": "生猪", "category": "农副"},
    {"name": "鸡蛋", "page_name": "鸡蛋", "category": "农副"},

    # --- 化工 (全面扩充版) ---
    # 基础有机原料
    {"name": "纯苯", "page_name": "纯苯", "category": "化工"},
    {"name": "甲苯", "page_name": "甲苯", "category": "化工"},
    {"name": "混二甲苯", "page_name": "混二甲苯", "category": "化工"},
    {"name": "乙烯", "page_name": "乙烯", "category": "化工"},
    {"name": "丙烯", "page_name": "丙烯", "category": "化工"},
    {"name": "丁二烯", "page_name": "丁二烯", "category": "化工"},
    {"name": "甲醇", "page_name": "甲醇", "category": "化工"},
    {"name": "乙醇", "page_name": "乙醇", "category": "化工"},
    {"name": "乙二醇", "page_name": "乙二醇", "category": "化工"},
    {"name": "二甘醇", "page_name": "二甘醇", "category": "化工"},
    {"name": "正丁醇", "page_name": "正丁醇", "category": "化工"},
    {"name": "异丁醇", "page_name": "异丁醇", "category": "化工"},
    {"name": "辛醇", "page_name": "辛醇", "category": "化工"}, # 或异辛醇
    {"name": "异辛醇", "page_name": "异辛醇", "category": "化工"},
    {"name": "丙烷", "page_name": "丙烷", "category": "化工"},
    {"name": "正丁烷", "page_name": "正丁烷", "category": "化工"},
    {"name": "MTBE", "page_name": "MTBE", "category": "化工"},
    {"name": "石脑油", "page_name": "石脑油", "category": "化工"},
    {"name": "溶剂油", "page_name": "溶剂油", "category": "化工"},
    {"name": "石油焦", "page_name": "石油焦", "category": "化工"},
    
    # 无机化工
    {"name": "硫酸", "page_name": "硫酸", "category": "化工"},
    {"name": "盐酸", "page_name": "盐酸", "category": "化工"},
    {"name": "硝酸", "page_name": "硝酸", "category": "化工"},
    {"name": "磷酸", "page_name": "磷酸", "category": "化工"},
    {"name": "烧碱", "page_name": "烧碱", "category": "化工"}, # 氢氧化钠
    {"name": "纯碱", "page_name": "纯碱", "category": "化工"}, # 碳酸钠
    {"name": "小苏打", "page_name": "小苏打", "category": "化工"}, # 碳酸氢钠
    {"name": "硫磺", "page_name": "硫磺", "category": "化工"},
    {"name": "电石", "page_name": "电石", "category": "化工"}, # 碳化钙
    {"name": "黄磷", "page_name": "黄磷", "category": "化工"},
    {"name": "磷矿石", "page_name": "磷矿石", "category": "化工"},
    {"name": "钛白粉", "page_name": "钛白粉", "category": "化工"},
    {"name": "钛精矿", "page_name": "钛精矿", "category": "化工"},
    {"name": "硼酸", "page_name": "硼酸", "category": "化工"},
    {"name": "溴素", "page_name": "溴素", "category": "化工"},
    {"name": "双氧水", "page_name": "双氧水", "category": "化工"},
    {"name": "碳酸钾", "page_name": "碳酸钾", "category": "化工"},
    {"name": "碳酸锂", "page_name": "碳酸锂", "category": "化工"},
    {"name": "氢氧化锂", "page_name": "氢氧化锂", "category": "化工"},
    {"name": "液氯", "page_name": "液氯", "category": "化工"},
    {"name": "氯乙酸", "page_name": "氯乙酸", "category": "化工"},
    {"name": "三氯甲烷", "page_name": "三氯甲烷", "category": "化工"},
    {"name": "二氯甲烷", "page_name": "二氯甲烷", "category": "化工"},
    {"name": "四氯乙烯", "page_name": "四氯乙烯", "category": "化工"},
    {"name": "三氯乙烯", "page_name": "三氯乙烯", "category": "化工"},
    {"name": "氢氟酸", "page_name": "氢氟酸", "category": "化工"},
    
    # 化肥/农化
    {"name": "尿素", "page_name": "尿素", "category": "化工"},
    {"name": "复合肥", "page_name": "复合肥", "category": "化工"},
    {"name": "磷酸一铵", "page_name": "磷酸一铵", "category": "化工"},
    {"name": "磷酸二铵", "page_name": "磷酸二铵", "category": "化工"},
    {"name": "氯化钾", "page_name": "氯化钾", "category": "化工"}, # 注意页面可能为"氯化钾(进口)"
    {"name": "硫酸钾", "page_name": "硫酸钾", "category": "化工"},
    {"name": "硝酸钾", "page_name": "硝酸钾", "category": "化工"},
    {"name": "草甘膦", "page_name": "草甘膦", "category": "化工"},
    {"name": "硫酸铵", "page_name": "硫酸铵", "category": "化工"},
    
    # 芳烃及衍生物
    {"name": "苯乙烯", "page_name": "苯乙烯", "category": "化工"},
    {"name": "苯酚", "page_name": "苯酚", "category": "化工"},
    {"name": "丙酮", "page_name": "丙酮", "category": "化工"},
    {"name": "苯胺", "page_name": "苯胺", "category": "化工"},
    {"name": "MDI", "page_name": "MDI", "category": "化工"},          # 二苯基甲烷二异氰酸酯
    {"name": "TDI", "page_name": "TDI", "category": "化工"},          # 甲苯二异氰酸酯
    {"name": "环氧丙烷", "page_name": "环氧丙烷", "category": "化工"},
    {"name": "环氧乙烷", "page_name": "环氧乙烷", "category": "化工"},
    {"name": "环氧氯丙烷", "page_name": "环氧氯丙烷", "category": "化工"},
    {"name": "1,4-丁二醇", "page_name": "1,4-丁二醇", "category": "化工"},
    {"name": "DMF", "page_name": "DMF", "category": "化工"},          # 二甲基甲酰胺
    {"name": "DMAC", "page_name": "DMAC", "category": "化工"},        # 二甲基乙酰胺
    {"name": "N-甲基吡咯烷酮", "page_name": "N-甲基吡咯烷酮", "category": "化工"},
    {"name": "己内酰胺", "page_name": "己内酰胺", "category": "化工"},
    {"name": "PA6", "page_name": "PA6", "category": "化工"},          # 尼龙6
    {"name": "PA66", "page_name": "PA66", "category": "化工"},        # 尼龙66
    
    # 酸/酯/醇类
    {"name": "醋酸", "page_name": "醋酸", "category": "化工"},        # 乙酸
    {"name": "醋酐", "page_name": "醋酐", "category": "化工"},
    {"name": "醋酸乙酯", "page_name": "醋酸乙酯", "category": "化工"},
    {"name": "醋酸丁酯", "page_name": "醋酸丁酯", "category": "化工"},
    {"name": "丙烯酸", "page_name": "丙烯酸", "category": "化工"},
    {"name": "丙烯酸丁酯", "page_name": "丙烯酸丁酯", "category": "化工"},
    {"name": "丙烯酸甲酯", "page_name": "丙烯酸甲酯", "category": "化工"},
    {"name": "丙烯酸乙酯", "page_name": "丙烯酸乙酯", "category": "化工"},
    {"name": "甲基丙烯酸甲酯", "page_name": "甲基丙烯酸甲酯", "category": "化工"}, # MMA
    {"name": "顺酐", "page_name": "顺酐", "category": "化工"},        # 顺丁烯二酸酐
    {"name": "苯酐", "page_name": "苯酐", "category": "化工"},        # 邻苯二甲酸酐
    {"name": "己二酸", "page_name": "己二酸", "category": "化工"},
    {"name": "柠檬酸", "page_name": "柠檬酸", "category": "化工"},
    {"name": "甲酸", "page_name": "甲酸", "category": "化工"},
    {"name": "丙酸", "page_name": "丙酸", "category": "化工"},
    {"name": "丙烯腈", "page_name": "丙烯腈", "category": "化工"},
    {"name": "丙烯酰胺", "page_name": "丙烯酰胺", "category": "化工"},
    
    # 塑料/橡胶
    {"name": "聚乙烯", "page_name": "聚乙烯", "category": "化工"},    # PE
    {"name": "聚丙烯", "page_name": "聚丙烯", "category": "化工"},    # PP
    {"name": "聚氯乙烯", "page_name": "聚氯乙烯", "category": "化工"}, # PVC
    {"name": "ABS", "page_name": "ABS", "category": "化工"},
    {"name": "PS", "page_name": "PS", "category": "化工"},            # 聚苯乙烯
    {"name": "EPS", "page_name": "EPS", "category": "化工"},          # 可发性聚苯乙烯
    {"name": "PET", "page_name": "PET", "category": "化工"},          # 聚对苯二甲酸乙二醇酯
    {"name": "EVA", "page_name": "EVA", "category": "化工"},          # 乙烯-醋酸乙烯共聚物
    {"name": "顺丁橡胶", "page_name": "顺丁橡胶", "category": "化工"}, # BR
    {"name": "丁苯橡胶", "page_name": "丁苯橡胶", "category": "化工"}, # SBR
    {"name": "丁基橡胶", "page_name": "丁基橡胶", "category": "化工"}, # IIR
    {"name": "丁腈橡胶", "page_name": "丁腈橡胶", "category": "化工"}, # NBR
    {"name": "乙丙橡胶", "page_name": "乙丙橡胶", "category": "化工"}, # EPDM
    {"name": "天然橡胶", "page_name": "天然橡胶", "category": "化工"}, # 有时也归在橡塑
    
    # 氟化工/硅化工
    {"name": "萤石", "page_name": "萤石", "category": "化工"},
    {"name": "氟化铝", "page_name": "氟化铝", "category": "化工"},
    {"name": "冰晶石", "page_name": "冰晶石", "category": "化工"},
    {"name": "R22", "page_name": "R22", "category": "化工"},          # 二氟一氯甲烷
    {"name": "R134a", "page_name": "R134a", "category": "化工"},      # 四氟乙烷
    {"name": "有机硅DMC", "page_name": "有机硅DMC", "category": "化工"},
    {"name": "多晶硅", "page_name": "多晶硅", "category": "化工"},
    {"name": "白炭黑", "page_name": "白炭黑", "category": "化工"},    # 水合二氧化硅
    
    # 其他精细化学品
    {"name": "活性炭", "page_name": "活性炭", "category": "化工"},
    {"name": "焦亚硫酸钠", "page_name": "焦亚硫酸钠", "category": "化工"},
    {"name": "石蜡", "page_name": "石蜡", "category": "化工"},
    {"name": "石油树脂", "page_name": "石油树脂", "category": "化工"},
    {"name": "DOP", "page_name": "DOP", "category": "化工"},          # 邻苯二甲酸二辛酯
    {"name": "DINP", "page_name": "DINP", "category": "化工"},        # 邻苯二甲酸二异壬酯
    {"name": "DBP", "page_name": "DBP", "category": "化工"},          # 邻苯二甲酸二丁酯
    {"name": "DIBP", "page_name": "DIBP", "category": "化工"},        # 邻苯二甲酸二异丁酯
    {"name": "环氧大豆油", "page_name": "环氧大豆油", "category": "化工"},
    {"name": "脂肪醇", "page_name": "脂肪醇", "category": "化工"},
    {"name": "聚四氟乙烯", "page_name": "聚四氟乙烯", "category": "化工"}, # PTFE
    {"name": "维生素A", "page_name": "维生素A", "category": "化工"},
    {"name": "维生素C", "page_name": "维生素C", "category": "化工"},
    {"name": "维生素E", "page_name": "维生素E", "category": "化工"},
    {"name": "左旋肉碱", "page_name": "左旋肉碱", "category": "化工"},
    # 可以根据生意社页面继续补充 [citation:2][citation:10]
]

# ========== 品类对应的子域名 ==========
SUBDOMAIN_MAP = {
    "农副": "agr",
    "化工": "chem",
    # 后续可扩展 "能源": "energy", "金属": "metal"
}

# ========== 抓取函数（包含网络重试） ==========
def fetch_category_pages(category, target_names, start_page=1, max_pages=1100, incremental=False):
    """
    抓取指定品类的所有页面，包含网络重试机制
    :param category: 品类名（如 '农副', '化工'）
    :param target_names: 该品类下需要抓取的商品名列表（已弃用，但保留接口）
    :param start_page: 起始页码
    :param max_pages: 最大页码
    :param incremental: 是否增量模式（True: 只抓取包含当天日期的页面）
    """
    sub = SUBDOMAIN_MAP.get(category, "agr")
    base_url = f"https://{sub}.100ppi.com/kx/list---{{}}.html"
    latest_prices = {}
    page = start_page
    empty_page_count = 0      # 连续无 <li> 标签页计数
    today = datetime.now().date().isoformat()  # 当天日期

    print(f"\n===== 开始抓取 {category} 品类 (子域名: {sub}) =====")
    if incremental:
        print(f"增量模式：只抓取 {today} 的数据")
    print("正在启动无头浏览器获取数据...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        while True:
            url = base_url.format(page)
            print(f"\n正在抓取第 {page} 页: {url}")

            # ----- 页面加载重试机制（最多3次） -----
            max_retries = 3
            page_loaded = False
            for attempt in range(1, max_retries + 1):
                try:
                    print(f"  尝试第 {attempt} 次加载页面...")
                    driver.get(url)
                    time.sleep(random.uniform(3, 6))
                    page_loaded = True
                    break
                except Exception as e:
                    print(f"  第 {attempt} 次尝试失败: {e}")
                    if attempt == max_retries:
                        print(f"  页面 {url} 在 {max_retries} 次尝试后仍然失败，跳过该页。")
                        page_loaded = False
                    else:
                        wait_time = random.uniform(5, 10)
                        print(f"  等待 {wait_time:.1f} 秒后重试...")
                        time.sleep(wait_time)

            if not page_loaded:
                page += 1
                continue

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            items = soup.find_all('li')
            print(f"第 {page} 页找到 {len(items)} 个 <li> 标签")

            if not items:
                empty_page_count += 1
                if empty_page_count >= 2:
                    print("已到达最后一页（连续两页无<li>标签），停止翻页")
                    break
                else:
                    page += 1
                    continue
            else:
                empty_page_count = 0

            page_stored = 0
            page_products = set()
            page_has_today = False  # 增量模式用：记录本页是否有当天数据

            for li in items:
                # 1. 提取日期
                span = li.find('span')
                if not span:
                    continue
                date_text = span.get_text().strip()
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_text)
                if not date_match:
                    continue
                date_str = date_match.group(1)

                # 增量模式：检查是否是当天数据
                if incremental and date_str == today:
                    page_has_today = True

                # 2. 提取商品名
                a_tag = li.find('a')
                if not a_tag:
                    continue
                raw_name = a_tag.get_text().strip()

                # 3. 获取整个 <li> 的纯文本
                li_text = li.get_text()

                # 4. 直接在整个文本中搜索 "商品名为价格"
                price_match = re.search(rf'{re.escape(raw_name)}.*?为(\d+\.?\d*)', li_text)
                if not price_match:
                    continue
                price = float(price_match.group(1))

                # 5. 清洗商品名
                clean_name = raw_name
                if clean_name.startswith('日'):
                    clean_name = clean_name[1:]
                if clean_name.endswith('参考价'):
                    clean_name = clean_name[:-3]

                # 6. 存储所有商品（去重由 store_price 处理）
                store_price(clean_name, price, date_str, category)
                page_stored += 1
                page_products.add(clean_name)
                latest_prices[clean_name] = price

            if page_stored > 0:
                print(f"本页存储了 {page_stored} 条历史价格记录")
                print(f"本页商品: {list(page_products)}")
            else:
                print("本页无有效商品可存储")

            # 增量模式判断：如果本页没有当天数据，立即停止翻页
            if incremental and not page_has_today:
                print(f"第 {page} 页没有当天数据，停止翻页")
                break

            page += 1
            if page > max_pages:
                print(f"已达到预设最大页数 {max_pages}，停止翻页")
                break

    except Exception as e:
        print(f"抓取过程中出错: {e}")
    finally:
        driver.quit()

    print(f"{category} 品类抓取完成，共处理 {page-start_page} 页")
    return latest_prices

def store_price(name, price, price_date=None, category=None):
    """存储价格到 Supabase（支持分类）"""
    if price is None:
        return

    if price_date is None:
        date_str = datetime.now().date().isoformat()
    else:
        date_str = price_date

    print(f"准备存储: {name}, 日期: {date_str}, 价格: {price}, 分类: {category}")

    check_url = f"{SUPABASE_URL}/rest/v1/agricultural_prices"
    check_params = {
        "name": f"eq.{name}",
        "date": f"eq.{date_str}"
    }
    try:
        check_response = requests.get(check_url, headers=HEADERS, params=check_params)
        if check_response.status_code == 200 and len(check_response.json()) > 0:
            print(f"跳过: {name} 在 {date_str} 的价格已存在。")
            return

        data = {"name": name, "date": date_str, "price": price, "category": category}
        insert_response = requests.post(check_url, headers=HEADERS, json=data)
        if insert_response.status_code == 201:
            print(f"成功存储: {name} - {price} (日期: {date_str}, 分类: {category})")
        else:
            print(f"存储失败: {name}, 状态码: {insert_response.status_code}, 错误: {insert_response.text}")
    except Exception as e:
        print(f"存储过程中发生错误: {name}, 错误: {e}")

if __name__ == "__main__":
    print("开始执行数据抓取任务（增量模式，只抓取当天数据）...")

    # 模式选择：False 为增量模式（只抓包含当天日期的页面）
    FULL_MODE = False

    # 按品类分组商品
    categories_dict = {}
    for item in commodities:
        cat = item["category"]
        if cat not in categories_dict:
            categories_dict[cat] = []
        categories_dict[cat].append(item["page_name"])

    # 循环处理所有品类（农副、化工等）
    for cat, target_names in categories_dict.items():
        print(f"\n{'='*50}")
        print(f"准备处理品类: {cat}")
        print(f"包含商品数: {len(target_names)}")

        if FULL_MODE:
            # 全量模式（历史抓取）：从第1页开始，最多1100页
            start_page = 1
            max_pages = 1100
            incremental = False
        else:
            # 增量模式：从第1页开始，但会在内部根据日期自动停止
            start_page = 1
            max_pages = 50   # 农副最多2页，化工最多35页，50足够安全
            incremental = True

        latest = fetch_category_pages(
            category=cat,
            target_names=target_names,
            start_page=start_page,
            max_pages=max_pages,
            incremental=incremental
        )

        if latest:
            print(f"{cat} 品类当天抓取的商品数: {len(latest)}")
        else:
            print(f"{cat} 品类当天无新数据")

    print("\n所有品类抓取任务完成！")