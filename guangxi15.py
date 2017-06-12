import requests
from bs4 import BeautifulSoup
import time
import re
import random
import logging
import socket
import base64
from postgresql import driver
import postgresql
import json

logging.basicConfig(level=logging.DEBUG)

'信用广西详情爬取中,新增的十五位注册码'

DB = driver.connect(host='106.75.145.80', user='gxj', password='xiaojun.guo1', database='cra1', port=9988)


# 数据库异常重新连接
def conn_sql():
    global DB
    if DB.closed:
        DB = postgresql.driver.connect(host='106.75.145.80', user='gxj', password='xiaojun.guo1', database='cra1', port=9988)
    return DB


# 把列表分段，每个子列表长度为n
def sub_list(list_bef, n):
    list_aft = []
    length = len(list_bef)
    multiple = int(length/n)
    for sub in range(multiple):
        list_aft.append(list_bef[sub*n:(sub+1)*n])
    return list_aft


# 截取a标签内的内容
def split_date(old_date, a, b):
    new_date = str(old_date).split(a)[1].split(b)[0]
    new_date = new_date.replace('"', '').replace('\'', '')
    return new_date


# 对其他模块的th.td内容进行格式处理
def format_model(h, d):
    new = []
    index_l = [h.index(i) for i in h]
    len_h = len(list(set(index_l)))
    n = len(h)/len(list(set(index_l)))
    if int(n) > 1:
        new.append(h[:len_h])
        for i in range(int(n)):
            new.append(d[len_h * i:len_h * (i+1)])
    else:
        new.append(h)
        new.append(d)
    return new


# 把两个列表映射成字典
def convto_dict(list1, list2):
    todict = dict(map(lambda x, y: [x, y], list1, list2))
    return todict


# 从数据库中获得id
def get_id():
    # upp, low = rangenum()
    # sql_sur = "select id,body from org_raw_guangxi_id where incream>" + str(upp) +"and incream <" + str(low) + "and used = '0';"
    # sql_sur = "select id,body from org_guangxi_id_new where incream>" + str(upp) + "and incream <" + str(low) + "and used = '0';"
    sql_sur = "select id,body from org_guangxi_id15 where flag = '0' ORDER BY random() limit 100;"
    result = DB.query(sql_sur)
    result_id = [i[0] for i in result]
    result1 = [eval(i[1])['href'] for i in result]
    result_reg = [eval(i[1])['regNo'] for i in result]
    result_ent = [eval(i[1])['entid'] for i in result]
    return result1, result_reg, result_ent, result_id


# 保存数据
def save_date(gxid, regno, sql_save):
    try:
        sql_save = json.dumps(sql_save, ensure_ascii=False)
        sql_desc = "insert into org_raw_guangxi15 values ('{}', '{}', '{}', '{}');".format(gxid, regno, time.ctime(), sql_save)
        DB.query(sql_desc)
        logging.warning('*******  数据存储完成时间 {} *********'.format(time.ctime()))
    except Exception:
        logging.warning('   *****  重复数据   ****** ')
        update_pg(gxid)


# 更新used字段
def update_pg(up_id):
    sql_update = "update org_guangxi_id15 set flag = '1' where id = '{}';".format(up_id)
    DB.query(sql_update)
    logging.warning('*******  数据更新完成  *********')


# 解析除基本信息的第一部分其他模块,参数为保持通话的session，模块的部分url
def other_spider(con_s, other_url):
    ourl = 'http://gx.gsxt.gov.cn' + other_url

    credit_ticket = ourl.split('=')[-1]
    entid = ourl.split('=')[1].split('&')[0]

    orel = con_s.get(ourl, timeout=15)
    osoup = BeautifulSoup(orel.text, 'lxml')
    h1 = osoup.select('h1.public-title2')[0].get_text().replace('\r','').replace('\n','').replace('\t','').replace(' ','')
    th = [i.get_text().replace('\r','').replace('\n','').replace('\t','').replace(' ','') for i in osoup.select('th')]
    if '认缴明细' in str(th):
        th = th[:3]+th[5:]
    td = osoup.select('td')
    new_td = []

    # 处理特殊的表头
    if '股东及出资信息股东的出资信息' in str(h1):
        h1 = '股东及出资信息'
    elif '行政' in str(h1):
        h1 = '企业' + h1
    elif '股东及出资信息' in str(h1) and '认缴额（万元）' in str(th):
        h1 = '企业股东及出资信息'
    elif '条信息' in str(h1) and '商标注册信息' not in str(h1):
        h1 = h1.split('条信息')[-1]
    else:
        h1 = h1
    # 对td 标签进行文本处理
    # 分页处理,变更信息

    if h1 == '变更信息':
        b_td = [i.get_text() for i in td]
        bg_url = 'http://gx.gsxt.gov.cn/gjjbj/gjjbj/gjjbj/gjjbj/gjjbj/gjjbj/gjjbj/gjjbj/gjjQueryCreditAction!xj_biangengFrame.dhtml?clear=true&credit_ticket=' + credit_ticket
        if len(osoup.select('#pagescount')) > 0:
            for i in osoup.select('#pagescount'):
                page_n = i['value']

                if int(page_n) > 1:
                    bgxx_td = []
                    for n in range(2, (int(page_n) + 1)):
                        date = {
                            'pageNos': n,
                            'ent_id': entid,
                            'urltag': '5',
                            'pageSize': '5',
                            'pageNo': (n - 1)
                        }
                        bg_rel = con_s.post(bg_url, data=date, timeout=15)
                        bg_soup = BeautifulSoup(bg_rel.text, 'lxml')
                        # bg_td = [i.get_text() for i in bg_soup.select('td')]
                        for bg in bg_soup.select('td'):
                            bgxx_td.append(bg.get_text())

                    new_td = b_td + bgxx_td
        else:
            new_td = b_td
    # 处理商标注册信息
    elif '商标注册信息' in str(h1):
        if osoup.select('.detailsList'):
            shanbiao = osoup.select('.detailsList')[0].select('p')
            h1 = '商标注册信息'
            sb_th = ['商标注册号', '类别', '注册公告日期', '查看详情']
            sb_td = []
            for sb in shanbiao:
                if sb.a:
                    sb_td.append('http://gx.gsxt.gov.cn' + sb.a['href'])
                elif ':' in sb.get_text():
                    sb_td.append(str(sb.get_text()).split(':')[1])
                else:
                    sb_td.append(str(sb.get_text()).split('：')[1])
            th = sb_th
            new_td = sb_td
    # 处理分支机构信息
    elif '分支机构信息' in str(h1) and '暂无' not in str(td):
        for fz in td:
            if ':' in fz.get_text():
                new_td.append(str(fz.get_text()).split('：')[1].replace('\r','').replace('\n','').replace('\t','').replace(' ',''))
            else:
                new_td.append(fz.get_text().replace('\r','').replace('\n','').replace('\t','').replace(' ',''))

    else:
        for i in td:
            if i.a:
                if '年报信息' in str(h1):
                    new_td.append('http://gx.gsxt.gov.cn'+i.a['href'])
                else:
                    new_td.append(str(split_date(i.a['onclick'], '(', ')')))

            else:
                new_td.append(i.get_text().replace('\r','').replace('\n','').replace('\t','').replace(' ',''))
    if '暂无' in str(new_td) and len(new_td) == 1:
        return '', '', ''
    elif len(new_td) < 1:
        return '', '', ''
    else:
        return h1, th, new_td


# 行政许可信息 行政处罚信息 列入经营异常名录信息 列入严重违法失信企业名单（黑名单）信息
def qita_spider(qt_soup):
    # new_list = []
    h = qt_soup.select('h1.public-title2')[0].get_text().replace('\r','').replace('\n','').replace('\t','').replace(' ','')
    th = [i.get_text().replace('\r','').replace('\n','').replace('\t','').replace(' ','') for i in qt_soup.select('th')]
    td_list = qt_soup.select('td')
    td = []
    if h == '行政处罚信息':
        for qt_td in td_list:
            if qt_td.a != None:
                td.append('http://gx.gsxt.gov.cn' + qt_td.a['href'])
            else:
                td.append(qt_td.get_text().replace('\r', '').replace('\n', '').replace('\t', '').replace(' ', ''))
    else:
        td = [i.get_text().replace('\r','').replace('\n','').replace('\t','').replace(' ','') for i in td_list]
    if len(td) >= 1 and '暂无' not in str(td):
        leng = int(len(th))
        new_list = [th] + sub_list(td, leng)
        return h, new_list
    else:
        return [], []


# 请求数据，解析
def gxspider(keyid, key2, key3, key4, key5):
    mess = {}
    s = requests.session()
    s.headers = {
        'Host': 'gx.gsxt.gov.cn',
        # 'Connection': 'keep-alive',
        # 'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.75 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8'
    }
    url = 'http://gx.gsxt.gov.cn' + keyid
    rel = s.get(url, timeout=15)
    soup = BeautifulSoup(rel.text, 'lxml')
    # 基础信息处理
    jcxx_div = soup.select('div.qyqx-detail')
    jcxx_td = jcxx_div[0].select('td')
    jcxx_text = [i.get_text().replace('\r','').replace('\n','').replace('\t','').replace(' ','') for i in jcxx_td if i.get_text() != '']
    jcxx_tag = []
    jcxx_mess = []
    for i in jcxx_text:
        jcxx_tag.append(str(i).split('：')[0])
        jcxx_mess.append(str(i).split('：')[-1])
    jcxx = convto_dict(jcxx_tag, jcxx_mess)
    jcxx['顺序'] = jcxx_tag
    mess['营业执照信息'] = jcxx
    # 获得其他模块的url
    iframe_div = soup.select('.rightFrame')
    iframe_id = [i.get('src') for i in iframe_div]
    for u in iframe_id:
        head, other_th, other_td = other_spider(s, u)
        if head != '':
            if len(other_th) > 1:
                n = int(len(other_th))
            else:
                n = 1
            if '主要人员信息' in str(head) or '成员名册信息' in str(head):
                mess[head] = [['姓名', '职位']] + sub_list(other_td, 2)
            elif '分支机构信息' in str(head):
                mess['分支机构信息'] = [['公司名称', '统一社会信用代码/注册号', '登记机关']] + sub_list(other_td, 3)
            else:

                mess[head] = [other_th] + sub_list(other_td, n)
            # mess.pop('')
    # 行政许可信息 行政处罚信息 列入经营异常名录信息 列入严重违法失信企业名单（黑名单）信息
    url2 = 'http://gx.gsxt.gov.cn'+key2
    url3 = 'http://gx.gsxt.gov.cn'+key3
    url4 = 'http://gx.gsxt.gov.cn'+key4
    url5 = 'http://gx.gsxt.gov.cn'+key5
    rel2 = s.get(url2, timeout=15)
    soup2 = BeautifulSoup(rel2.text, 'lxml')
    soup2_h, soup2_tab = qita_spider(soup2)
    if soup2_h != []:
        mess[soup2_h] = soup2_tab

    rel3 = s.get(url3, timeout=15)
    soup3 = BeautifulSoup(rel3.text, 'lxml')
    soup3_h, soup3_tab = qita_spider(soup3)
    if soup3_h != []:
        mess[soup3_h] = soup3_tab

    rel4 = s.get(url4, timeout=15)
    soup4 = BeautifulSoup(rel4.text, 'lxml')
    soup4_h, soup4_tab = qita_spider(soup4)
    if soup4_h != []:
        mess[soup4_h] = soup4_tab

    rel5 = s.get(url5, timeout=15)
    soup5 = BeautifulSoup(rel5.text, 'lxml')
    soup5_h, soup5_tab = qita_spider(soup5)
    if soup5_h != []:
        mess[soup5_h] = soup5_tab
    print(json.dumps(mess, ensure_ascii=False))
    return mess


def main():
    sql_id, sql_reg, sql_ent, sq_id = get_id()
    for i in sql_id:
        entid = i.split('=')[1].split('&')[0]
        credit_t = i.split('=')[-1]
        keyid = '/gjjbj/gjjQueryCreditAction!openEntInfo.dhtml?entId='+entid+'&clear=true&urltag=1&credit_ticket='+credit_t
        keyid2 = '/xzxk/xzxkAction!xj_qyxzxkFrame.dhtml?entId='+entid+'&clear=true&urltag=7'
        keyid3 = '/gdgq/gdgqAction!xj_qyxzcfFrame.dhtml?entId='+entid+'&regno='+sql_reg[sql_id.index(i)]+'&uniscid='+sql_ent[sql_id.index(i)]+'&clear=true&urltag=14'
        keyid4 = '/gsgs/gsxzcfAction!list_jyycxx.dhtml?entId='+entid+'&clear=true&urltag=8'
        keyid5 = '/gsgs/gsxzcfAction!list_yzwfxx.dhtml?ent_id='+entid+'&clear=true&urltag=9'

        try:
            save_body = gxspider(keyid, keyid2, keyid3, keyid4, keyid5)
            save_date(sq_id[sql_id.index(i)], sql_reg[sql_id.index(i)], save_body)
            update_pg(sq_id[sql_id.index(i)])
        except TypeError:
            continue
        except ConnectionError:
            continue


if __name__ == '__main__':
    while True:
        try:
            main()
        except Exception as e:
            logging.warning('             main函数except    = {}'.format(e))
            DB.close()
            # 重新连接数据库
            conn_sql()
            time.sleep(5)
            continue
    DB.closed()



