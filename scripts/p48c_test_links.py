#!/usr/bin/env python3
from __future__ import annotations

from urllib.parse import urlencode

BASE="https://jianshi-bua.pages.dev"
PROJECTS=[
    ("vertical-industry-saas","垂直行业软件订阅服务（SaaS）"),
    ("amazon-fba-niche-brand","亚马逊物流（FBA）细分品牌"),
    ("digital-product-business","数字产品业务"),
    ("affiliate-content-site","联盟营销 / 内容站"),
    ("amazon-kdp-publishing","亚马逊 KDP 数字出版"),
    ("agency-business","垂直服务型业务"),
]


def tagged(path:str, *, source:str, medium:str, campaign:str)->str:
    q=urlencode({
        "utm_source":source,
        "utm_medium":medium,
        "utm_campaign":campaign,
    })
    return f"{BASE}{path}?{q}"


def main()->None:
    print("P4.8C｜第一批真实用户测试链接")
    print()
    print("【主测试入口｜优先使用】")
    print(tagged(
        "/",
        source="manual_invite",
        medium="private_share",
        campaign="p48_first100",
    ))
    print()
    print("【机会库入口｜仅当受测者已经理解见势是什么】")
    print(tagged(
        "/opportunities/",
        source="manual_invite",
        medium="guided_test",
        campaign="p48_library_test",
    ))
    print()
    print("【定性访谈｜直接进入指定项目，不计入首页入口转化判断】")
    for slug,title in PROJECTS:
        print(f"{title}:")
        print(tagged(
            f"/opportunity/{slug}/",
            source="manual_interview",
            medium="guided_test",
            campaign="p48_project_interview",
        ))
    print()
    print("【内部 QA｜不发送行为分析事件】")
    print(f"{BASE}/?qa=1")
    print(f"{BASE}/opportunities/?qa=1")
    for slug,title in PROJECTS:
        print(f"{title}: {BASE}/opportunity/{slug}/?qa=1")


if __name__=="__main__":
    main()
