*** Settings ***
Documentation     百度搜索示例智能体
Library           agents.eg_baidu_search.baidu_search.BaiduSearchLibrary

*** Variables ***
# ${SEARCH_KEYWORD} 由外部传递（agent.json 中的 inputs 定义）
# 如果外部未传递，使用此默认值
${SEARCH_KEYWORD}    渐入佳境

*** Test Cases ***
百度搜索测试
    [Documentation]    使用百度搜索引擎进行关键词搜索
    [Tags]    smoke    baidu    search
    
    Open Baidu
    Search Keyword    ${SEARCH_KEYWORD}
    ${title}=    Get Page Title
    Log    搜索完成，页面标题: ${title}
    Close All Browsers

*** Keywords ***
Open Baidu Page
    [Documentation]    打开百度首页
    Open Baidu
    Log    百度首页打开成功

Search On Baidu
    [Arguments]    ${keyword}
    [Documentation]    在百度上搜索指定关键词
    Search Keyword    ${keyword}
    Log    搜索关键词 ${keyword} 完成
