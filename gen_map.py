# -*- coding: utf-8 -*-
import csv
import re
import svgwrite
import os
import colorsys

# ========== 配置区：在此填入通过编辑模式调试得到的正确值 ==========
# 平移
DEFAULT_TX = -24
DEFAULT_TY = -39
# 缩放 (X, Y 独立)
DEFAULT_SX = 1.95
DEFAULT_SY = 1.4
# 旋转角度 (度)
DEFAULT_ANGLE = 0
# 旋转中心 (画布坐标，通常为 500,400)
DEFAULT_CX = 500
DEFAULT_CY = 400
# ============================================================

def hsl_to_hex(h, s, l):
    """将 HSL 颜色转换为十六进制字符串 #RRGGBB"""
    r, g, b = colorsys.hls_to_rgb(h/360.0, l/100.0, s/100.0)
    return "#{:02x}{:02x}{:02x}".format(int(r*255), int(g*255), int(b*255))

def get_color_for_country(country_name):
    """根据国家中文名生成十六进制颜色"""
    if not country_name:
        return '#000000'  # 黑色
    h = sum(ord(c) for c in country_name) * 13 % 360
    s = 70
    l = 40
    return hsl_to_hex(h, s, l)

def parse_coord(coord_str):
    parts = coord_str.split(',')
    if len(parts) != 2:
        return None
    try:
        x = float(parts[0].strip())
        y = float(parts[1].strip())
        return (x, y)
    except ValueError:
        return None

def load_svg_background(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        match = re.search(r'<svg[^>]*>(.*?)</svg>', content, re.DOTALL)
        if match:
            return match.group(1).strip()
    except Exception as e:
        print(f"读取背景文件失败: {e}")
    return None

def generate_city_svg(cities, canvas_width=1000, canvas_height=800, margin=0.1):
    if not cities:
        return None

    xs = [c[1][0] for c in cities]
    ys = [c[1][1] for c in cities]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    width_x = max_x - min_x
    width_y = max_y - min_y
    if width_x == 0:
        width_x = 1
    if width_y == 0:
        width_y = 1

    min_x -= width_x * margin
    max_x += width_x * margin
    min_y -= width_y * margin
    max_y += width_y * margin

    def map_coord(x, y):
        px = (x - min_x) / (max_x - min_x) * canvas_width
        py = (max_y - y) / (max_y - min_y) * canvas_height
        return (px, py)

    dwg = svgwrite.Drawing(size=(canvas_width, canvas_height), profile='tiny')
    font_family = "SimHei, 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'PingFang SC', sans-serif"
    font_size = 20

    for code, coord, name, country_name in cities:
        x, y = map_coord(*coord)

        # 根据国家名生成文字颜色（十六进制）
        text_color = get_color_for_country(country_name)
        # 构造显示文本
        if country_name:
            display_name = f"{name} ({country_name})"
        else:
            display_name = name

        if code.startswith('town'):
            # 城镇：黑色方形，边长 8 像素
            dwg.add(dwg.rect(insert=(x-4, y-4), size=(8, 8),
                             fill='black', stroke='none'))
            text_elem = dwg.text(display_name, insert=(x + 7, y + 4),
                                 font_size=font_size, font_family=font_family,
                                 fill=text_color, class_='map-label')
            dwg.add(text_elem)
        elif code.startswith('castle'):
            # 城堡：黑色圆形，半径 3 像素
            dwg.add(dwg.circle(center=(x, y), r=3, fill='black', stroke='none'))
            text_elem = dwg.text(display_name, insert=(x + 7, y + 4),
                                 font_size=font_size, font_family=font_family,
                                 fill=text_color, class_='map-label')
            dwg.add(text_elem)
        else:
            dwg.add(dwg.circle(center=(x, y), r=3, fill='gray', stroke='none'))
            text_elem = dwg.text(display_name, insert=(x + 7, y + 4),
                                 font_size=font_size, font_family=font_family,
                                 fill='black', class_='map-label')
            dwg.add(text_elem)

    svg_string = dwg.tostring()
    svg_string = re.sub(r'<\?xml[^>]*\?>', '', svg_string).strip()
    return svg_string

def main():
    # 1. 读取城市数据（包含国家中文名）
    cities = []
    with open('result.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if len(row) < 5:
                continue
            code = row[0].strip()
            coord_str = row[1].strip()
            name = row[2].strip()
            country_name = row[4].strip()  # 第5列是国家中文名
            coord = parse_coord(coord_str)
            if coord:
                cities.append((code, coord, name, country_name))

    if not cities:
        print("没有有效的城市数据！")
        return

    # 2. 生成城市标记 SVG
    city_svg = generate_city_svg(cities)

    # 3. 加载日本地图背景
    bg_inner = load_svg_background('japan.svg')
    if bg_inner:
        bg_group = f'<g id="japan-background" opacity="0.6">{bg_inner}</g>'
        svg_content = re.sub(r'(<svg[^>]*>)', r'\1' + bg_group, city_svg, count=1)
        print("已嵌入日本地图背景")
    else:
        svg_content = city_svg
        print("未找到 japan.svg，将仅显示城市标记")

    # 添加旋转中心标记（初始隐藏）
    center_marker = '<circle id="rotation-center-marker" cx="0" cy="0" r="5" fill="none" stroke="blue" stroke-width="2" style="display:none;" /><path id="rotation-center-cross" d="M-5 0 L5 0 M0 -5 L0 5" stroke="blue" stroke-width="2" style="display:none;" transform="translate(0,0)" />'
    svg_content = re.sub(r'(<svg[^>]*>)', r'\1' + center_marker, svg_content, count=1)

    # 4. 构造 bgState 初始化的 JavaScript 代码
    bg_state_code = f"""let bgState = {{
    tx: {DEFAULT_TX},
    ty: {DEFAULT_TY},
    sx: {DEFAULT_SX},
    sy: {DEFAULT_SY},
    angle: {DEFAULT_ANGLE},
    cx: {DEFAULT_CX},
    cy: {DEFAULT_CY},
}};
const defaultBgState = {{ ...bgState }};"""

    # 5. HTML 模板（包含最小化功能）
    html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>日本城市分布地图（固定全图调试）</title>
    <script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js"></script>
    <style>
        html, body {
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
            overflow: hidden;
            background-color: #f0f0f0;
            font-family: Arial, sans-serif;
        }
        #map-container {
            width: 100%;
            height: 100%;
        }
        svg {
            width: 100%;
            height: 100%;
            display: block;
            background-color: white;
        }
        #control-panel {
            position: fixed;
            top: 20px;
            left: 20px;
            background: rgba(255,255,255,0.95);
            border: 1px solid #ccc;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            z-index: 1000;
            pointer-events: auto;
            width: 380px;
            max-height: 90vh;
            overflow-y: auto;
            transition: opacity 0.2s;
        }
        #control-panel.hidden {
            display: none;
        }
        #toggle-panel-btn {
            position: fixed;
            top: 20px;
            left: 20px;
            z-index: 1001;
            width: 36px;
            height: 36px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 50%;
            font-size: 24px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            line-height: 1;
            transition: background-color 0.2s;
        }
        #toggle-panel-btn:hover {
            background-color: #45a049;
        }
        #toggle-panel-btn.hidden {
            display: flex;  /* 始终显示，由内部符号变化 */
        }
        #control-panel h3 {
            margin-top: 0;
            text-align: center;
        }
        .mode-toggle {
            margin-bottom: 15px;
            text-align: center;
        }
        .mode-toggle label {
            font-weight: bold;
            margin-right: 10px;
        }
        .status-item {
            margin: 8px 0;
            font-size: 0.9em;
            display: flex;
            justify-content: space-between;
        }
        .status-item span:first-child {
            font-weight: bold;
        }
        .scale-row {
            display: flex;
            align-items: center;
            margin: 5px 0;
        }
        .scale-row span {
            width: 60px;
            font-weight: bold;
        }
        .scale-row button {
            width: 50px;
            margin: 0 5px;
            padding: 5px;
            background-color: #2196F3;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .scale-row button:hover {
            background-color: #1976D2;
        }
        .scale-value {
            margin-left: 10px;
            min-width: 50px;
            text-align: right;
        }
        .note {
            font-size: 0.85em;
            color: #666;
            margin-top: 15px;
            border-top: 1px solid #ddd;
            padding-top: 10px;
        }
        .note kbd {
            background: #f0f0f0;
            border: 1px solid #ccc;
            border-radius: 3px;
            padding: 2px 5px;
            font-size: 0.9em;
        }
        button {
            width: 100%;
            padding: 8px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 1em;
            margin-top: 10px;
        }
        button:hover {
            background-color: #45a049;
        }
        .edit-mode-highlight {
            filter: drop-shadow(0 0 5px rgba(0,0,255,0.8));
            stroke: blue !important;
            stroke-width: 2 !important;
        }
        .checkbox-row {
            display: flex;
            align-items: center;
            margin: 10px 0;
        }
        .checkbox-row input {
            margin-right: 8px;
        }
    </style>
</head>
<body>
    <div id="map-container">
        {svg_content}
    </div>
    <button id="toggle-panel-btn">+</button>
    <div id="control-panel" class="hidden">
        <h3>背景地图调整</h3>
        <div class="mode-toggle">
            <label>
                <input type="checkbox" id="edit-mode-checkbox"> 编辑模式
            </label>
            <span style="font-size:0.9em; color:#666;">(背景可调，城市固定)</span>
        </div>
        <div class="checkbox-row">
            <input type="checkbox" id="fixed-view-checkbox">
            <label for="fixed-view-checkbox"><strong>固定全图</strong> (强制显示完整画布)</label>
        </div>
        <div class="status-item">
            <span>平移 X:</span> <span id="tx-display">0</span>
        </div>
        <div class="status-item">
            <span>平移 Y:</span> <span id="ty-display">0</span>
        </div>
        <div class="status-item">
            <span>缩放 X:</span> <span id="sx-display">1.00</span>
        </div>
        <div class="status-item">
            <span>缩放 Y:</span> <span id="sy-display">1.00</span>
        </div>
        <div class="status-item">
            <span>旋转角度:</span> <span id="angle-display">0°</span>
        </div>
        <div class="status-item">
            <span>旋转中心 X:</span> <span id="cx-display">500</span>
        </div>
        <div class="status-item">
            <span>旋转中心 Y:</span> <span id="cy-display">400</span>
        </div>

        <div style="margin: 10px 0; border-top: 1px solid #ccc;"></div>
        <div style="font-weight: bold; margin-bottom: 5px;">独立缩放 (按钮)</div>
        <div class="scale-row">
            <span>X轴:</span>
            <button id="sx-minus">-</button>
            <button id="sx-plus">+</button>
            <span class="scale-value" id="sx-value">1.00</span>
        </div>
        <div class="scale-row">
            <span>Y轴:</span>
            <button id="sy-minus">-</button>
            <button id="sy-plus">+</button>
            <span class="scale-value" id="sy-value">1.00</span>
        </div>

        <button id="reset-bg-btn">重置背景</button>
        <div class="note">
            <p><strong>编辑模式操作（背景移动，城市不动）：</strong></p>
            <p><kbd>左键拖动</kbd> 平移背景</p>
            <p><kbd>Ctrl + 左键</kbd> 设置旋转中心（蓝色十字）</p>
            <p><kbd>Q</kbd> / <kbd>E</kbd> 旋转（1°/次）</p>
            <p><kbd>滚轮</kbd> 同时缩放 XY (等比)</p>
            <p>下方按钮可独立缩放 X 或 Y。</p>
            <p>勾选“固定全图”可强制显示完整画布，便于调试。</p>
            <p><strong>重置背景将恢复为您在脚本配置区设置的默认值。</strong></p>
        </div>
    </div>

    <script>
        (function() {
            const svgElement = document.querySelector('#map-container svg');
            if (!svgElement) return;

            // 获取背景元素
            const bgGroup = document.getElementById('japan-background');
            if (!bgGroup) {
                document.getElementById('control-panel').style.display = 'none';
                console.warn('未找到背景元素，控制面板已隐藏');
                return;
            }

            // 添加固定网格背景（作为参考系）
            function addGrid() {
                const gridGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
                gridGroup.setAttribute('id', 'grid-background');
                gridGroup.setAttribute('opacity', '0.15');
                for (let i = 0; i <= 1000; i += 50) {
                    const lineV = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                    lineV.setAttribute('x1', i);
                    lineV.setAttribute('y1', 0);
                    lineV.setAttribute('x2', i);
                    lineV.setAttribute('y2', 800);
                    lineV.setAttribute('stroke', '#888');
                    lineV.setAttribute('stroke-width', '0.5');
                    gridGroup.appendChild(lineV);
                }
                for (let i = 0; i <= 800; i += 50) {
                    const lineH = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                    lineH.setAttribute('x1', 0);
                    lineH.setAttribute('y1', i);
                    lineH.setAttribute('x2', 1000);
                    lineH.setAttribute('y2', i);
                    lineH.setAttribute('stroke', '#888');
                    lineH.setAttribute('stroke-width', '0.5');
                    gridGroup.appendChild(lineH);
                }
                svgElement.insertBefore(gridGroup, svgElement.firstChild);
            }
            addGrid();

            // 旋转中心标记
            const centerMarker = document.getElementById('rotation-center-marker');
            const centerCross = document.getElementById('rotation-center-cross');

            // ---------- 背景变换状态 ----------
            /*BG_STATE*/

            // 更新背景 transform 并刷新显示
            function applyBackgroundTransform() {
                const { tx, ty, sx, sy, angle, cx, cy } = bgState;
                const transform = `translate(${tx}, ${ty}) translate(${cx}, ${cy}) rotate(${angle}) scale(${sx}, ${sy}) translate(${-cx}, ${-cy})`;
                bgGroup.setAttribute('transform', transform);

                document.getElementById('tx-display').textContent = tx.toFixed(1);
                document.getElementById('ty-display').textContent = ty.toFixed(1);
                document.getElementById('sx-display').textContent = sx.toFixed(2);
                document.getElementById('sy-display').textContent = sy.toFixed(2);
                document.getElementById('sx-value').textContent = sx.toFixed(2);
                document.getElementById('sy-value').textContent = sy.toFixed(2);
                document.getElementById('angle-display').textContent = angle + '°';
                document.getElementById('cx-display').textContent = cx.toFixed(1);
                document.getElementById('cy-display').textContent = cy.toFixed(1);

                if (centerMarker && centerCross) {
                    centerMarker.setAttribute('cx', cx);
                    centerMarker.setAttribute('cy', cy);
                    centerCross.setAttribute('transform', `translate(${cx}, ${cy})`);
                }
            }

            function showCenterMarker(show) {
                if (centerMarker) centerMarker.style.display = show ? 'block' : 'none';
                if (centerCross) centerCross.style.display = show ? 'block' : 'none';
            }

            applyBackgroundTransform();
            showCenterMarker(false);

            // 重置背景到默认值（从配置区读取）
            function resetBackground() {
                bgState = { ...defaultBgState };
                applyBackgroundTransform();
                showCenterMarker(false);
            }

            // ---------- 初始化 svg-pan-zoom ----------
            let panZoomInstance = svgPanZoom(svgElement, {
                zoomEnabled: true,
                controlIconsEnabled: true,
                fit: true,
                center: true,
                minZoom: 0.5,
                maxZoom: 10,
                zoomScaleSensitivity: 0.4,
            });

            // 文字固定大小处理
            const labels = svgElement.querySelectorAll('.map-label');
            const baseFontSize = 20;
            function updateFontSize() {
                const zoom = panZoomInstance.getZoom();
                const newSize = baseFontSize / zoom;
                labels.forEach(text => {
                    text.setAttribute('font-size', newSize + 'px');
                });
            }
            updateFontSize();
            panZoomInstance.setOnZoom(updateFontSize);

            // ---------- 固定全图控制 ----------
            const fixedViewCheckbox = document.getElementById('fixed-view-checkbox');
            let fixedView = false;

            function applyFixedView(force) {
                if (fixedView) {
                    svgElement.setAttribute('viewBox', '0 0 1000 800');
                    if (panZoomInstance && !editingMode) {
                        panZoomInstance.disable();
                    }
                } else {
                    if (!editingMode) {
                        if (!panZoomInstance) {
                            panZoomInstance = svgPanZoom(svgElement, {
                                zoomEnabled: true,
                                controlIconsEnabled: true,
                                fit: true,
                                center: true,
                                minZoom: 0.5,
                                maxZoom: 10,
                            });
                            panZoomInstance.setOnZoom(updateFontSize);
                        } else {
                            panZoomInstance.enable();
                        }
                    }
                }
            }

            fixedViewCheckbox.addEventListener('change', function(e) {
                fixedView = e.target.checked;
                applyFixedView();
            });

            // ---------- 编辑模式状态 ----------
            let editingMode = false;
            const editCheckbox = document.getElementById('edit-mode-checkbox');

            let isDragging = false;
            let dragStartX, dragStartY;
            let dragStartTx, dragStartTy;

            function getMouseCanvasCoords(event) {
                const pt = svgElement.createSVGPoint();
                pt.x = event.clientX;
                pt.y = event.clientY;
                const ctm = svgElement.getScreenCTM().inverse();
                const svgCoord = pt.matrixTransform(ctm);
                return { x: svgCoord.x, y: svgCoord.y };
            }

            function setCityOpacity(opacity) {
                const cityElements = svgElement.querySelectorAll('.map-label, circle, rect');
                cityElements.forEach(el => {
                    if (el.id !== 'japan-background' && el.id !== 'rotation-center-marker' && el.id !== 'rotation-center-cross') {
                        el.style.opacity = opacity;
                    }
                });
            }

            function onMouseDown(e) {
                if (!editingMode) return;
                e.preventDefault();
                e.stopPropagation();

                const coords = getMouseCanvasCoords(e);
                if (e.ctrlKey) {
                    bgState.cx = coords.x;
                    bgState.cy = coords.y;
                    bgState.angle = 0;
                    applyBackgroundTransform();
                    showCenterMarker(true);
                } else {
                    isDragging = true;
                    dragStartX = coords.x;
                    dragStartY = coords.y;
                    dragStartTx = bgState.tx;
                    dragStartTy = bgState.ty;
                }
            }

            function onMouseMove(e) {
                if (!editingMode || !isDragging) return;
                e.preventDefault();
                e.stopPropagation();

                const coords = getMouseCanvasCoords(e);
                const dx = coords.x - dragStartX;
                const dy = coords.y - dragStartY;
                bgState.tx = dragStartTx + dx;
                bgState.ty = dragStartTy + dy;
                applyBackgroundTransform();
            }

            function onMouseUp(e) {
                if (!editingMode) return;
                e.preventDefault();
                e.stopPropagation();
                isDragging = false;
            }

            function onWheel(e) {
                if (!editingMode) return;
                e.preventDefault();
                e.stopPropagation();

                const delta = -Math.sign(e.deltaY) * 0.1;
                let newSx = bgState.sx + delta;
                let newSy = bgState.sy + delta;
                newSx = Math.min(5.0, Math.max(0.2, newSx));
                newSy = Math.min(5.0, Math.max(0.2, newSy));
                bgState.sx = newSx;
                bgState.sy = newSy;
                applyBackgroundTransform();
            }

            function onKeyDown(e) {
                if (!editingMode) return;
                if (e.key === 'q' || e.key === 'Q') {
                    e.preventDefault();
                    bgState.angle -= 1;
                    applyBackgroundTransform();
                } else if (e.key === 'e' || e.key === 'E') {
                    e.preventDefault();
                    bgState.angle += 1;
                    applyBackgroundTransform();
                }
            }

            function adjustSx(delta) {
                if (!editingMode) {
                    alert('请先开启编辑模式');
                    return;
                }
                let newSx = bgState.sx + delta;
                newSx = Math.min(5.0, Math.max(0.2, newSx));
                bgState.sx = newSx;
                applyBackgroundTransform();
            }
            function adjustSy(delta) {
                if (!editingMode) {
                    alert('请先开启编辑模式');
                    return;
                }
                let newSy = bgState.sy + delta;
                newSy = Math.min(5.0, Math.max(0.2, newSy));
                bgState.sy = newSy;
                applyBackgroundTransform();
            }

            document.getElementById('sx-minus').addEventListener('click', () => adjustSx(-0.05));
            document.getElementById('sx-plus').addEventListener('click', () => adjustSx(0.05));
            document.getElementById('sy-minus').addEventListener('click', () => adjustSy(-0.05));
            document.getElementById('sy-plus').addEventListener('click', () => adjustSy(0.05));

            function setEditingMode(enabled) {
                editingMode = enabled;
                if (enabled) {
                    if (panZoomInstance) {
                        panZoomInstance.destroy();
                        panZoomInstance = null;
                    }
                    if (!fixedView) {
                        // 保持当前 viewBox 不变
                    } else {
                        svgElement.setAttribute('viewBox', '0 0 1000 800');
                    }
                    bgGroup.classList.add('edit-mode-highlight');
                    setCityOpacity(0.3);
                    if (bgState.cx !== 500 || bgState.cy !== 400) {
                        showCenterMarker(true);
                    }
                    svgElement.addEventListener('mousedown', onMouseDown);
                    window.addEventListener('mousemove', onMouseMove);
                    window.addEventListener('mouseup', onMouseUp);
                    svgElement.addEventListener('wheel', onWheel, { passive: false });
                    window.addEventListener('keydown', onKeyDown);
                } else {
                    bgGroup.classList.remove('edit-mode-highlight');
                    setCityOpacity(1.0);
                    showCenterMarker(false);
                    svgElement.removeEventListener('mousedown', onMouseDown);
                    window.removeEventListener('mousemove', onMouseMove);
                    window.removeEventListener('mouseup', onMouseUp);
                    svgElement.removeEventListener('wheel', onWheel);
                    window.removeEventListener('keydown', onKeyDown);
                    isDragging = false;

                    if (!fixedView) {
                        panZoomInstance = svgPanZoom(svgElement, {
                            zoomEnabled: true,
                            controlIconsEnabled: true,
                            fit: true,
                            center: true,
                            minZoom: 0.5,
                            maxZoom: 10,
                        });
                        panZoomInstance.setOnZoom(updateFontSize);
                        updateFontSize();
                    } else {
                        svgElement.setAttribute('viewBox', '0 0 1000 800');
                    }
                }
            }

            editCheckbox.addEventListener('change', function(e) {
                setEditingMode(e.target.checked);
            });

            document.getElementById('reset-bg-btn').addEventListener('click', resetBackground);

            // ---------- 面板最小化功能 ----------
            const toggleBtn = document.getElementById('toggle-panel-btn');
            const panel = document.getElementById('control-panel');
            toggleBtn.addEventListener('click', function() {
                if (panel.classList.contains('hidden')) {
                    panel.classList.remove('hidden');
                    toggleBtn.textContent = '−';
                } else {
                    panel.classList.add('hidden');
                    toggleBtn.textContent = '+';
                }
            });

            // 初始为非编辑模式
            setEditingMode(false);
        })();
    </script>
</body>
</html>
"""

    # 6. 将占位符 /*BG_STATE*/ 替换为实际的 bgState 代码
    html_output = html_template.replace('/*BG_STATE*/', bg_state_code)

    # 7. 写入 HTML 文件
    with open('map.html', 'w', encoding='utf-8') as f:
        f.write(html_output.replace('{svg_content}', svg_content))

    print("交互式地图已生成：map.html")
    print("默认背景参数已从配置区读取。重置背景将恢复这些默认值。")
    print("城镇显示为黑色方形，城堡显示为黑色圆形，文字颜色按国家区分并附国家名。")
    print("新增最小化按钮（左上角），点击可隐藏/显示控制面板。")

if __name__ == '__main__':
    main()