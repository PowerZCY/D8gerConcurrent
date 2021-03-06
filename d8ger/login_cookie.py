#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import json
import os
import ssl

import requests

# 屏蔽HTTPS证书校验, 忽略安全警告
requests.packages.urllib3.disable_warnings()
context = ssl._create_unverified_context()

default_file_path = os.path.expanduser('~') + "/ssoLogin.json"
default_extra_cookie = "HT1=10225189"


def init_login_file_name() -> list:
    """
    初始化参数, 读取shell命令参数, 自动登录
    依次返回httpie_view方式, 线程池, 登录cookie
    :rtype: str
    """
    parser = argparse.ArgumentParser(description="登录解析器")
    parser.add_argument("-f", "--filepath", type=str, help="登录JSON文件路径, 默认 ~/ssoLogin.json")
    parser.add_argument("-e", "--extraCookie", type=str, help="登录额外cookie选项, 默认 HT1=10225189")
    args = parser.parse_args()
    sso_login_file_name = args.filepath
    if sso_login_file_name is None or len(sso_login_file_name) == 0 or str.isspace(sso_login_file_name):
        sso_login_file_name = default_file_path
    extra_cookie = default_extra_cookie
    if args.extraCookie is not None:
        extra_cookie = args.extraCookie
    print("设置登录文件: [{}]".format(sso_login_file_name))
    return [sso_login_file_name, extra_cookie]


def auto_login() -> str:
    """
    自动登录, 获取登录Cookie
    :rtype: str
    """
    login_result_list = init_login_file_name()
    login_file_name = login_result_list[0]
    extra_cookie = login_result_list[1]
    try:
        with open(login_file_name, 'r') as sso_login_request_data:
            request_json = json.load(sso_login_request_data)
    except Exception as e:
        print("不存在{}文件, 请先创建并按照JSON格式填写请求数据".format(login_file_name))
        print("示例ssoLogin.json:")
        default_login = {
            "url": "https://sso.testa.huitong.com/api/v100/ssonew/login",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "HT-app": 2
            },
            "body": {
                "phone": "18999999999",
                "smsAuthCode": "123456",
                "loginType": 0,
                "pwd": "123456"
            }
        }
        print(json.dumps(default_login, ensure_ascii=False, indent=4))
        exit(0)
    url = request_json['url']
    method = request_json['method']
    request_headers = handle_json_str_value(request_json['headers'])
    ht_app = request_headers['HT-app']
    if ht_app is None:
        ht_app = "2"
    content_type = request_headers['Content-Type']
    if content_type is None:
        content_type = "application/json"
    request_body = handle_json_str_value(request_json['body'])
    # request_headers = {"Content-Type": "application/json", "HT-app": "6"}
    response = requests.request(method, url, headers=request_headers, json=request_body, timeout=3, verify=False)
    response_headers = response.headers
    # 处理Cookie, 多个Cookie之间使用';'分隔, 否则校验cookie时出现"domain."在高版本中tomcat中报错
    # https://blog.csdn.net/w57685321/article/details/84943176
    cookie = response_headers.get("set-Cookie").replace(", _r", "; _r").replace(", _a", "; _a")
    # JSON标准格式
    response_body = json.dumps(response.json(), ensure_ascii=False, indent=4)
    session_cookie_file_json = {
        "__meta__": {
            "about": "HTTPie session file",
            "help": "https://httpie.org/doc#sessions",
            "httpie": "2.0.0"
        },
        "headers": {
            "Content-Type": content_type,
            "HT-app": ht_app,
            "Cookie": extra_cookie + "; " + cookie
        }
    }
    print("登录响应Cookie结果: \n{}\n\n登录响应BODY结果: \n{}\n".format(cookie, response_body))
    session_cookie_content = json.dumps(session_cookie_file_json, ensure_ascii=False, indent=4)
    session_cookie_file_name = os.path.expanduser('~') + "/session-cookie-read-only.json"
    try:
        with open(session_cookie_file_name, 'w') as session_cookie_file_data:
            session_cookie_file_data.write(session_cookie_content)
    except Exception as e:
        print("创建[{}]文件失败, 请检查权限".format(session_cookie_file_name))
    print("已创建[{}]文件方便后续接口调用, 文件内容如下\n{}".format(session_cookie_file_name, session_cookie_content))
    return cookie


def example_httpie_cmd():
    httpie_cmd = "http --verify=no -v --session-read-only=~/session-cookie-read-only.json POST https://127.0.0.1:8080/account/sentinel < ~/Desktop/ssoLogin/requestBody.json -d >>~/Desktop/ssoLogin/ResponseBody.json"
    print("在~/Desktop/ssoLogin/requestBody.json文件中写好请求body参数, 则示例Httpie命令: \n{}\n".format(httpie_cmd))
    print("HTTPie使用参考: https://httpie.org/docs#non-string-json-fields\n")


def handle_json_str_value(json: json) -> json:
    """
    将json的值都变为字符串处理
    :param json:
    :rtype: json
    """
    for (k, v) in json.items():
        json[k] = str(v)
    return json


def main():
    auto_login()
    example_httpie_cmd()


if __name__ == '__main__':
    main()
