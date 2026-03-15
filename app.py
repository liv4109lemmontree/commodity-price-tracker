import os
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request
import requests
import json

# --- Supabase 配置（使用 Publishable key）---
SUPABASE_URL = "https://zfhxofztxbxxpgvkmuig.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}
# -------------------------------------------

app = Flask(__name__)

def get_full_date_range():
    """获取数据表中最早和最晚的日期，返回 (min_date, max_date) 字符串"""
    url = f"{SUPABASE_URL}/rest/v1/agricultural_prices"
    try:
        # 获取最早日期
        min_resp = requests.get(url, headers=HEADERS, params={"select": "date", "order": "date.asc", "limit": 1})
        min_data = min_resp.json()
        min_date = min_data[0]['date'] if min_data else None

        # 获取最晚日期
        max_resp = requests.get(url, headers=HEADERS, params={"select": "date", "order": "date.desc", "limit": 1})
        max_data = max_resp.json()
        max_date = max_data[0]['date'] if max_data else None

        return min_date, max_date
    except Exception as e:
        print(f"获取日期范围失败: {e}")
        return None, None

def get_chart_data(start_date=None, end_date=None):
    """
    获取指定日期范围内的价格数据（支持分页，确保获取全部）。
    循环请求直到没有数据为止。
    """
    if start_date and end_date:
        start = start_date
        end = end_date
    else:
        min_date, max_date = get_full_date_range()
        if min_date and max_date:
            start = min_date
            end = max_date
        else:
            end = datetime.now().date().isoformat()
            start = (datetime.now().date() - timedelta(days=365)).isoformat()

    url = f"{SUPABASE_URL}/rest/v1/agricultural_prices"
    all_data = []
    page_start = 0
    page_limit = 1000

    while True:
        params = [
            ("select", "name,date,price,category"),
            ("date", f"gte.{start}"),
            ("date", f"lte.{end}"),
            ("order", "date.asc"),
            ("limit", str(page_limit)),
            ("offset", str(page_start))
        ]

        try:
            response = requests.get(url, headers=HEADERS, params=params)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"分页获取数据失败 (offset {page_start}): {e}")
            break

        if not data:
            print(f"offset {page_start} 无数据，停止分页")
            break

        all_data.extend(data)
        print(f"获取到 {len(data)} 条数据，当前总条数 {len(all_data)} (offset {page_start})")

        if len(data) < page_limit:
            print("本次返回数据少于 limit，已是最后一页")
            break

        page_start += page_limit

    print(f"从Supabase总共获取到 {len(all_data)} 条数据 (范围: {start} 至 {end})")

    if not all_data:
        return [], {}, {}

    commodity_categories = {}
    names = set()
    for item in all_data:
        name = item['name']
        names.add(name)
        if name not in commodity_categories:
            commodity_categories[name] = item.get('category', '未知')

    names = sorted(names)
    dates = sorted(set(item['date'] for item in all_data))

    price_map = {name: {} for name in names}
    for item in all_data:
        price_map[item['name']][item['date']] = item['price']

    series_dict = {}
    for name in names:
        series_dict[name] = [price_map[name].get(d) for d in dates]

    return dates, series_dict, commodity_categories

@app.route('/')
def index():
    # 获取全局日期范围，用于前端日期选择器
    global_min_date, global_max_date = get_full_date_range()
    if not global_min_date or not global_max_date:
        global_min_date = "2025-01-01"
        global_max_date = datetime.now().date().isoformat()

    # 从请求参数获取用户选择的日期范围
    start_param = request.args.get('start')
    end_param = request.args.get('end')

    # 如果用户提供了有效日期，则使用；否则使用最近365天
    if start_param and end_param:
        try:
            # 简单验证日期格式
            datetime.strptime(start_param, '%Y-%m-%d')
            datetime.strptime(end_param, '%Y-%m-%d')
            start_date = start_param
            end_date = end_param
        except:
            start_date = None
            end_date = None
    else:
        start_date = None
        end_date = None

    dates, series_dict, commodity_categories = get_chart_data(start_date=start_date, end_date=end_date)

    dates_json = json.dumps(dates)
    series_json = json.dumps(series_dict)
    categories_json = json.dumps(commodity_categories)

    # 当前选择的日期，用于 input 的 value
    if start_date and end_date:
        current_start = start_date
        current_end = end_date
    else:
        # 默认最近365天
        current_end = datetime.now().date().isoformat()
        current_start = (datetime.now().date() - timedelta(days=365)).isoformat()

    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>大宗商品价格走势</title>
        <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
        <style>
            #chart-container { width: 100%; height: 600px; margin-top: 20px; }
            .controls { text-align: center; margin: 20px; }
            .date-picker { margin: 10px; }
            button { padding: 8px 16px; margin: 0 8px; cursor: pointer; }
            .category-btn.active { background-color: #4CAF50; color: white; }
        </style>
    </head>
    <body>
        <div class="controls">
            <form method="get" style="display: inline-block;">
                <label>起始日期: <input type="date" name="start" value="{{ current_start }}" min="{{ global_min }}" max="{{ global_max }}"></label>
                <label>结束日期: <input type="date" name="end" value="{{ current_end }}" min="{{ global_min }}" max="{{ global_max }}"></label>
                <button type="submit">更新图表</button>
            </form>
            <br>
            <button id="btn-all" class="active">显示全部</button>
            <button id="btn-agr">仅农副</button>
            <button id="btn-chem">仅化工</button>
            <p>点击图例中的商品名称，可以单独显示或隐藏该商品的曲线。</p>
        </div>
        <div id="chart-container"></div>

        <script>
            var dates = {{ dates_json | safe }};
            var seriesDict = {{ series_json | safe }};
            var commodityCategories = {{ categories_json | safe }};

            // 构建所有系列
            var allSeries = [];
            for (var name in seriesDict) {
                allSeries.push({
                    name: name,
                    type: 'line',
                    data: seriesDict[name],
                    smooth: true,
                    symbol: 'circle',
                    symbolSize: 6,
                    connectNulls: true,
                    category: commodityCategories[name] || '未知'
                });
            }

            var chartDom = document.getElementById('chart-container');
            var myChart = echarts.init(chartDom);

            // 基础配置函数（不含系列）
            function getBaseOption() {
                return {
                    title: { text: '大宗商品价格走势' },
                    tooltip: { trigger: 'axis' },
                    legend: { 
                        type: 'scroll',
                        pageIconColor: 'gray',
                        bottom: 10
                    },
                    grid: { left: '3%', right: '4%', bottom: '15%', top: '15%', containLabel: true },
                    xAxis: {
                        type: 'category',
                        data: dates,
                        axisLabel: { rotate: 30 }
                    },
                    yAxis: { type: 'value', name: '价格 (元/吨)' },
                    dataZoom: [
                        { type: 'slider', start: 0, end: 100 },
                        { type: 'inside', start: 0, end: 100 }
                    ]
                };
            }

            // 初始化图表（显示全部）
            myChart.setOption(Object.assign(getBaseOption(), { series: allSeries }), { notMerge: true });

            // 获取按钮
            var btnAll = document.getElementById('btn-all');
            var btnAgr = document.getElementById('btn-agr');
            var btnChem = document.getElementById('btn-chem');

            // 通用更新函数：构建新配置并替换
            function updateChartWithSeries(newSeries) {
                console.log('更新图表，系列数量:', newSeries.length);
                var newOption = Object.assign(getBaseOption(), { series: newSeries });
                myChart.setOption(newOption, { notMerge: true });
            }

            btnAll.addEventListener('click', function() {
                console.log('显示全部');
                updateChartWithSeries(allSeries);
                setActive('btn-all');
            });

            btnAgr.addEventListener('click', function() {
                console.log('仅农副');
                var filtered = allSeries.filter(s => s.category === '农副');
                console.log('农副系列数:', filtered.length);
                updateChartWithSeries(filtered);
                setActive('btn-agr');
            });

            btnChem.addEventListener('click', function() {
                console.log('仅化工');
                var filtered = allSeries.filter(s => s.category === '化工');
                console.log('化工系列数:', filtered.length);
                updateChartWithSeries(filtered);
                setActive('btn-chem');
            });

            function setActive(activeId) {
                ['btn-all', 'btn-agr', 'btn-chem'].forEach(id => {
                    var btn = document.getElementById(id);
                    if (btn) {
                        if (id === activeId) {
                            btn.classList.add('active');
                        } else {
                            btn.classList.remove('active');
                        }
                    }
                });
            }

            window.addEventListener('resize', function() { myChart.resize(); });
        </script>
    </body>
    </html>
    """

    return render_template_string(html_template,
                                  dates_json=dates_json,
                                  series_json=series_json,
                                  categories_json=categories_json,
                                  current_start=current_start,
                                  current_end=current_end,
                                  global_min=global_min_date,
                                  global_max=global_max_date)

if __name__ == '__main__':
    app.run(debug=True, port=5001)