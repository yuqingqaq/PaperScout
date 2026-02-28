#!/usr/bin/env python3
"""整理推荐日期"""
import json
import os
from datetime import datetime

# 路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
PAPERS_PATH = os.path.join(PROJECT_DIR, 'output', 'papers.json')

# 2月工作日
FEB_WORKDAYS = [
    # Week 1: 2-6
    '2026-02-02', '2026-02-03', '2026-02-04', '2026-02-05', '2026-02-06',
    # Week 2: 9-13
    '2026-02-09', '2026-02-10', '2026-02-11', '2026-02-12', '2026-02-13',
    # Week 4: 24-27
    '2026-02-24', '2026-02-25', '2026-02-26', '2026-02-27'
]

def get_recommend_date(published):
    if not published or published == 'Unknown':
        return '2026-01-30'
    
    # 解析发表日期
    try:
        pub_date = datetime.strptime(published, '%Y-%m-%d')
    except:
        return '2026-01-30'
    
    cutoff = datetime(2026, 1, 30)
    
    # 1月30日之前的 -> 推荐日期为1月30日
    if pub_date < cutoff:
        return '2026-01-30'
    
    # 推荐日期 = 发表日期的下一个工作日
    for wd in FEB_WORKDAYS:
        wd_date = datetime.strptime(wd, '%Y-%m-%d')
        if wd_date > pub_date:  # 严格大于，下一个工作日
            return wd
    
    # 如果都不符合，返回2月27日
    return '2026-02-27'


def main():
    # 读取论文
    with open(PAPERS_PATH, 'r') as f:
        data = json.load(f)
    
    # 更新每篇论文的推荐日期
    for paper in data['papers']:
        pub = paper.get('published', '')
        old_rec = paper.get('recommend_date', '')
        new_rec = get_recommend_date(pub)
        paper['recommend_date'] = new_rec
        print(f"{paper['arxiv_id']}: {pub} -> {new_rec} (was: {old_rec})")
    
    # 保存
    with open(PAPERS_PATH, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f'\n✓ 已更新 {len(data["papers"])} 篇论文的推荐日期')


if __name__ == '__main__':
    main()
