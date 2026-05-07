#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import subprocess
from collections import defaultdict
from datetime import datetime

# ================= 配置 =================
DATA_DIR = "football.json/2025-26"
OUTPUT_FILE = "output/index.html"
LEAGUES = {
    "en.1.json": "Premier League",
    "es.1.json": "La Liga",
    "de.1.json": "Bundesliga",
    "it.1.json": "Serie A",
    "fr.1.json": "Ligue 1",
}
SEASON = "2025-26"
# ========================================

def load_matches(league_file):
    """加载联赛的 JSON 数据，返回比赛列表"""
    path = os.path.join(DATA_DIR, league_file)
    if not os.path.exists(path):
        print(f"警告: 文件 {path} 不存在，跳过")
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # 数据格式: {"name": "...", "rounds": [{"name": "...", "matches": [...]}]}
    matches = []
    for round_data in data.get("rounds", []):
        matches.extend(round_data.get("matches", []))
    return matches

def calculate_standings(matches):
    """根据比赛列表计算积分榜"""
    standings = defaultdict(lambda: {"played": 0, "won": 0, "drawn": 0, "lost": 0,
                                     "goals_for": 0, "goals_against": 0, "points": 0})
    for match in matches:
        team1 = match.get("team1", "")
        team2 = match.get("team2", "")
        score1 = match.get("score1")
        score2 = match.get("score2")
        if score1 is None or score2 is None:
            continue
        # 更新 team1
        standings[team1]["played"] += 1
        standings[team1]["goals_for"] += score1
        standings[team1]["goals_against"] += score2
        # 更新 team2
        standings[team2]["played"] += 1
        standings[team2]["goals_for"] += score2
        standings[team2]["goals_against"] += score1
        # 结果
        if score1 > score2:   # team1 胜
            standings[team1]["won"] += 1
            standings[team1]["points"] += 3
            standings[team2]["lost"] += 1
        elif score1 < score2: # team2 胜
            standings[team2]["won"] += 1
            standings[team2]["points"] += 3
            standings[team1]["lost"] += 1
        else:                 # 平局
            standings[team1]["drawn"] += 1
            standings[team2]["drawn"] += 1
            standings[team1]["points"] += 1
            standings[team2]["points"] += 1

    # 转换为列表并计算净胜球
    table = []
    for team, stat in standings.items():
        stat["goal_diff"] = stat["goals_for"] - stat["goals_against"]
        table.append({
            "team": team,
            "played": stat["played"],
            "won": stat["won"],
            "drawn": stat["drawn"],
            "lost": stat["lost"],
            "gf": stat["goals_for"],
            "ga": stat["goals_against"],
            "gd": stat["goal_diff"],
            "points": stat["points"]
        })
    # 排序：积分 > 净胜球 > 进球数
    table.sort(key=lambda x: (-x["points"], -x["gd"], -x["gf"]))
    # 添加排名
    for idx, row in enumerate(table, start=1):
        row["rank"] = idx
    return table

def generate_html(league_tables):
    """生成包含全部联赛表格的 HTML"""
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>五大联赛积分榜 - {SEASON}赛季</title>
    <style>
        body {{ font-family: 'Segoe UI', Roboto, Arial, sans-serif; background: #f0f2f5; margin: 0; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ text-align: center; color: #1e2a3a; margin-bottom: 10px; }}
        .sub {{ text-align: center; color: #4a6a8a; margin-bottom: 30px; }}
        .league {{ background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 30px; overflow-x: auto; }}
        .league h2 {{ background: #1e2a3a; color: white; margin: 0; padding: 12px 20px; font-size: 1.4rem; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
        th, td {{ padding: 10px 8px; text-align: center; border-bottom: 1px solid #e2e8f0; }}
        th {{ background: #f8fafc; color: #1e2a3a; font-weight: 600; }}
        tr:hover {{ background: #f1f5f9; }}
        .team {{ text-align: left; font-weight: 500; }}
        .rank {{ font-weight: bold; color: #2563eb; }}
        footer {{ text-align: center; margin-top: 30px; color: #6c757d; font-size: 12px; }}
    </style>
</head>
<body>
<div class="container">
    <h1>🏆 欧洲五大联赛积分榜</h1>
    <div class="sub">{SEASON}赛季 · 数据截止 {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
"""
    for league_name, table in league_tables:
        html += f"""
    <div class="league">
        <h2>📌 {league_name}</h2>
        <table>
            <thead>
                <tr><th>排名</th><th>球队</th><th>场次</th><th>胜</th><th>平</th><th>负</th><th>进球</th><th>失球</th><th>净胜球</th><th>积分</th></tr>
            </thead>
            <tbody>
"""
        for row in table:
            html += f"""
                <tr>
                    <td class="rank">{row['rank']}</td>
                    <td class="team">{row['team']}</td>
                    <td>{row['played']}</td>
                    <td>{row['won']}</td>
                    <td>{row['drawn']}</td>
                    <td>{row['lost']}</td>
                    <td>{row['gf']}</td>
                    <td>{row['ga']}</td>
                    <td>{row['gd']:+d}</td>
                    <td><strong>{row['points']}</strong></td>
                </tr>
"""
        html += """
            </tbody>
        </table>
    </div>
"""
    html += f"""
    <footer>数据来源: football.json | 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</footer>
</div>
</body>
</html>
"""
    return html

def git_commit_and_push():
    """使用 SSH 提交并推送更改（无需 token）"""
    try:
        # 添加 output/index.html （确保文件存在）
        subprocess.run(["git", "add", OUTPUT_FILE], check=True, capture_output=True, text=True)
        # 检查是否有变更
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            print("没有检测到文件变更，跳过提交")
            return
        # 提交
        commit_msg = f"Auto-update {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True, text=True)
        # 推送
        print("正在推送到远程仓库 (SSH)...")
        subprocess.run(["git", "push"], check=True, capture_output=True, text=True)
        print("✅ 推送成功！")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git 操作失败: {e}")
        if e.stderr:
            print(e.stderr)

def main():
    # 确保输出目录存在
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    league_tables = []
    for file_name, league_name in LEAGUES.items():
        print(f"处理 {league_name}...")
        matches = load_matches(file_name)
        if not matches:
            print(f"  警告: {league_name} 无比赛数据")
            continue
        table = calculate_standings(matches)
        league_tables.append((league_name, table))
        print(f"  已加载 {len(matches)} 场比赛，{len(table)} 支球队")

    if not league_tables:
        print("错误：未加载到任何联赛数据，请检查 football.json 目录结构")
        return

    # 生成 HTML
    html_content = generate_html(league_tables)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ 报告已生成: {OUTPUT_FILE}")

    # 提交并推送
    git_commit_and_push()

if __name__ == "__main__":
    main()