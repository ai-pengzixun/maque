*** Settings ***
Documentation     百度搜索OCR智能体
Library           agents.eg_baidu_search_ocr.baidu_search_ocr.BaiduSearchOCRLibrary

*** Variables ***
# ${SEARCH_KEYWORD} 由外部传递（agent.json 中的 inputs 定义）
# 如果外部未传递，使用此默认值
${SEARCH_KEYWORD}    渐入佳境

*** Test Cases ***
百度搜索OCR测试
    [Documentation]    使用OCR技术进行百度搜索关键词搜索
    [Tags]    smoke    baidu    search    ocr
    
    Open Baidu With OCR
    Search Keyword With OCR    ${SEARCH_KEYWORD}
    ${title}=    Get Page Title
    Log    搜索完成，页面标题: ${title}
    Close All Browsers

*** Keywords ***
Open Baidu Page With OCR
    [Documentation]    使用OCR打开百度首页
    Open Baidu With OCR
    Log    百度首页打开成功（OCR模式）

Search On Baidu With OCR
    [Arguments]    ${keyword}
    [Documentation]    使用OCR在百度上搜索指定关键词
    Search Keyword With OCR    ${keyword}
    Log    搜索关键词 ${keyword} 完成（OCR模式）
