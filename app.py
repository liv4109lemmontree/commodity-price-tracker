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

    if start_param and end_param:
        try:
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

    if start_date and end_date:
        current_start = start_date
        current_end = end_date
    else:
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
            * {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            }
            body {
                background: #f5f7fa;
                margin: 0;
                padding: 20px;
            }
            #chart-container {
                width: 100%;
                height: 600px;
                background: white;
                border-radius: 16px;
                box-shadow: 0 8px 20px rgba(0,0,0,0.05);
                padding: 16px;
                box-sizing: border-box;
                margin-top: 20px;
            }
            .controls {
                text-align: center;
                margin: 20px auto;
                background: white;
                padding: 20px;
                border-radius: 16px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.03);
                max-width: 900px;
            }
            .date-picker {
                margin: 10px 0;
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 10px;
            }
            .date-picker label {
                margin: 0 5px;
                font-size: 14px;
                color: #2c3e50;
                display: inline-flex;
                align-items: center;
                gap: 5px;
            }
            input[type="date"] {
                padding: 8px 12px;
                border: 1px solid #dcdfe6;
                border-radius: 30px;
                font-size: 14px;
                background: #f8fafc;
                transition: all 0.2s;
                outline: none;
            }
            input[type="date"]:focus {
                border-color: #409eff;
                box-shadow: 0 0 0 3px rgba(64,158,255,0.2);
            }
            select {
                padding: 8px 16px;
                border: 1px solid #dcdfe6;
                border-radius: 30px;
                font-size: 14px;
                background: #f8fafc;
                outline: none;
                min-width: 200px;
                max-width: 300px;
            }
            button {
                padding: 8px 18px;
                margin: 5px 8px;
                border: none;
                border-radius: 30px;
                background: #ecf5ff;
                color: #2c3e50;
                font-weight: 500;
                font-size: 14px;
                cursor: pointer;
                transition: all 0.2s ease;
                box-shadow: 0 2px 6px rgba(0,0,0,0.03);
            }
            button:hover {
                background: #d9e9ff;
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(64,158,255,0.2);
            }
            button.active {
                background: #409eff;
                color: white;
                box-shadow: 0 4px 12px rgba(64,158,255,0.3);
            }
            p {
                color: #5e6f88;
                font-size: 13px;
                margin-top: 15px;
            }
        </style>
    </head>
    <body>
        <div class="controls">
            <form method="get" style="display: inline-block;">
                <div class="date-picker">
                    <label>起始日期: <input type="date" name="start" value="{{ current_start }}" min="{{ global_min }}" max="{{ global_max }}"></label>
                    <label>结束日期: <input type="date" name="end" value="{{ current_end }}" min="{{ global_min }}" max="{{ global_max }}"></label>
                    <button type="submit">更新图表</button>
                </div>
            </form>
            <br>
            <div style="margin: 10px 0;">
                <select id="commodity-select">
                    <option value="all">全部商品</option>
                </select>
            </div>
            <button id="btn-all" class="active">显示全部</button>
            <button id="btn-agr">仅农副</button>
            <button id="btn-chem">仅化工</button>
            <p>点击品类按钮筛选，或在下方下拉框选择单个商品。</p>
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
                    symbolSize: 4,
                    connectNulls: true,
                    category: commodityCategories[name] || '未知'
                });
            }

            // 动态生成下拉选项
            var selectEl = document.getElementById('commodity-select');
            allSeries.sort((a, b) => a.name.localeCompare(b.name));
            allSeries.forEach(s => {
                var option = document.createElement('option');
                option.value = s.name;
                option.textContent = s.name + ' (' + s.category + ')';
                selectEl.appendChild(option);
            });

            var chartDom = document.getElementById('chart-container');
            var myChart = echarts.init(chartDom);

            // 基础配置函数（不含系列）
            function getBaseOption() {
                return {
                    title: {
                        text: '大宗商品价格走势',
                        left: 'center',
                        top: 10,
                        textStyle: { fontSize: 18, fontWeight: 'normal', color: '#2c3e50' }
                    },
                    tooltip: {
                        trigger: 'axis',
                        axisPointer: { type: 'shadow' },
                        backgroundColor: 'rgba(50,50,70,0.9)',
                        borderColor: '#aaa',
                        textStyle: { color: '#fff' }
                    },
                    legend: {
                        type: 'scroll',
                        orient: 'horizontal',
                        left: 'center',
                        bottom: 5,
                        icon: 'roundRect',
                        itemWidth: 12,
                        itemHeight: 8,
                        itemGap: 15,
                        textStyle: { fontSize: 12, color: '#2c3e50' },
                        pageIconColor: '#409eff',
                        pageIconSize: 12,
                        // 禁用默认的图例交互
                        selector: false,
                        selected: Object.fromEntries(allSeries.map(s => [s.name, true]))
                    },
                    grid: { left: '3%', right: '4%', bottom: '18%', top: '18%', containLabel: true },
                    xAxis: {
                        type: 'category',
                        data: dates,
                        axisLine: { lineStyle: { color: '#a0a0a0' } },
                        axisTick: { show: false },
                        axisLabel: { rotate: 30, fontSize: 11, color: '#5e6f88' },
                        splitLine: { show: false }
                    },
                    yAxis: {
                        type: 'value',
                        name: '价格 (元/吨)',
                        nameTextStyle: { fontSize: 12, color: '#5e6f88' },
                        axisLine: { show: false },
                        axisTick: { show: false },
                        axisLabel: { fontSize: 11, color: '#5e6f88' },
                        splitLine: { show: true, lineStyle: { color: '#eaeef2', type: 'dashed' } }
                    },
                    dataZoom: [
                        { type: 'slider', start: 0, end: 100, bottom: 10, height: 20, borderColor: 'transparent', backgroundColor: '#e4e7ed', fillerColor: 'rgba(64,158,255,0.2)', handleStyle: { color: '#409eff' } },
                        { type: 'inside', start: 0, end: 100 }
                    ],
                    color: ['#5470c6', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#ffdb5c', '#749f83']
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
                var newOption = getBaseOption();
                // 更新图例选中状态
                var selected = {};
                newSeries.forEach(s => selected[s.name] = true);
                newOption.legend.selected = selected;
                newOption.series = newSeries;
                myChart.setOption(newOption, { notMerge: true });
            }

            // 应用当前筛选：品类 + 商品选择
            function applyFilters() {
                var selectedCommodity = selectEl.value;
                var activeCat = null;
                if (btnAgr.classList.contains('active')) activeCat = '农副';
                else if (btnChem.classList.contains('active')) activeCat = '化工';

                var filtered = allSeries;
                if (activeCat) {
                    filtered = filtered.filter(s => s.category === activeCat);
                }
                if (selectedCommodity !== 'all') {
                    filtered = filtered.filter(s => s.name === selectedCommodity);
                }
                updateChartWithSeries(filtered);
            }

            // 设置按钮激活状态，并重置商品选择为全部
            function setActive(activeId) {
                btnAll.classList.remove('active');
                btnAgr.classList.remove('active');
                btnChem.classList.remove('active');
                if (activeId === 'btn-all') btnAll.classList.add('active');
                else if (activeId === 'btn-agr') btnAgr.classList.add('active');
                else if (activeId === 'btn-chem') btnChem.classList.add('active');
                // 点击品类按钮时，将商品选择设为"全部"
                selectEl.value = 'all';
                applyFilters();
            }

            // 按钮点击事件
            btnAll.addEventListener('click', function() {
                setActive('btn-all');
            });
            btnAgr.addEventListener('click', function() {
                setActive('btn-agr');
            });
            btnChem.addEventListener('click', function() {
                setActive('btn-chem');
            });

            // 商品选择变化
            selectEl.addEventListener('change', function() {
                // 清除所有按钮激活状态
                btnAll.classList.remove('active');
                btnAgr.classList.remove('active');
                btnChem.classList.remove('active');
                applyFilters();
            });

            // 初始化时默认全部显示
            applyFilters();

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